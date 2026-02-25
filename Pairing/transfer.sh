#!/usr/bin/env bash
set -e

### Master Script for initialization ###
### Ver 1.0 ###

### Setting File locations ###
echo "Setting File Paths"
SSH_KEY="$HOME/.ssh/id_rsa.pub"
SERVER_APP="Pairing/endpoint.py"
SERVER_URL="https://127.0.0.1:8443"
DEVICE_LIST="device_list.json"

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
        End_reason="closed"
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "[!] Timeout reached, shutting down Flask endpoint..."
    kill $FLASK_PID
    End_reason="timeout"
fi

if ["$End_reason" = "closed"] then
    echo "Enter UserName on target device"
    read UN
    echo "Enter HostName of target device"
    read HN

    OS_INFO=$(ssh -i $HOME/.ssh/id_rsa "$UN@$HN" 'cat /etc/os-release' )
    echo "$OS_INFO"

