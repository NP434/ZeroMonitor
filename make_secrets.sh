#!/bin/bash

#DIR Locations
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SECRETS_DIR="$REPO_DIR/../zero_monitor_secrets"
RAM_DIR="/run/zero_monitor_decrypted"
PASS_FILE="$RAM_DIR/zero_pass.txt"

echo "--- Zero Monitor: Security Initialization ---"

#Create Secrets Vault
if [ ! -d "$SECRETS_DIR" ]; then
    mkdir -p "$SECRETS_DIR"
    echo "Created directory: $SECRETS_DIR"
fi

#Collect Master Passkey
PASSCODE=$(cat "$PASS_FILE")

#Generate the SSH Key (Ed25519)
echo "Generating SSH key pair..."
yes | ssh-keygen -t ed25519 -C "admin@zeromonitor" -f "$SECRETS_DIR/id_ed25519" -N "$PASSCODE" -q
mv -f "$SECRETS_DIR/id_ed25519" "$SECRETS_DIR/id_ed25519.enc"
echo "Encrypted SSH keys generated"

#Create the Device List JSON
echo "Creating inital device list..."
echo '{"node1": {"hostname": "127.0.0.1", "user": "admin", "name": "LocalTest"}}' > "$SECRETS_DIR/device_list.json"

#Encrypt the Device List
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$SECRETS_DIR/device_list.json" -out "$SECRETS_DIR/encrypted_device_list.enc" -pass pass:"$PASSCODE"
rm "$SECRETS_DIR/device_list.json"
echo "Encrypted device list created"

#Remove Passcodes
unset PASSCODE
echo "--- Secrets Created ---"
"$REPO_DIR/startup_script.sh"