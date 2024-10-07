# Import necessary modules
import logging
import os
import json
from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load as tbload
from tabulate import tabulate
from yaml import load

# Try importing CLoader for YAML parsing for better performance
# Fallback to default Loader if CLoader is not available
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Configure logging for the script
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Define constants for the ping target IP and the host interface name
# 192.168.255.1 is the IP address on the CML side of the NAT interface.
PING_TARGET = "192.168.255.1"
HOST_DP_INTF = "ens3"

# Define a class for VLAN setup, which is a common setup step for all tests
class VlanSetup(aetest.CommonSetup):

    # Subsection to connect to devices
    @aetest.subsection
    def connect_to_devices(self):
        creds = {}
        # Construct the file path to the credentials file
        cred_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"))
        
        # Load credentials from the specified YAML file
        with open(cred_file) as fd:
            creds = load(fd, Loader=Loader)

        # Set environment variables for pyATS with the loaded credentials
        os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
        os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]
        os.environ["PYATS_AUTH_PASS"] = creds["ansible_ssh_pass"]

        # Load the testbed configuration from the specified YAML file
        testbed = tbload(os.path.realpath(os.path.join(os.path.dirname(__file__), "testbed", "testing.yml")))
        self.parent.parameters["testbed"] = testbed

        # Connect to all devices in the testbed in parallel
        testbed.connect()

    # Subsection to prepare test cases
    @aetest.subsection
    def prepare_testcases(self, testbed):
        # Mark the ConnCheck test case to run for each host device in the testbed
        aetest.loop.mark(ConnCheck, device=[d.name for d in testbed if (d.type == "host")])

# Define a class for connection check test case, inheriting from aetest.Testcase
class ConnCheck(aetest.Testcase):

    # Setup function to be run before tests
    @aetest.setup
    def setup(self, device, testbed):
        global PING_TARGET
        # Get the device object from the testbed
        d = testbed.devices[device]
        
        # Check if the device is connected
        if not d.connected:
            self.failed(f"Device {device} is not connected; failed to learn operational details")
            return

        # Log and get interface data from the device using the 'ip' command
        log.info(banner(f"Getting interface data from {device}"))
        self.ifconfig = json.loads(d.execute(f"ip -j addr show {HOST_DP_INTF}"))

        # Log and ping the target IP from the device
        log.info(banner(f"Pinging {PING_TARGET} from {device}"))
        self.ping = d.execute(f"ping -c 1 -W 3 {PING_TARGET}")

    # Test to check if the interface has an IP address
    @aetest.test
    def intf_has_ip(self, device):
        has_failed = False
        table_data = []
        found_ipv4 = False

        # Check the interface configuration for an IPv4 address
        if "addr_info" in self.ifconfig[0]:
            for addr in self.ifconfig[0]["addr_info"]:
                if addr["family"] == "inet":
                    found_ipv4 = True
                    table_row = [device, HOST_DP_INTF, addr["local"], "Passed"]
                    table_data.append(table_row)

        # If no IPv4 address found, log failure
        if not found_ipv4:
            table_row = [device, HOST_DP_INTF, "N/A", "Failed"]
            table_data.append(table_row)
            has_failed = True

        # Log the results in a table format
        log.info(tabulate(table_data, headers=["Device", "Interface", "Address", "Passed/Failed"], tablefmt="orgtbl"))

        # Determine the outcome based on whether an IP address was found
        if has_failed:
            self.failed(f"No IP address found for {HOST_DP_INTF}!")
        else:
            self.passed("Host has an IPv4 address")

    # Test to check if the ping to the target is successful
    @aetest.test
    def check_ping(self, device):
        # Check the output of the ping command for success
        if "1 received," not in self.ping:
            self.failed(f"Ping to {PING_TARGET} failed from {device}: '{self.ping}'!")
        else:
            self.passed(f"Target {PING_TARGET} is reachable from {device}")
