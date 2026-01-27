from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod
from fabric import Connection
import time
from concurrent.futures import ThreadPoolExecutor

@dataclass
class SystemMetrics:
    hostname: str
    cpu_temp_c: Optional[float]
    cpu_load_1m: Optional[float]
    mem_total_mb: Optional[int]
    mem_used_mb: Optional[int]
    disk_used_percent: Optional[float]

class MetricsProvider(ABC):
    def __init__(self, conn: Connection):
        self.conn = conn

    @abstractmethod
    def collect(self) -> SystemMetrics:
        pass

class LinuxMetricsProvider(MetricsProvider):
    def collect(self) -> SystemMetrics:
        cmd = r"""
HOST=$(hostname)
TEMP=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "")
LOAD=$(cut -d' ' -f1 /proc/loadavg)
MEM=$(free -m | awk 'NR==2{print $2","$3}')
DISK=$(df -h / | awk 'NR==2{print $5}')

echo "HOST=$HOST"
echo "TEMP=$TEMP"
echo "LOAD=$LOAD"
echo "MEM=$MEM"
echo "DISK=$DISK"
"""
        result = self.conn.run(cmd, hide=True)
        data = {}

        for line in result.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip()

        cpu_temp = (
            int(data["TEMP"]) / 1000.0
            if data.get("TEMP", "").isdigit()
            else None
        )

        mem_total, mem_used = map(int, data["MEM"].split(","))

        return SystemMetrics(
            hostname=data["HOST"],
            cpu_temp_c=cpu_temp,
            cpu_load_1m=float(data["LOAD"]),
            mem_total_mb=mem_total,
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"].replace("%", "")),
        )

class WindowsMetricsProvider(MetricsProvider):
    def collect(self) -> SystemMetrics:
        cmd = r"""
powershell -Command "
$hostn = hostname
$cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
$memTotal = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB
$memFree = (Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue
$disk = (Get-PSDrive C).Used / (Get-PSDrive C).Maximum * 100

Write-Output \"HOST=$hostn\"
Write-Output \"CPU=$cpu\"
Write-Output \"MEM=$memTotal,$memFree\"
Write-Output \"DISK=$disk\"
"""
        result = self.conn.run(cmd, hide=True)
        data = {}

        for line in result.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip()

        mem_total = float(data["MEM"].split(",")[0])
        mem_free = float(data["MEM"].split(",")[1])
        mem_used = int(mem_total - mem_free)

        return SystemMetrics(
            hostname=data["HOST"],
            cpu_temp_c=None,
            cpu_load_1m=float(data["CPU"]) / 100.0,
            mem_total_mb=int(mem_total),
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"]),
        )

@dataclass
class Node:
    # Common Name
    name: str
    # Connection ready to provide metrics
    provider: MetricsProvider

nodes = [
    Node(
        name="AlecsPi5",
        provider=LinuxMetricsProvider(
            # This connection references the Hosts found within .ssh/config
            # Will need to change this to accept raw parameters (Host, User, HostName) (AlecsPi5, alechoelscher, 192.168.-.-)
            Connection("AlecsPi5")
        )
    ),
    Node(
        name="AlecsPC",
        provider=WindowsMetricsProvider(
            Connection("AlecsPC")
        )
    ),
]

def poll_node(node: Node):
    """Function to poll a single node and handle errors gracefully"""
    try:
        return node.name, node.provider.collect()
    except Exception as e:
        return node.name, f"ERROR: {e}"

def poll_nodes(nodes, interval=5):
    """Function to poll multiple nodes concurrently using ThreadPoolExecutor"""
    with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
        # Polling loop
        while True:
            futures = [executor.submit(poll_node, n) for n in nodes]

            for f in futures:
                name, result = f.result()
                print(name, result)

            print("-" * 60)
            time.sleep(interval)

if __name__ == "__main__":
    poll_nodes(nodes, interval=5)