from fabric import ThreadingGroup
import re
from typing import Optional, Dict

class remote_target:
    def __init__(self, hostname: str) -> None:
        # Hostname = IP address or DNS name
        self.hostname = hostname

    def _create_group(self) -> ThreadingGroup:
        """Establishes a group of connections with target devices"""
        group = ThreadingGroup(
            #List of hosts, change to importing from JSON later
            "zeromonitor@123.345.23",
            "zeromonitor@123.343.12",
            "zeromonitor@123.245.64",
            # Adds parameters to paramiko connect function
            connect_kwargs={"key_filename": "~/.ssh/id_rsa"}
        )
        return group
    
    def _get_metrics(self, targets: ThreadingGroup) -> Dict[str, Optional[float]]:
        """Polls remote hosts and returns desired metrics (or errors)"""
        disk_usage = targets.run("df -h /")
        

        
        
