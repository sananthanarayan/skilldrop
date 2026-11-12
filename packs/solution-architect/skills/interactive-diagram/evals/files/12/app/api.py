from flask import Flask, jsonify, request

from app import catalog, holds

app = Flask(__name__)


@app.get("/search")
def search():
    q = request.args.get("q", "")
    return jsonify(catalog.search(q))


@app.post("/holds")
def place_hold():
    body = request.get_json()
    result = holds.place_hold(body["patron_id"], body["title_id"])
    return jsonify(result), 201


@app.post("/checkins")
def check_in():
    body = request.get_json()
    holds.on_checkin(body["copy_id"])
    return "", 204
