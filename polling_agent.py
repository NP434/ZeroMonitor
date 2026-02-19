from dataclasses import dataclass, asdict
from typing import Optional
from abc import ABC, abstractmethod
from fabric import Connection
from concurrent.futures import ThreadPoolExecutor
from json import dump, load
import time
from datetime import datetime
from queue import Queue
import threading
import os
import logging

# Architecture as it exists:

# Supervisor class: Acting as driver
# Runs two controller servicers:
# metrics consumer (Data interpreter), 
# and config watcher (this module will stay in driver)
#
# config watcher checks to see if device_list (later full config file) has changed
# performs updates accordingly
#
# if device_list has changed, config watcher calls reconcile to make the current state
# of execution match the current configuration
#
# Reconcile function handles addition of new nodes, removal of nodes, or changes to node settings
# 
# If new node
# Check to see which node is new, add it to threadpool, set it off
# each node schedules itself and can be stopped with a flag "stop_event"
# Each node also publishes its data to the supervisor/driver owned queue in the data format MetricsEvent
#
# If removed node
# Stop it gracefully and delete it
#
# If node settings has changed
# Relaunch them with updated settings
# 
# Metrics consumer will later be implmeneted as the "Data Interpreter" module
# It will 1. Pull MetricsEvents from Supervisor/Driver owned queue, 2. interpret them 
# (compare with thresholds, add to cache if successful, get everything ready for display)
# and 3. push these interpreted metrics into another queue that will go directly to the UI

# Standardized logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

# Create unique loggers for each segment 
log_supervisor = logging.getLogger("supervisor")
log_worker = logging.getLogger("worker")
log_consumer = logging.getLogger("consumer")

# This object is passed to the data queue and includes system metrics
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

# Abstract base class for all operating systems to be implmeneted
class MetricsProvider(ABC):
    def __init__(self, conn: Connection):
        self.conn = conn

    @abstractmethod
    def collect(self) -> SystemMetrics:
        """Abstract method to be implemented by subclasses"""
        pass

# This class collects data from a Linux system and returns a SystemMetrics object
class LinuxMetricsProvider(MetricsProvider):
    def collect(self) -> SystemMetrics:
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
        result = self.conn.run(cmd, hide=True, timeout=10)
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
            timestamp = datetime.now().isoformat(),
            cpu_temp_c=cpu_temp,
            cpu_load_1m=float(data["LOAD"]),
            mem_total_mb=mem_total,
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"].replace("%", "")),
        )

# This class collects data from a Windows system and returns a SystemMetrics object
class WindowsMetricsProvider(MetricsProvider):
    def collect(self) -> SystemMetrics:
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
            timestamp = datetime.now().isoformat(),
            cpu_temp_c=None,
            cpu_load_1m=float(data["CPU"]) / 100.0,
            mem_total_mb=int(mem_total),
            mem_used_mb=mem_used,
            disk_used_percent=float(data["DISK"]),
        )

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

# Load and initialize targets from device_list.json
def load_targets() -> list:
    """Function to load and initialize targets from device_list.json"""
    nodes = []
    with open("device_list.json", "r") as file:
        data = load(file)
    items = data.values()

    for item in items:
        host = item.get("hostname")
        user = item.get("user")
        name = item.get("name")
        os_type = item.get("operating_system")
        poll_freq = int(item.get("polling_frequency", 5))

        conn = Connection(host=host, user=user, connect_timeout=5)
        if(os_type.lower() == "linux"):
            provider = LinuxMetricsProvider(conn)
        elif(os_type.lower() == "windows"):
            provider = WindowsMetricsProvider(conn)
        else:
            # Gracefully handle error if OS is unsupported
            log_supervisor.warning(
                "Skipping node '%s' — unsupported OS '%s'",
                name,
                os_type,
            )
            continue

        nodes.append(Node(name=name, provider=provider, interval=poll_freq))
    # Returns list of node objects
    return nodes

def run_node(node: Node, queue: Queue):
    """Worker thread loop for a single node"""
    # Create logger for specific worker thread
    logger = logging.getLogger(f"worker.{node.name}")

    stop_event = node.stop_event
    interval = node.interval

    # schedule first run immediately
    next_run = time.monotonic()

    # Main worker loop
    while True:

        # Kill worker thread when stop_event flag is set
        if stop_event.is_set():
            print(f"[{node.name}] stopping worker")
            return

        now = time.monotonic()

        # Calculate time until next scheduled run
        wait_time = next_run - now
        # Wait until next scheduled run 
        if wait_time > 0:
            # wait() returns True if stop_event triggered
            if stop_event.wait(wait_time):
                print(f"[{node.name}] stopped during wait")
                return

        # If wait time is over, try to collect metrics
        try:
            metrics = node.provider.collect()
            logger.info("metrics collected successfully")
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

# Driver class, to be migrated to driver module (seperate file with access to UI and polling agent methods)
class Supervisor:
    def __init__(self):
            # Group of workers
            self.workers = {}

            # Queue where all metrics providers output their collected metrics
            self.queue = Queue()

            # Control Threads
            self.control_executor = ThreadPoolExecutor(max_workers=2)

            # polling workers
            self.worker_executor = ThreadPoolExecutor(max_workers=50)

    def start(self):
        """Function to launch all control threads"""
        # Creates two worker threads, one to consume metrics (This will later be the Data Interpreter Module)
        self.control_executor.submit(metrics_consumer, self.queue)
        # And another to watch for config updates and update worker threads accordingly
        self.control_executor.submit(self.watch_config)

# Later, this function will need to handle first launch vs. regular launch behavior
# Check config, its empty? first launch routine, its got information? run as usual and revert state
    def watch_config(self):
        """Function to check config and launch worker threads accordingly"""

        # Variable to store the last time that device_list.json was modified
        last_mtime = 0 

        while True:
            try:
                # Check if device_list was changed
                mtime = os.path.getmtime("device_list.json")

                # If it has been changed
                if mtime != last_mtime:
                    # Record the time, relaunch worker threads
                    last_mtime = mtime
                    log_supervisor.info("Config changed — reloading")

                    # Update node list, reconcile targets
                    nodes = load_targets()
                    self.reconcile(nodes)

            except Exception as e:
                log_supervisor.error("Config reload failed: %s", e)

            time.sleep(2)

    # Reconcile function allows for hot-reload behavior for node monitoring
    # compares the active workers managed by the Superviser against the nodes defined in the newly loaded configuration file 
    # performs actions to synchronize them 
    def reconcile(self, new_nodes):
        """Function to reconcile the currently running worker set with the latest configuration"""
        # Gather information about current node list, and new node list
        new_map = {n.name: n for n in new_nodes}
        current_names = set(self.workers.keys())
        new_names = set(new_map.keys())

        # This block starts any new nodes that have been added
        for name in new_names - current_names:
            # Create node
            node = new_map[name]
            # Create its own stop_event object that can be invoked with .set()
            node.stop_event = threading.Event()

            # Submit new node to worker_executor pool
            future = self.worker_executor.submit(run_node, node, self.queue)

            # Add node to supervisor/driver worker list
            self.workers[name] = (node, future)
            log_supervisor.info("Started worker: %s", name)

        # This block removes any nodes that have been removed from device_list
        for name in current_names - new_names:
            # Pop that node from workers list
            node, future = self.workers.pop(name)
            # Trigger that nodes stop event
            node.stop_event.set()
            log_supervisor.info("Stopping worker: %s", name)

        # This block checks for any updated configuration for existing nodes (ie polling interval changes)
        for name in new_names & current_names:
            old_node, _ = self.workers[name]
            new_node = new_map[name]

            # Currently only interval changes require restart
            if new_node.interval != old_node.interval:
                log_supervisor.info("Reloading worker: %s", name)

                # Stop old worker gracefully
                old_node.stop_event.set()

                # Start replacement worker with new settings
                new_node.stop_event = threading.Event()
                future = self.worker_executor.submit(run_node, new_node, self.queue)

                self.workers[name] = (new_node, future)

# Later, this function will be adapted to be the Data intepreter, which will 
# Consume data from queue, interpret it, and put it into another queue for the UI
def metrics_consumer(queue):
    """Function to recieve metrics from the supervisor/drivers queue"""
    while True:
        # Pull next event in queue
        event = queue.get()

        # If successful, write data to cache
        if event.success:
            filename = f"{event.node}_cache.json"
            with open(filename, "w") as f:
                dump(event.payload, f, indent=4)
        # Log cache update
        log_consumer.info("cache updated: %s", event.node)

# Main entry into program, will likely function similarly in final driver code
if __name__ == "__main__":
    Supervisor().start()

    while True:
        time.sleep(60)