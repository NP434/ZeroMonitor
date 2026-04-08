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
import threading
from fabric import Connection

def upload_key_async(key_path):
    with open(key_path, "rb") as f:
        requests.post(
            "https://127.0.0.1:8443/transfer",
            data=f,
            headers={"Content-Type": "text/plain"},
            verify=False
        )


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
    
    def detect_os(self,host,user,key_path=None,password=None):
        try:
            if key_path:
                print("Attempting key based connection")
                con = Connection(host=host, user=user, connect_kwargs={"key_filename": key_path})
            else:
                print("Attempting pass based connection")
                con = Connection(host=host, user=user, connect_kwargs={"password": password})

            # Try Linux/macOS
            print("performing Linux check")
            result = con.run("uname", hide=True, warn=True)
            if result.ok:
                print("Linux Detected")
                return "Linux"

            # Try Windows
            result = con.run("ver", hide=True, warn=True)
            if result.ok:
                print("Windows Detected")
                return "Windows"

            return "OS_Unknown"

        except Exception as e:
            print(f"[!] OS detection failed: {e}")
            return "OS_Unknown"

        finally:
            print("OS detection finished")
            try:
                con.close()
            except:
                pass

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
        serv_cert_path = str(Path(self.config.server_cert).resolve())
        serv_key_path = str(Path(self.config.server_key).resolve())

        if node_config["pairing_mode"] == "Endpoint":
            # This section handles the logic of the endpoint creation and
            # transfer of ssh key via the endpoint

            # Create a pairing token and store it for display to the UI
            pairing_token = token_hex(4)
            # Retrieve the hosts IP
            ip = self.get_ip()
            pdat = {"pairing_token": pairing_token,
                f"Command": 'Curl -k -H f"P-Key:{pairing_token}" f"https://{ip}:8443/transfer" -o authorized_keys.pub'}
            print(pairing_token)
            with open(self.config.pairing_info, "w") as f:
                json.dump(pdat,f)
            print("Publishing display token event")
            self.bus.publish("Display_token",pdat["Command"])

            # Start the endpoint using eh endpoint.py file
            if not Path(key_path).is_file():
                raise FileNotFoundError("SSH key does not exist.")
            else:
                print("[*] SSH key already exists")

            # Start endpoint server
            print("Endpoint start up")
            flask_proc = subprocess.Popen(
                ["python", "-u", "Pairing/endpoint.py", key_path, pairing_path, serv_cert_path, serv_key_path]
            )

            # Wait for server to start
            time.sleep(5)
            
            try:
                #Handling key upload
                print("Uploading data")
                threading.Thread(target=upload_key_async,args=(key_path,), daemon=True).start()
                # Get status
                response = requests.get("https://127.0.0.1:8443/stat", verify=False)
                status = response.json().get("stat")

                if status == "retrieved":
                    os_info = self.detect_os_ssh(
                                hn,un,
                    key_path=os.path.expanduser("~/.ssh/id_rsa")
                    )
                else:
                    os_info = "OS_Unknown"

            finally:
                # Kill Flask process
                flask_proc.terminate()
                flask_proc.wait()


            node_config["operating_system"] = os_info
            with open("device_list.json", "w") as f:
                json.dump(node_config,f, indent=4)


        elif node_config["pairing_mode"] == "Pass_auth":
            #Handles the password bassed ssh login if selected by the user
            print("Using password based authentication")
            os_info = self.detect_os(hn,un,password=pw)          
            node_config["operating_system"] = os_info
            with open("device_list.json", "w") as f:
                json.dump(node_config,f, indent=4)
                print("Saving node data to node config")
        print("Publishing vault event")
        self.bus.publish("SYNC_VAULT", {})
