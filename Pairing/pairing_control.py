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
        #self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)
    
    def add_node(self, node_config:dict):
        """Handle the add node event but activating transfer and returning device info"""
        un = node_config["user"]
        hn = node_config["hostname"]
        os_info = subprocess.run([script,un,hn],check=True,
                                 capture_output=True,text=True)
        node_config["operating_system"] = os_info.stdout.strip()
       #with open("device_list.json", "w") as f:
            #son.dump(data, f, indent=4)

        

        

