# Control file for pairing module, handles add device events and communications
# with the event bus

import logging
from event_bus import EventBus
import subprocess
import json
from pathlib import Path
from secrets import token_hex


script = "./Pairing/transfer.sh"
p_script = "./Pairing/pb_transfer.sh"
        
class ControlPairing:
    """Framework for the pairng class that drives the pairing module"""
    def __init__(self, bus:EventBus, config):
        self.bus = bus
        self.config = config
        #self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)
    
    def add_node(self, node_config:dict):
        """Handle the add node event but activating transfer and returning device info"""
        un = node_config["user"]
        hn = node_config["hostname"]
        pw = node_config["Pword"]
        key_path = self.config.ssh_pub_key
        list_path = self.config.decrypted_list
        pairing_path = self.config.pairing_info
        serv_cert_path = self.config.server_cert
        serv_key_path = self.config.server_key
        if node_config["pairing_mode"] == "Endpoint":
            # Create and store key in location
            pairing_token = token_hex(4)
            pdat = {"pairing_token": pairing_token,
                f"Command": 'Curl -k -H "P-Key:{pairing_token}" "192.168.0.106:8443/transfer" -o retrieved_key.pub'}
            with open(self.config.pairing_info, "w") as f:
                json.dump(pdat,f)
            self.bus.publish("Display_token",pairing_token)

            os_info = subprocess.run(
                [script, un, hn, key_path, list_path, pairing_path,
                 serv_cert_path,serv_key_path],
                check=True,
                text=True,
                capture_output=True
            )
            node_config["operating_system"] = os_info.stdout.strip()
            del node_config["pairing_mode"]
            with open("device_list.json", "w") as f:
                json.dump(f,node_config, indent=4)
        elif node_config["pairing_mode"] == "Pass_auth":
            os_info = subprocess.run([p_script, un,hn, pw ],
                                     check = True,
                                     text=True,
                                     capture_output=True)
            node_config["operating_system"] = os_info.stdout.strip()
            del node_config["pairing_mode"]
            with open("device_list.json", "w") as f:
                json.dump(f,node_config, indent=4)
        self.bus.publish("SYNC_VAULT", {})

        

        

