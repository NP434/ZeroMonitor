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
    main_script = os.path.join(base_dir, "../main.py")
    
    # Check for venv 
    venv_options = ['venv', '.venv']
    python_exec = sys.executable # Default fallback

    for venv_name in venv_options:
        venv_python = os.path.join(base_dir, venv_name, "bin", "python")
        if os.path.exists(venv_python):
            python_exec = venv_python
            print(f"[INFO] Virtual Environment detected at: {venv_python}")
            break
    
    if python_exec == sys.executable and not os.path.exists(os.path.join(base_dir, 'venv')):
        print("[WARNING] No virtual environment found. Using system Python.")

    # Get the actual user who ran 'sudo'
    user = os.environ.get('SUDO_USER', 'root')

    print(f"Detected Project Directory: {base_dir}")
    print(f"Target User: {user}")

    # Define the systemd service template
    service_content = textwrap.dedent(f"""\
        [Unit]
        Description=Zero Monitor Appliance
        After=graphical.target network-online.target
        Wants=network-online.target

        [Service]
        Type=simple
        User={user}
        WorkingDirectory={base_dir}
        # Explicitly calling the venv python handles all dependencies like Fabric
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

    # Enable and start the service
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

    print("\nStartup Service Installed Successfully")
    print("To test now, run: sudo systemctl start zero_monitor.service")
    print("To view live logs, run: journalctl -u zero_monitor.service -f")

if __name__ == "__main__":
    create_startup_service()