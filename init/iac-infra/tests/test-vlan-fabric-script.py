import logging
import os
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

IGNORE_VLANS = ["1", "1002", "1003", "1004", "1005"]


def expand_range(r):
    # From https://stackoverflow.com/questions/18759512/expand-a-range-which-looks-like-1-3-6-8-10-to-1-2-3-6-8-9-10
    rl = [s.split("-") for s in r.split(",")]  # Extract each comma-separated range element
    rl = [range(int(i[0]), int(i[1]) + 1) if len(i) == 2 else i for i in rl]  # expand the ranges

    return [int(item) for sl in rl for item in sl]


class VlanSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect_to_devices(self):
        creds = {}
        vfabric = {}
        cred_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"))
        fabric_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "vlan-fabric.yml"))
        with open(cred_file) as fd:
            creds = load(fd, Loader=Loader)

        with open(fabric_file) as fd:
            vfabric = load(fd, Loader=Loader)

        os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
        os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]
        os.environ["PYATS_AUTH_PASS"] = creds["ansible_ssh_pass"]

        testbed = tbload(os.path.realpath(os.path.join(os.path.dirname(__file__), "testbed-testing.yml")))
        self.parent.parameters["testbed"] = testbed
        self.parent.parameters["vfabric"] = vfabric["fabric"]

        # Connect to all devices in parallel.
        testbed.connect()

    @aetest.subsection
    def prepare_testcases(self, testbed):
        aetest.loop.mark(VlanCheck, device=[d.name for d in testbed if (d.type == "dist-switch" or d.type == "access-switch")])


class VlanCheck(aetest.Testcase):
    @aetest.setup
    def setup(self, device, testbed):
        d = testbed.devices[device]
        if not d.connected:
            self.failed(f"Device {device} is not connected; failed to learn operational details")
            return

        self.type = d.type

        log.info(banner(f"Gathering VLAN info from {device}"))
        self.vlan = d.learn("vlan")

        log.info(banner(f"Gathering STP info from {device}"))
        self.stp_summ = d.parse("show spanning-tree summary")
        self.stp_det = d.parse("show spanning-tree detail")

        aetest.skipIf.affix(VlanCheck.stp_check_root, condition=(d.type != "dist-switch"), reason="Not a distribution switch")
        aetest.skipIf.affix(VlanCheck.stp_check_not_root, condition=(d.type != "access-switch"), reason="Not a distribution switch")

    @aetest.test
    def vlan_exists_test(self, device, vfabric):
        global IGNORE_VLANS

        has_failed = False
        table_data = []

        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]

        i = 0
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

        for v, vinfo in self.vlan.info["vlans"].items():
            if str(v) not in IGNORE_VLANS and str(v) not in vlans:
                has_failed = True
                table_row = [device, v, vinfo["name"], "Failed (Extra)"]
                table_data.append(table_row)

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

    @aetest.test
    def stp_check_root(self, device, vfabric):
        global IGNORE_VLANS

        has_failed = False
        table_data = []
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]

        root_vlans = self.stp_summ["root_bridge_for"].split(",")
        root_vlans = [s.strip() for s in root_vlans]

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

        log.info(
            tabulate(
                table_data,
                headers=["Device", "VLAN ID", "Is Root?", "Passed/Failed"],
                tablefmt="orgtbl",
            )
        )

        if has_failed:
            self.failed("This switch is not the root bridge for some VLANs!")
        else:
            self.passed("STP root bridge data is consistent")

    @aetest.test
    def stp_check_not_root(self, device, vfabric):
        global IGNORE_VLANS

        has_failed = False
        table_data = []
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]

        root_vlans = self.stp_summ["root_bridge_for"].split(",")
        root_vlans = [s.strip() for s in root_vlans]

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

        log.info(tabulate(table_data, headers=["Device", "VLAN ID", "Is Root?", "Passed/Failed"], tablefmt="orgtbl"))

        if has_failed:
            self.failed("This switch is the root VLAN for some VLANs (missing on trunk?)!")
        else:
            self.passed("STP root bridge data is consistent")

    @aetest.test
    def stp_check_ports(self, device, vfabric):
        global IGNORE_VLANS

        has_failed = False
        table_data = []
        ttype = "distribution"
        if self.type == "access-switch":
            ttype = "access"

        trunk_ports = [d["port"] for d in vfabric["trunk_ports"][ttype]]
        avlans = []
        if self.type == "access-switch":
            avlans = [str(d["access_vlan"]) for d in vfabric["access_ports"][device]]

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
