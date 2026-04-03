# Control file for pairing module, handles add device events and communications
# with the event bus

import logging
from event_bus import EventBus
import subprocess
import json
from pathlib import Path
from secrets import token_hex

script = "./Pairing/transfer.sh"
BASE_DIR = Path(__file__).resolve().parent
PK_FILE = BASE_DIR / "Pdata.json"
p_script = "./Pairing/pb_transfer.sh"
        
class ControlPairing:
    """Framework for the pairng class that drives the pairing module"""
    def __init__(self, bus:EventBus):
        self.bus = bus
        #self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)
    
    def add_node(self, node_config:dict):
        """Handle the add node event but activating transfer and returning device info"""
        un = node_config["user"]
        hn = node_config["hostname"]
        pw = node_config["Pword"]
        if node_config["pairing_mode"] == "Endpoint":
            # Create and store key in location
            pairing_token = token_hex(4)
            pdat = {"pairing_token": pairing_token,
                f"Command": 'Curl -k -H "P-Key:{pairing_token}" "192.168.0.106:8443/transfer" -o retrieved_key.pub'}
            with open(PK_FILE, "w") as f:
                json.dump(pdat,f)
            self.bus.publish("Display_token",pairing_token)
            os_info = subprocess.run(
                [script, un, hn],
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

        

        

