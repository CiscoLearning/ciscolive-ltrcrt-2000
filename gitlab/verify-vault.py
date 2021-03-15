import argparse
import logging
import requests
import hvac
import json
import os
logger = logging.getLogger('vault-verify')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vault Init')
    parser.add_argument('--vault', default="http://10.10.20.50:1234", help='the vault server')
    parser.add_argument('--log', default="INFO")
    args = parser.parse_args()

    logger.setLevel(args.log)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    client = hvac.Client(args.vault, os.getenv("VAULT_TOKEN"))
    data = client.read("kv-v1/aci/bootcamp")
    logger.info(data)

    logger.info(data["data"]["ACI_USERNAME"])
    logger.info(data["data"]["ACI_PASSWORD"])



