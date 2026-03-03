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
    
    def add_node(self, node_config:dict):
        """Handle the add node event but activating transfer and returning device info"""
        hostname = node_config.get("hostname")
        user = node_config.get("user")
        subprocess.run([script],check=True)
        

        

