# Control file for pairing module, handles add device events and communications
# with the event bus

import logging
from event_bus import EventBus
import subprocess
import json

script = "./Pairing/transfer.sh"

class ControlPairing:
    """Framework for the pairng class that drives the pairing module"""
    def __init__(self, bus:EventBus):
        self.bus = bus
        self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)
    
    def add_node(self, d_name:str):
        """Handle the add node event but activating transfer and returning device info"""
        with open("device_list.json", "r") as f:
            data = json.load(f)
            hn = data[d_name]["hostname"]
            un = data[d_name]["user"]
        os_info = subprocess.run([script,un,hn],check=True,
                                 capture_output=True,text=True)
        data[d_name]["operating_system"] = os_info.stdout.strip()
        with open("device_list.json", "w") as f:
            json.dump(data, f, indent=4)

        

        

