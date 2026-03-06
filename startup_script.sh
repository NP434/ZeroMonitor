#!/bin/bash

#DIR Locations
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SECRETS_DIR="$REPO_DIR/../zero_monitor_secrets"
RAM_DIR="/run/zero_monitor_decrypted"
PASS_FILE="$RAM_DIR/zero_pass.txt"

#Check for GitHub Updates
echo "--- Checking for updates from GitHub ---"
"$REPO_DIR/update_project.sh"

#Collect Master Passkey
PASSCODE=$(cat "$PASS_FILE")

#Decryption Phase
cp "$SECRETS_DIR/id_ed25519.enc" "$RAM_DIR/my_key"
ssh-keygen -p -P "$PASSCODE" -N "$PASSCODE" -f "$RAM_DIR/my_key"
chmod 600 "$RAM_DIR/my_key"

openssl enc -d -aes-256-cbc -pbkdf2 -salt 
	-in "$SECRETS_DIR/encrypted_device_list.enc" 
	-out "$RAM_DIR/device_list.json" 
	-pass pass:"$PASSCODE"
chmod 600 "$RAM_DIR/device_list.json"

#Remove Password from RAM
unset PASSCODE
echo "--- Secrets Decrypted ---"
python3 "$REPO_DIR/main.py"
