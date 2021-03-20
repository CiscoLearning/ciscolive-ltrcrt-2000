#!/usr/bin/env python

import os


def main(runtime):
    testscript = os.path.join(os.path.dirname(__file__), "test-connectivity-script.py")

    runtime.tasks.run(testscript=testscript)
