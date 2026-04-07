# Control file for pairing module, handles add device events and communications
# with the event bus

import logging
from event_bus import EventBus
import subprocess
import json
from pathlib import Path
from secrets import token_hex
import requests
import time
import os
import socket

script = "./Pairing/transfer.sh"
p_script = "./Pairing/pb_transfer.sh"


class ControlPairing:
    """Framework for the pairng class that drives the pairing module"""
    def __init__(self, bus:EventBus, config):
        self.bus = bus
        self.config = config
        #self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)

    def get_ip(self):
        """retreives the IP address of host and adds it to curl command"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8",80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    

    def add_node(self, node_config:dict):
        """Handle the add node event but activating transfer and returning device info"""
        #Following section used to set needed target details
        un = node_config["user"]
        hn = node_config["hostname"]
        pw = node_config["Pword"]

        #Following sets path files for neccessary components
        key_path = self.config.ssh_pub_key
        list_path = self.config.decrypted_list
        pairing_path = self.config.pairing_info
        serv_cert_path = self.config.server_cert
        serv_key_path = self.config.server_key

        if node_config["pairing_mode"] == "Endpoint":
            # This section handles the logic of the endpoint creation and
            # transfer of ssh key via the endpoint

            # Create a pairing token and store it for display to the UI
            pairing_token = token_hex(4)
            # Retrieve the hosts IP
            ip = self.get_ip()
            pdat = {"pairing_token": pairing_token,
                f"Command": 'Curl -k -H "P-Key:{pairing_token}" "https://{ip}:8443/transfer" -o authorized_keys.pub'}
            with open(self.config.pairing_info, "w") as f:
                json.dump(pdat,f)
            self.bus.publish("Display_token",pdat["Command"])

            # Start the endpoint using eh endpoint.py file
            if not Path(key_path).is_file():
                raise FileNotFoundError("SSH key does not exist.")
            else:
                print("[*] SSH key already exists")

            # Start endpoint server
            print("Endpoint start up")
            flask_proc = subprocess.Popen(
                ["python", "-u", "Pairing/endpoint.py", key_path, pairing_path, serv_cert_path, serv_key_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )

            # Wait for server to start
            time.sleep(5)
            
            try:
                #Handling key upload
                print("Uploading data")
                with open(key_path, "rb") as f:
                    requests.post("https://127.0.0.1:8443/transfer",
                    data=f,
                    headers={"Content-Type": "text/plain"},
                    verify=False
                    )
                # Get status
                response = requests.get("https://127.0.0.1:8443/stat", verify=False)
                status = response.json().get("stat")

                if status == "retrieved":
                    try:
                        # Try Linux/macOS
                        os_info = subprocess.check_output(
                            [ "ssh", "-i", os.path.expanduser("~/.ssh/id_rsa"), f"{un}@{hn}", "cat /etc/os-release"],
                            stderr=subprocess.DEVNULL,
                            text=True
                            )
                        os_info = "Linux"
                    except subprocess.CalledProcessError:
                        try:
                            # Try Windows
                            os_info = subprocess.check_output(
                            ["ssh", "-i", os.path.expanduser("~/.ssh/id_rsa"), f"{un}@{hn}", "ver"],
                            stderr=subprocess.DEVNULL,
                            text=True
                            )
                            os_info = "Windows"

                        except subprocess.CalledProcessError:
                            os_info = "OS_Unknown"
                else:
                    os_info = "OS_Unknown"

            finally:
                # Kill Flask process
                flask_proc.terminate()
                flask_proc.wait()


            node_config["operating_system"] = os_info.stdout.strip()
            del node_config["pairing_mode"]
            with open("device_list.json", "w") as f:
                json.dump(f,node_config, indent=4)


        elif node_config["pairing_mode"] == "Pass_auth":
            #Handles the password bassed ssh login if selected by the user
            os_info = subprocess.run([p_script, un,hn, pw ],
                                     check = True,
                                     text=True,
                                     capture_output=True)
            node_config["operating_system"] = os_info.stdout.strip()
            del node_config["pairing_mode"]
            with open("device_list.json", "w") as f:
                json.dump(f,node_config, indent=4)
        self.bus.publish("SYNC_VAULT", {})

        

        

