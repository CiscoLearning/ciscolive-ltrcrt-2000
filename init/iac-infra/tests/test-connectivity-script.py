import logging
import os
import json
from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load as tbload
from tabulate import tabulate
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

PING_TARGET = "192.168.255.1"
HOST_DP_INTF = "ens3"


class VlanSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect_to_devices(self):
        creds = {}
        cred_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"))
        with open(cred_file) as fd:
            creds = load(fd, Loader=Loader)

        os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
        os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]
        os.environ["PYATS_AUTH_PASS"] = creds["ansible_ssh_pass"]

        testbed = tbload(os.path.realpath(os.path.join(os.path.dirname(__file__), "testbed-testing.yml")))
        self.parent.parameters["testbed"] = testbed

        # Connect to all devices in parallel.
        testbed.connect()

    @aetest.subsection
    def prepare_testcases(self, testbed):
        aetest.loop.mark(ConnCheck, device=[d.name for d in testbed if (d.type == "host")])


class ConnCheck(aetest.Testcase):
    @aetest.setup
    def setup(self, device, testbed):
        global PING_TARGET

        d = testbed.devices[device]
        if not d.connected:
            self.failed(f"Device {device} is not connected; failed to learn operational details")
            return

        log.info(banner(f"Getting interface data from {device}"))
        self.ifconfig = json.loads(d.execute(f"ip -j addr show {HOST_DP_INTF}"))

        log.info(banner(f"Pinging {PING_TARGET} from {device}"))
        # The device model itself provides a ping() method, but this one shows how you
        # execute arbitrary CLI commands.
        self.ping = d.execute(f"ping -c 1 -W 3 {PING_TARGET}")

    @aetest.test
    def intf_has_ip(self, device):
        has_failed = False
        table_data = []
        found_ipv4 = False

        if "addr_info" in self.ifconfig[0]:
            for addr in self.ifconfig[0]["addr_info"]:
                if addr["family"] == "inet":
                    found_ipv4 = True
                    table_row = [device, HOST_DP_INTF]
                    table_row.append(addr["local"])
                    table_row.append("Passed")

                    table_data.append(table_row)

        if not found_ipv4:
            table_row = [device, HOST_DP_INTF, "N/A", "Failed"]
            table_data.append(table_row)
            has_failed = True

        log.info(tabulate(table_data, headers=["Device", "Interface", "Address", "Passed/Failed"], tablefmt="orgtbl"))

        if has_failed:
            self.failed(f"No IP address found for {HOST_DP_INTF}!")
        else:
            self.passed("Host has an IPv4 address")

    @aetest.test
    def check_ping(self, device):
        if "1 received," not in self.ping:
            self.failed(f"Ping to {PING_TARGET} failed from {device}: '{self.ping}'!")
        else:
            self.passed(f"Target {PING_TARGET} is reachable from {device}")
