#!/usr/bin/env bash
set -e

### Master Script for initialization ###
### Ver 1.0 ###

### Setting File locations ###
echo "Setting File Paths"
SSH_KEY="$HOME/.ssh/id_rsa.pub"
SERVER_APP="Initialization/endpoint.py"
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

### Retreive and store key locally ###
echo "Retreived data \n"
read -p "Enter Pairing Key: " KEY
curl -k -H "Pairing-Key: $KEY" "$SERVER_URL/transfer" -o retrieved_key.pub

### Retains endpoint unitl user wants it closed ###
echo " use Ctrl + C to end session"
wait

### end flask ###
kill $FLASK_PID