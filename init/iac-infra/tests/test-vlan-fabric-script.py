import logging
import os

# Importing pyATS and Genie libraries for automated testing and network device interaction
from pyats import aetest  # pyATS test automation framework
from pyats.log.utils import banner  # Utility for creating log banners
from genie.testbed import load as tbload  # Genie library for loading testbed configurations
from tabulate import tabulate  # Library for creating textual tables
from yaml import load  # YAML library for loading configuration files

# Attempt to use CLoader for faster YAML parsing; fall back to default Loader if unavailable
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Set up logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

# List of VLANs to ignore during checks
IGNORE_VLANS = ["1", "1002", "1003", "1004", "1005"]

# Function to expand VLAN ranges given as strings into lists of individual VLAN IDs
def expand_range(r):
    # From https://stackoverflow.com/questions/18759512/expand-a-range-which-looks-like-1-3-6-8-10-to-1-2-3-6-8-9-10
    rl = [s.split("-") for s in r.split(",")]  # Extract each comma-separated range element
    rl = [range(int(i[0]), int(i[1]) + 1) if len(i) == 2 else i for i in rl]  # Expand the ranges
    return [int(item) for sl in rl for item in sl]  # Flatten the list and convert to integers

# Define a class for VLAN setup, inheriting from aetest.CommonSetup
class VlanSetup(aetest.CommonSetup):
    
    # Subsection to connect to devices
    @aetest.subsection
    def connect_to_devices(self):
        creds = {}
        vfabric = {}
        
        # Load credentials and VLAN fabric configuration files
        cred_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"))
        fabric_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "vlan-fabric.yml"))
        with open(cred_file) as fd:
            creds = load(fd, Loader=Loader)  # Load credentials from YAML file
        with open(fabric_file) as fd:
            vfabric = load(fd, Loader=Loader)  # Load VLAN fabric configuration from YAML file
        
        # Set environment variables for pyATS authentication
        os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
        os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]
        os.environ["PYATS_AUTH_PASS"] = creds["ansible_ssh_pass"]
        
        # Load the testbed configuration
        testbed = tbload(os.path.realpath(os.path.join(os.path.dirname(__file__), "testbed", "testing.yml")))
        self.parent.parameters["testbed"] = testbed
        self.parent.parameters["vfabric"] = vfabric["fabric"]
        
        # Connect to all devices in parallel
        testbed.connect()

    # Subsection to prepare test cases
    @aetest.subsection
    def prepare_testcases(self, testbed):
        # Mark VlanCheck tests to run on distribution and access switches
        aetest.loop.mark(VlanCheck, device=[d.name for d in testbed if (d.type == "dist-switch" or d.type == "access-switch")])

# Define a class for VLAN checks, inheriting from aetest.Testcase
class VlanCheck(aetest.Testcase):
    
    # Setup method to gather VLAN and STP information from the device
    @aetest.setup
    def setup(self, device, testbed):
        d = testbed.devices[device]
        if not d.connected:
            self.failed(f"Device {device} is not connected; failed to learn operational details")
            return

        self.type = d.type

        # Log and gather VLAN information
        log.info(banner(f"Gathering VLAN info from {device}"))
        self.vlan = d.learn("vlan")

        # Log and gather STP (Spanning Tree Protocol) summary and detailed information
        log.info(banner(f"Gathering STP info from {device}"))
        self.stp_summ = d.parse("show spanning-tree summary")
        self.stp_det = d.parse("show spanning-tree detail")

        # Skip root checks for non-distribution switches and not-root checks for non-access switches
        aetest.skipIf.affix(VlanCheck.stp_check_root, condition=(d.type != "dist-switch"), reason="Not a distribution switch")
        aetest.skipIf.affix(VlanCheck.stp_check_not_root, condition=(d.type != "access-switch"), reason="Not a distribution switch")

    # Test to verify VLAN existence
    @aetest.test
    def vlan_exists_test(self, device, vfabric):
        global IGNORE_VLANS
        has_failed = False
        table_data = []  # List to store table rows for logging
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]  # List of VLAN IDs from fabric configuration
        i = 0

        # Check if each VLAN in the fabric configuration exists on the device
        for v in vlans:
            table_row = []
            table_row.append(device)
            table_row.append(v)
            table_row.append(vfabric["vlans"]["l2"][i]["name"])
            if v not in self.vlan.info["vlans"]:
                has_failed = True
                table_row.append("Failed (Missing)")
            else:
                table_row.append("Passed")
            table_data.append(table_row)
            i += 1

        # Check if there are any extra VLANs on the device that are not in the fabric configuration
        for v, vinfo in self.vlan.info["vlans"].items():
            if str(v) not in IGNORE_VLANS and str(v) not in vlans:
                has_failed = True
                table_row = [device, v, vinfo["name"], "Failed (Extra)"]
                table_data.append(table_row)

        # Log the results in a tabular format
        log.info(
            tabulate(
                table_data,
                headers=["Device", "VLAN ID", "VLAN Name", "Passed/Failed"],
                tablefmt="orgtbl",
            )
        )

        if has_failed:
            self.failed("There is some VLAN database discrepancies!")
        else:
            self.passed("All VLANs present and accounted for!")

    # Test to check if the device is the root bridge for the expected VLANs (distribution switches)
    @aetest.test
    def stp_check_root(self, device, vfabric):
        global IGNORE_VLANS
        has_failed = False
        table_data = []
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]  # List of VLAN IDs from fabric configuration

        # Get the list of VLANs for which this device is the root bridge from STP summary
        root_vlans = self.stp_summ["root_bridge_for"].split(",")
        root_vlans = [s.strip() for s in root_vlans]

        # Check if the device is the root bridge for each VLAN
        for v in vlans:
            if str(v) in IGNORE_VLANS:
                continue

            table_row = []
            table_row.append(device)
            table_row.append(v)
            if f"VLAN{v.zfill(4)}" not in root_vlans:
                table_row.append("N")
                has_failed = True
                table_row.append("Failed")
            else:
                table_row.append("Y")
                table_row.append("Passed")
            table_data.append(table_row)

        # Log the results in a tabular format
        log.info(
            tabulate(
                table_data,
                headers=["Device", "VLAN ID", "Is Root? ", "Passed/Failed"],
                tablefmt="orgtbl",
            )
        )

        if has_failed:
            self.failed("This switch is not the root bridge for some VLANs!")
        else:
            self.passed("STP root bridge data is consistent")

    # Test to check if the device is not the root bridge for any VLANs (access switches)
    @aetest.test
    def stp_check_not_root(self, device, vfabric):
        global IGNORE_VLANS
        has_failed = False
        table_data = []
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]  # List of VLAN IDs from fabric configuration

        # Get the list of VLANs for which this device is the root bridge from STP summary
        root_vlans = self.stp_summ["root_bridge_for"].split(",")
        root_vlans = [s.strip() for s in root_vlans]

        # Check if the device is not the root bridge for each VLAN
        for v in vlans:
            if str(v) in IGNORE_VLANS:
                continue

            table_row = []
            table_row.append(device)
            table_row.append(v)
            if f"VLAN{v.zfill(4)}" in root_vlans:
                table_row.append("Y")
                has_failed = True
                table_row.append("Failed")
            else:
                table_row.append("N")
                table_row.append("Passed")
            table_data.append(table_row)

        # Log the results in a tabular format
        log.info(
            tabulate(
                table_data,
                headers=["Device", "VLAN ID", "Is Root? ", "Passed/Failed"],
                tablefmt="orgtbl",
            )
        )

        if has_failed:
            self.failed("This switch is the root VLAN for some VLANs (missing on trunk?)!")
        else:
            self.passed("STP root bridge data is consistent")

    # Test to check if all trunk ports are forwarding and carrying the correct VLANs
    @aetest.test
    def stp_check_ports(self, device, vfabric):
        global IGNORE_VLANS
        has_failed = False
        table_data = []

        # Determine the switch type (distribution or access) for trunk port checks
        ttype = "distribution"
        if self.type == "access-switch":
            ttype = "access"

        # List of trunk ports from the fabric configuration
        trunk_ports = [d["port"] for d in vfabric["trunk_ports"][ttype]]
        avlans = []  # List of access VLANs for access switches
        if self.type == "access-switch":
            avlans = [str(d["access_vlan"]) for d in vfabric["access_ports"][device]]

        # Check each VLAN's STP details for trunk port status
        for v, vinfo in self.stp_det["pvst"]["vlans"].items():
            if str(v) in IGNORE_VLANS:
                continue

            i = 0
            for port in trunk_ports:
                port_failed = False
                table_row = []
                table_row.append(device)
                table_row.append(v)
                table_row.append(port)
                allowed_vlans = expand_range(str(vfabric["trunk_ports"][ttype][i]["allowed_vlans"]))
                if int(v) in allowed_vlans or str(v) in avlans:
                    table_row.append("Y")
                    if port not in vinfo["interfaces"]:
                        has_failed = port_failed = True
                        table_row.append("N")
                        table_row.append("N/A")
                    else:
                        table_row.append("Y")
                        table_row.append(vinfo["interfaces"][port]["status"])
                        if "forwarding" not in vinfo["interfaces"][port]["status"]:
                            has_failed = port_failed = True
                else:
                    table_row.append("N")
                    table_row.append("N/A")
                    table_row.append("N/A")

                if port_failed:
                    table_row.append("Failed")
                else:
                    table_row.append("Passed")

                i += 1
                table_data.append(table_row)

        # Log the results in a tabular format
        log.info(
            tabulate(
                table_data,
                headers=[
                    "Device",
                    "VLAN ID",
                    "Trunk Port",
                    "Should Carry VLAN?",
                    "Does Carry VLAN?",
                    "Port Status",
                    "Passed/Failed",
                ],
                tablefmt="orgtbl",
            )
        )

        if has_failed:
            self.failed("STP Port inconsistencies detected!")
        else:
            self.passed("All trunk ports are forwarding and carrying the right VLANs")
