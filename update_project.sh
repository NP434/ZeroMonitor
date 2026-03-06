#!/bin/bash

#Working Directory
cd "$(dirname "$0")"

#Look at latest data
git fetch origin secret_management

#Check if update needed
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/secret_management)

if [ "$LOCAL" != "$REMOTE" ]; then
	echo "Update Avaliable, Pulling new code..."
	git pull origin secret_management
	exit 0 # Update Complete
else
	echo "No changes on GitHub. Running latest version."
	exit 1 # Running Latest Version
fi

# AUTO UPDATE
# crontab -e
# 0 1 * * * /home/admin/zero_monitor_dir/Zero_Monitor_Test/update_project.sh >> /home/admin/zero_monitor_dir/update_log.txt 2>&1