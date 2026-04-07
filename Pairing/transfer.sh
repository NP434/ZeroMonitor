#!/usr/bin/env bash
set -ex

### Master Script for initialization ###
### Ver 1.0 ###

### Setting File locations ###
echo "Setting File Paths"
SERVER_APP="Pairing/endpoint.py"
SERVER_URL="https://127.0.0.1:8443"

### setting varaibles ###
UN="$1"
HN="$2"
SSH_KEY="$3"
DEVICE_LIST="$4"
PAIRING="$5"
SERV_CERT="$6"
SERV_KEY="$7"

if [ ! -f "$SSH_KEY" ]; then
  echo "[*] SSH key does not exits."
  exit
else
  echo "[*] SSH key already exists"
fi

### HTTPS Start up ###
echo "Endpoint start up"
python -u "$SERVER_APP" "$SSH_KEY" "$PAIRING" "$SERV_CERT" "$SERV_KEY" &
FLASK_PID=$!

### Wait for flask to start
sleep 5

### Upload Key ###
echo "Uploading data"
curl -k -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @"$SSH_KEY" \
"$SERVER_URL/transfer"

STATUS=$(curl -sk "$SERVER_URL/stat" | python3 -c "import sys,json; print(json.load(sys.stdin)['stat'])")

if [ "$STATUS" = "False" ]; then
  if OS_INFO=$(ssh -i "$HOME/.ssh/id_rsa" "$UN@$HN" 'cat /etc/os-release' 2>/dev/null); then
    echo "$OS_INFO"
  elif OS_INFO=$(ssh -i "$HOME/.ssh/id_rsa" "$UN@$HN" 'ver' 2>/dev/null); then
    echo "$OS_INFO"
  else
    echo "OS_Unknown"
  fi
else
    echo "OS_Unknown"
fi

kill $FLASK_PID




