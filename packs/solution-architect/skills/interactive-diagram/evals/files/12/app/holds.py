import yaml

from app import db, notify

_cfg = yaml.safe_load(open("config.yaml"))
MAX_ACTIVE = _cfg["holds"]["max_active_per_patron"]


class HoldRefused(Exception):
    pass


def place_hold(patron_id, title_id):
    patron = db.one("SELECT id, card_expires FROM patrons WHERE id = %s", (patron_id,))
    if patron is None or patron["card_expires"] < db.today():
        raise HoldRefused("card missing or expired")

    active = db.one(
        "SELECT count(*) AS n FROM holds WHERE patron_id = %s AND status IN ('waiting', 'ready')",
        (patron_id,),
    )
    if active["n"] >= MAX_ACTIVE:
        raise HoldRefused("too many active holds")

    hold_id = db.insert(
        "INSERT INTO holds (patron_id, title_id, status, placed_at) VALUES (%s, %s, 'waiting', now()) RETURNING id",
        (patron_id, title_id),
    )

    copy = db.one(
        "SELECT id FROM copies WHERE title_id = %s AND status = 'on_shelf' LIMIT 1",
        (title_id,),
    )
    if copy:
        _make_ready(hold_id, copy["id"])
        return {"hold_id": hold_id, "status": "ready"}

    position = db.one(
        "SELECT count(*) AS n FROM holds WHERE title_id = %s AND status = 'waiting' AND id <= %s",
        (title_id, hold_id),
    )
    return {"hold_id": hold_id, "status": "waiting", "position": position["n"]}


def on_checkin(copy_id):
    copy = db.one("SELECT id, title_id FROM copies WHERE id = %s", (copy_id,))
    db.execute("UPDATE loans SET returned_at = now() WHERE copy_id = %s AND returned_at IS NULL", (copy_id,))

    nxt = db.one(
        "SELECT id FROM holds WHERE title_id = %s AND status = 'waiting' ORDER BY placed_at LIMIT 1",
        (copy["title_id"],),
    )
    if nxt is None:
        db.execute("UPDATE copies SET status = 'on_shelf' WHERE id = %s", (copy_id,))
        return
    _make_ready(nxt["id"], copy_id)


def _make_ready(hold_id, copy_id):
    db.execute("UPDATE copies SET status = 'held' WHERE id = %s", (copy_id,))
    db.execute("UPDATE holds SET status = 'ready', copy_id = %s WHERE id = %s", (copy_id, hold_id))
    notify.send_ready(hold_id)
