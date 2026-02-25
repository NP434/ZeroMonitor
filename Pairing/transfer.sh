#!/usr/bin/env bash
set -e

### Master Script for initialization ###
### Ver 1.0 ###

### Setting File locations ###
echo "Setting File Paths"
SSH_KEY="$HOME/.ssh/id_rsa.pub"
SERVER_APP="Pairing/endpoint.py"
SERVER_URL="https://127.0.0.1:8443"

if [ ! -f "$SSH_KEY" ]; then
  echo "[*] SSH key does not exits."
  exit
else
  echo "[*] SSH key already exists"
fi

### HTTPS Start up ###
echo "Endpoint start up"
python -u "$SERVER_APP" &
FLASK_PID=$!

### Wait for flask to start
sleep 2

### Upload Key ###
echo "Uploading data"
curl -k -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @"$SSH_KEY" \
"$SERVER_URL/transfer"

# Chcek if key has been retrieved and timer for endpoint expiration
TIMEOUT=120  # seconds
ELAPSED=0

while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    STATUS=$(curl -sk "$SERVER_URL/stat" | jq -r '.active')
    if [ "$STATUS" = "false" ]; then
        echo "[*] Pairing key retrieved, shutting down Flask endpoint..."
        kill $FLASK_PID
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "[!] Timeout reached, shutting down Flask endpoint..."
    kill $FLASK_PID
fi
