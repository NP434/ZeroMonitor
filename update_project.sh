#!/bin/bash

#Working Directory
cd "$(dirname "$0")"

#Look at latest data
git fetch origin main

#Check if update needed
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" != "$REMOTE" ]; then
	echo "Update Avaliable, Pulling new code..."
	git pull origin main
	exit 0 # Update Complete
else
	echo "No changes on GitHub. Running latest version."
	exit 1 # Running Latest Version
fi

# AUTO UPDATE
# crontab -e
# 0 1 * * * /home/admin/zero_monitor_dir/Zero_Monitor_Test/update_project.sh >> /home/admin/zero_monitor_dir/update_log.txt 2>&1