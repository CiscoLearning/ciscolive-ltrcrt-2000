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


class VlanSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect_to_devices(self):
        creds = {}
        vfabric = {}
        cred_file = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"
            )
        )
        fabric_file = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "vlan-fabric.yml")
        )
        with open(cred_file) as fd:
            creds = load(fd, Loader=Loader)

        with open(fabric_file) as fd:
            vfabric = load(fd, Loader=Loader)

        os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
        os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]
        os.environ["PYATS_AUTH_PASS"] = creds["ansible_ssh_pass"]

        testbed = tbload(
            os.path.realpath(
                os.path.join(os.path.dirname(__file__), "testbed-testing.yml")
            )
        )
        self.parent.parameters["testbed"] = testbed
        self.parent.parameters["vfabric"] = vfabric["fabric"]

        # Connect to all devices in parallel.
        testbed.connect()

    @aetest.subsection
    def prepare_testcases(self, testbed):
        aetest.loop.mark(
            DistVlanCheck, device=[d.name for d in testbed if d.type == "dist-switch"]
        )
        # aetest.loop.mark(
        #    AccessVlanCheck,
        #    device=[d.name for d in testbed if d.type == "access-switch"],
        # )


class DistVlanCheck(aetest.Testcase):
    @aetest.setup
    def setup(self, device, testbed):
        d = testbed.devices[device]
        if not d.connected:
            self.failed(
                f"Device {device} is not connected; failed to learn operational details"
            )
            return

        log.info(banner(f"Gathering VLAN info from {device}"))
        self.vlan = d.learn("vlan")

        log.info(banner(f"Gathering STP info from {device}"))
        self.stp_summ = d.parse("show spanning-tree summary")
        self.stp_det = d.parse("show spanning-tree detail")

    @aetest.test
    def vlan_exists_test(self, device, vfabric):
        has_failed = False
        table_data = []

        IGNORE_VLANS = ["1", "1002", "1003", "1004", "1005"]

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

        for v, vinfo in self.vlan.info["vlans"].items():
            if v not in IGNORE_VLANS and v not in vlans:
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
        has_failed = False
        table_data = []
        vlans = [str(d["vlan_id"]) for d in vfabric["vlans"]["l2"]]

        root_vlans = self.stp_summ["root_bridge_for"].split(",")
        root_vlans = [s.strip() for s in root_vlans]

        for v in vlans:
            table_row = []
            table_row.append(device)
            table_row.append(v)
            if f"VLAN{v.zfill(4)}" not in root_vlans:
                table_row.append("N")
                has_failed = True
            else:
                table_row.append("Y")

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
