#!/usr/bin/env bash


### Set user name, host name from exterior file
UN="$1"
HN="$2"
PW="$3"

echo "attempting ssh key transfer"
sshpass -p "$PW" ssh-copy-id $UN@$HN

echo "transfer success, attempting first connection and target OS ident"
if OS_INFO=$(ssh -i "$HOME/.ssh/id_rsa" "$UN@$HN" 'cat /etc/os-release' 2>/dev/null); then
    echo "$OS_INFO"
elif OS_INFO=$(ssh -i "$HOME/.ssh/id_rsa" "$UN@$HN" 'ver' 2>/dev/null); then
    echo "$OS_INFO"
else
    echo "OS_Unknown"
fi


