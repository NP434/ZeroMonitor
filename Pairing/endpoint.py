"""
Description: Version 1.0 for flask endpoint, handles upload and download for
key transfer for the system
"""
from flask import Flask, request,abort,send_file
from pathlib import Path
from secrets import token_hex
import json
import threading
import sys

BASE_DIR = Path(__file__).resolve().parent


KEY_FILE = Path(sys.argv[1] if len(sys.argv) > 1 else None)
PK_FILE = Path(sys.argv[2] if len(sys.argv) > 2 else None)
SERV_CERT = Path(sys.argv[3] if len(sys.argv) > 3 else None)
SERV_KEY = Path(sys.argv[4] if len(sys.argv) > 4 else None)


def get_pairing_token():
    if not PK_FILE.exists():
        return None
    with open(PK_FILE, "r") as f:
        return json.load(f).get("pairing_token")

app = Flask(__name__)
close = threading.Event()

endpoint_active = True

@app.route("/transfer", methods=["GET","POST"])
def example():
  

    if not endpoint_active:
        abort(410, "Endpoint closed")
    
    if request.method == "POST":
        # Handles posting data
        key_data = request.data.decode("utf-8")

        if not key_data.startswith("ssh-"):
            #Ensure key matches format
            abort(400, "Invalid SSH Key")
        KEY_FILE.write_text(key_data)
        return "Storage success", 201

    elif request.method == "GET":
        pairing_token = get_pairing_token()

        if not pairing_token or provided_key != pairing_token:
            abort(403, "Unauthorized")
        provided_key = request.headers.get("P-Key")
        print("\n Pairing Key ")
        print(f"{pairing_token}")
        print("-----------------")

        if provided_key != pairing_token:
            abort(403, "Unauthorized")
        # Handles retreiveing data
        if not KEY_FILE.exists():
            abort(404, "No data stored")   
        
        close.set()
        PK_FILE.unlink(missing_ok=True)

        return send_file(KEY_FILE, mimetype="text/plain")
    
    return "SSH key received", 200

@app.route("/stat", methods=["GET"])
def stat():
    closed = close.wait(timeout = 120)
    if closed:
        return {"stat": "retrieved"}, 200
    else:
        return {"stat": "timeout"}, 200

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8443,
        ssl_context=(str(SERV_CERT),
                      str(SERV_KEY))
    )