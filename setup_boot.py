import os
import sys
import subprocess
import textwrap

def create_startup_service():
    print("Configuring Startup Service")

    # Ensure Sudo
    if os.geteuid() != 0:
        print("[ERROR] This script must be run with sudo.")
        print("Please run: sudo python setup_boot.py")
        sys.exit(1)

    # Get absolute paths dynamically
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")
    
    # Use the exact python executable
    python_exec = sys.executable 
    
    # Get the actual user who ran 'sudo'
    user = os.environ.get('SUDO_USER', 'root')

    print(f"Detected Project Directory: {base_dir}")
    print(f"Detected Python Environment: {python_exec}")
    print(f"Target User: {user}")

    # Define the systemd service template
    # We use graphical.target to ensure the desktop environment is loaded before Pygame starts
    # textwrap so indents don't look bad
    service_content = textwrap.dedent(f"""\
        [Unit]
        Description=Zero Monitor Appliance
        After=graphical.target network-online.target
        Wants=network-online.target

        [Service]
        Type=simple
        User={user}
        WorkingDirectory={base_dir}
        ExecStart={python_exec} {main_script}
        Environment=DISPLAY=:0
        Environment=WAYLAND_DISPLAY=wayland-1
        Environment=XDG_RUNTIME_DIR=/run/user/1000
        Restart=always
        RestartSec=5

        [Install]
        WantedBy=graphical.target
    """)

    service_path = "/etc/systemd/system/zero_monitor.service"

    # Write the file
    print("\nWriting systemd service file...")
    try:
        with open(service_path, "w") as f:
            f.write(service_content)
        print(f"[SUCCESS] Saved to {service_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write service file: {e}")
        sys.exit(1)

    # Enable and start the service via command line
    print("\nEnabling service in systemctl...")
    commands = [
        ["systemctl", "daemon-reload"],
        ["systemctl", "enable", "zero_monitor.service"]
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] Executed: {' '.join(cmd)}")
        else:
            print(f"[ERROR] Failed: {' '.join(cmd)}\n{result.stderr}")

    print("Startup Service Installed")
    print("To view live logs, run: journalctl -u zero_monitor.service -f")

if __name__ == "__main__":
    create_startup_service()