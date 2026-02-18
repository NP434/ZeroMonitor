"""
Description: Version 1.0 for flask endpoint, handles upload and download for
key transfer for the system
"""
from flask import Flask, request,abort,send_file
from pathlib import Path
from secrets import token_hex

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / "certs"
KEY_FILE = BASE_DIR / "uploaded_key.pub"
pairing_key = token_hex(4)

app = Flask(__name__)

@app.route("/transfer", methods=["GET","POST"])
def example():
    if request.method == "POST":
        # Handles posting data
        key_data = request.data.decode("utf-8")

        if not key_data.startswith("ssh-"):
            #Ensure key matches format
            abort(400, "Invalid SSH Key")
        KEY_FILE.write_text(key_data)
        return "Storage success", 201

    elif request.method == "GET":
        provided_key = request.headers.get("Pairing-Key")

        print("Expected:", pairing_key)
        print("Received:", provided_key)
    
        if provided_key != pairing_key:
            abort(403, "Unauthorized")
        # Handles retreiveing data
        if not KEY_FILE.exists():
            abort(404, "No data stored")   
        return send_file(KEY_FILE, mimetype="text/plain")
    
    return "SSH key received", 200

if __name__ == "__main__":
    print("\n Pairing Key ")
    print(f"{pairing_key}")
    print("-----------------")

    app.run(
        host="127.0.0.1",
        port=8443,
        ssl_context=(CERT_DIR / "server.crt",
                     CERT_DIR / "server.key")
    )