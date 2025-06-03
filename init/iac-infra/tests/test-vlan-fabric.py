#!/usr/bin/env python

import os

import yaml
from genie.testbed import load


def main(runtime):
    if runtime.testbed:
        print("Can't provide testbed via CLI flags")
        return

    # Load credentials and VLAN fabric configuration files
    cred_file = os.path.realpath(
        os.path.join(
            os.path.dirname(__file__), "..", "ansible", "group_vars", "all.yml"
        )
    )
    with open(cred_file) as fd:
        creds = yaml.safe_load(fd)  # Load credentials from YAML file

    # Set environment variables for pyATS authentication
    os.environ["PYATS_USERNAME"] = creds["ansible_ssh_user"]
    os.environ["PYATS_PASSWORD"] = creds["ansible_ssh_pass"]

    # Load the testbed configuration
    testbed = load(
        os.path.realpath(os.path.join(os.path.dirname(__file__), "testbed-testing.yml"))
    )

    # Find the location of the script in relation to the job file
    testscript = os.path.join(os.path.dirname(__file__), "test-vlan-fabric-script.py")

    # Run the script
    runtime.tasks.run(testscript=testscript, testbed=testbed)
