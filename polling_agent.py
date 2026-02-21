import threading
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional
from abc import ABC, abstractmethod
from fabric import Connection
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

# This object is the direct result of metrics collection
@dataclass
class SystemMetrics:
    hostname: str
    timestamp: str
    cpu_temp_c: Optional[float]
    cpu_load_1m: Optional[float]
    mem_total_mb: Optional[int]
    mem_used_mb: Optional[int]
    disk_used_percent: Optional[float]

# This object is passed to the metrics queue and includes system metrics
@dataclass
class MetricEvent:
    # Common name of node
    node: str
    # Status of last polling attempt
    success: bool
    # Metrics data
    payload: dict
    # Timestamp
    timestamp: str

# Abstract base class for all operating systems to be implmeneted
class MetricsProvider(ABC):
    def __init__(self, conn: Connection):
        self.conn = conn

    @abstractmethod
    def collect(self, node_name: str, stop_event=None) -> SystemMetrics:
        """Abstract method to be implemented by subclasses"""
        pass

# This class represents a single target device
@dataclass
class Node:
    # Common Name
    name: str
    # OS Specific MetricsProvider object (already contains hostname)
    provider: MetricsProvider
    # Configurable Polling Interval
    interval: int
    # Used to stop/start/restart nodes when config changes
    stop_event: threading.Event | None = None
    # Used for exponential backoff logic
    fail_count: int = 0

# This class collects data from a Linux system and returns a SystemMetrics object
class LinuxMetricsProvider(MetricsProvider):
    def collect(self, node_name: str, stop_event=None) -> SystemMetrics:
        """Linux specific metrics provider"""
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
        result = self.conn.run(
            cmd,
            hide=True,
            timeout=10,
            node_name=node_name,
            stop_event=stop_event
        )
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

        mem_total = mem_used = None
        if "MEM" in data and "," in data["MEM"]:    
            mem_total, mem_used = map(int, data["MEM"].split(","))

        return SystemMetrics(
            hostname=data["HOST"],
            timestamp = datetime.now().isoformat(),
            cpu_temp_c=cpu_temp,
            cpu_load_1m=float(data["LOAD"]),
            mem_total_mb=mem_total,
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"].replace("%", "")),
        )
    
# This class collects data from a Windows system and returns a SystemMetrics object
class WindowsMetricsProvider(MetricsProvider):
    def collect(self, node_name: str, stop_event=None) -> SystemMetrics:
        """Windows specific metrics provider"""
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
        result = self.conn.run(
            cmd,
            hide=True,
            timeout=10,
            node_name=node_name,
            stop_event=stop_event
        )
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
            timestamp = datetime.now().isoformat(),
            cpu_temp_c=None,
            cpu_load_1m=float(data["CPU"]) / 100.0,
            mem_total_mb=int(mem_total),
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"]),
        )
    

# This class maintains a persistent ssh session with targets to reduce polling overhead 
class PersistentConnection:
    """Persistent connection to reduce SSH overhead"""
    def __init__(self, host: str, user: str, connect_timeout=5, max_retries=5):
        self.host = host
        self.user = user
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries
        self.conn: Optional[Connection] = None
        # Semaphore for thread safety
        self.lock = threading.Lock() 

    def open(self):
        """Open connection if not already open"""
        # Lock semaphore
        with self.lock:
            # Create conneciton if it doesnt exist
            if self.conn is None:
                self.conn = Connection(
                    host=self.host,
                    user=self.user,
                    connect_timeout=self.connect_timeout
                )

    def run(self, cmd, node_name=None, stop_event=None, **kwargs):
        """Run a command with automatic reconnect and retries"""
        retries = 0
        # If we are under max retries
        while retries < self.max_retries:
            try:
                # Try to open connection
                self.open()
                # return successful connection
                return self.conn.run(cmd, **kwargs)
            except Exception as e:
                # else, record error, and retry
                name = node_name if node_name else self.host
                logging.warning(
                    "[%s] SSH command failed: %s (retry %d/%d)",
                    name, e, retries + 1, self.max_retries
                )
                retries += 1
                # Close the connection and retry
                with self.lock:
                    if self.conn:
                        try:
                            self.conn.close()
                        except Exception:
                            pass
                        self.conn = None
                # exponential backoff for connection retries, max 10 seconds
                sleep_time = min(2 ** retries, 10)

                if stop_event and stop_event.wait(sleep_time):
                    raise RuntimeError("Command aborted due to shutdown")
                else:
                    time.sleep(sleep_time)

        name = node_name if node_name else self.host
        raise RuntimeError(f"SSH connection to {name} failed after {self.max_retries} retries")

    def close(self):
        """Close connection explicitly"""
        # Lock Semaphore
        with self.lock:
            # Repeatedly close connection
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None

# This class handles polling nodes, it is created and owned by driver
# Driver will use this manager to handle the collection of metrics from targets
# Has various methods relating to all things polling
class PollingAgent:
    """Manages worker threads for polling nodes"""
    def __init__(self, queue: Queue):
        self.workers = {}  # node_name -> (Node, Future)
        self.worker_executor = ThreadPoolExecutor(max_workers=50)
        self.queue = queue

    def launch_nodes(self, nodes: list[Node]):
        """Function to start polling all nodes"""
        self.reconcile(nodes)

    def reconcile(self, new_nodes):
        """Function to reconcile the currently running worker set with the latest configuration"""
        # Gather information about current node list, and new node list
        new_map = {n.name: n for n in new_nodes}
        current_names = set(self.workers.keys())
        new_names = set(new_map.keys())

        # This block starts any new nodes that have been added
        for name in new_names - current_names:
            self.add_node(new_map[name])

        # This block removes any nodes that have been removed from device_list
        for name in current_names - new_names:
            self.remove_node(name)

        # This block checks for any updated configuration for existing nodes (ie polling interval changes)
        for name in new_names & current_names:
            self.update_node(new_map, name)
    
    def add_node(self, node: Node):
        """Function to add a polling target"""
        # Create the nodes stop_event
        node.stop_event = threading.Event()

        # Add worker thread to threadpool
        future = self.worker_executor.submit(run_node, node, self.queue)

        # Add worker thread to active workers list
        self.workers[node.name] = (node, future)
        logging.info("Started worker: %s", node.name)

    def remove_node(self, name: str):
        """Function to remove an active node"""
        # Remove node from active workers list
        entry = self.workers.pop(name, None)

        # If invalid, stop
        if not entry:
            return

        # Stop the node itself by setting stop_event
        node, future = entry
        node.stop_event.set()
        logging.info("Stopping worker: %s", name)

    def update_node(self, new_map: dict, name: str):
        """Function to update a nodes configuration"""
        old_node, _ = self.workers[name]
        new_node = new_map[name]

        # If interval has changed, reload worker with new settings
        if new_node.interval != old_node.interval:
            logging.info("Reloading worker: %s", name)
            # Stop old node
            old_node.stop_event.set()

            # Create new_nodes stop event
            new_node.stop_event = threading.Event()

            # Add worker thread to threadpool, start it
            future = self.worker_executor.submit(run_node, new_node, self.queue)

            # Add worker to active workers list
            self.workers[name] = (new_node, future)

    def stop_all_nodes(self):
        """Function to stop polling all nodes"""
        for name in list(self.workers.keys()):
            self.remove_node(name)

    def shutdown(self):
        """Fully shutdown executor"""
        self.stop_all_nodes()
        self.worker_executor.shutdown(wait=True, cancel_futures=True)

def run_node(node: Node, queue: Queue):
    """Worker thread loop for a single node"""
    # Create logger for specific worker thread
    logger = logging.getLogger(f"worker.{node.name}")

    # Load variables from specific node
    stop_event = node.stop_event
    interval = node.interval
    conn = node.provider.conn

    # Schedule first run immediately
    next_run = time.monotonic()

    try:
        # Main worker loop
        while True:

            # Kill worker thread when stop_event flag is set
            if stop_event.is_set():
                logger.info("Worker stopping")
                return

            now = time.monotonic()

            # Calculate time until next scheduled run
            wait_time = next_run - now
            # Wait until next scheduled run 
            if wait_time > 0:
                # wait() returns True if stop_event triggered, immediately shuts down workers if stop_event is set
                if stop_event.wait(wait_time):
                    logger.info("Worker stopped during wait")
                    return

            # If wait time is over, try to collect metrics
            try:
                metrics = node.provider.collect(
                    node.name,
                    stop_event=stop_event
                )
                logger.info("metrics collected successfully for %s", node.name)
                # Put metrics in the queue
                queue.put(MetricEvent(
                    node=node.name,
                    success=True,
                    payload=asdict(metrics),
                    timestamp=datetime.now().isoformat()
                ))

            # If collection fails, gracefully handle and display reason
            except Exception as e:
                logger.warning("collection failed: %s", e)
                queue.put(MetricEvent(
                    node=node.name,
                    success=False,
                    payload={"error": str(e)},
                    timestamp=datetime.now().isoformat()
                ))

            # Schedule the next execution time (avoid timing drift)
            next_run += interval

            # If collection took too long, schedule now
            if next_run < time.monotonic():
                next_run = time.monotonic()

    # Exit that runs no matter what to close persistent ssh connection
    finally:
        logger.info("Closing SSH connection")
        try:
            conn.close()
        except Exception:
            pass