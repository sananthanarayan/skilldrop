"""billing-api HTTP entry point."""
from flask import Flask, jsonify, request

from auth import require_internal_caller
from config.settings import load_settings

app = Flask(__name__)
settings = load_settings()


@app.post("/internal/charges")
@require_internal_caller
def create_charge():
    body = request.get_json()
    # ... create the charge against the processor using settings["processor_api_key"]
    return jsonify({"status": "queued", "invoice_id": body["invoice_id"]}), 202
