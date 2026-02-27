#!/bin/bash

#DIR Locations
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SECRETS_DIR="$REPO_DIR/../zero_monitor_secrets"
RAM_DIR="/run/zero_monitor_decrypted"

#Make RAM Vault
if [ ! -d "$RAM_DIR" ]; then
	sudo mkdir -p "$RAM_DIR"
	sudo chown admin:admin "$RAM_DIR"
fi

#Check for GitHub Updates
echo "--- Checking for updates from GitHub ---"
"$REPO_DIR/update_project.sh"

#Get User Password
echo "--- Authentication Module ---"
read -s -p "Enter Master Passcode: " PASS
echo ""

#Decryption Phase
cp "$SECRETS_DIR/id_ed25519.enc" "$RAM_DIR/my_key"
ssh-keygen -p -P "$PASS" -N "$PASS" -f "$RAM_DIR/my_key"
chmod 600 "$RAM_DIR/my_key"

openssl enc -d -aes-256-cbc -pbkdf2 -salt -in "$SECRETS_DIR/encrypted_device_list.enc" -out "$RAM_DIR/device_list.json" -pass pass:"$PASS"
chmod 600 "$RAM_DIR/device_list.json"

#Remove Password from RAM
unset PASS
echo "--- Secrets Decrypted ---"
python3 "$REPO_DIR/main.py"
