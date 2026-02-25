# Control file for pairing module, handles add device events and communications
# with the event bus

import logging
from event_bus import EventBus
import subprocess

script = "./Pairing/transfer.sh"

class ControlPairing:
    """Framework for the pairng class that drives the pairing module"""
    def __init__(self, bus:EventBus):
        self.bus = bus
        self.logger = logging.getlogger("pairing")
        self.bus.subscribe("ADD_NODE", self.add_node)
    
    def add_node(self):
        """Handle the add node event but activating transfer and returning device info"""
        subprocess.run([script],check=True)
        

