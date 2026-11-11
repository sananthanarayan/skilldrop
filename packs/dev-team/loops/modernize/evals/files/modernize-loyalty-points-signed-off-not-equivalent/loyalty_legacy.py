# loyalty_legacy.py -- points for each basket, used by the nightly points run
import datetime

def points(spend_pence, date_str):
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    pts = spend_pence // 500          # 1 point per whole 5 pounds
    if d.weekday() == 1:              # Tuesday: double points
        pts = pts * 2
    if pts > 500:                     # cap per basket
        pts = 500
    return pts
