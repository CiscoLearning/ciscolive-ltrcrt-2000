import argparse
import logging
import requests
import hvac
import json
logger = logging.getLogger('vault-helper')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vault Init')
    parser.add_argument('--vault', help='the vault server')
    parser.add_argument('--vault_token', help='the vault server')
    parser.add_argument('--vault_keys', nargs='+', help="the vault unseal keys")
    parser.add_argument('--vault_backend_type', default='kv-v2', help=' the Vault backend type for the secrets engine')
    parser.add_argument('--log', default="INFO")
    args = parser.parse_args()

    logger.setLevel(args.log)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Initialize the HVAC client
    logger.debug("initializing hvac client")
    client = hvac.Client(args.vault, args.vault_token)
    
    # Verify that the vault system is initialized. 
    logger.debug("vault is_initialized=%s", client.sys.is_initialized())
    assert client.sys.is_initialized() == True

    # Check if the engine secret is already enabled
    secret_engines = client.sys.list_mounted_secrets_engines()
    if f'{args.vault_backend_type}/' not in secret_engines:
        logger.debug("enabling secrets engine %s", args.vault_backend_type)
        client.sys.enable_secrets_engine(backend_type=args.vault_backend_type)
    else:
        logger.debug("secrets engine %s already enabled", args.vault_backend_type)
    # Check if the AppRole auth method is already enabled
    auth_methods = client.sys.list_auth_methods()
    logger.debug("listing auth methods auth_methods=%s", auth_methods)
    if "approle/" not in auth_methods:
        enable_auth_method = client.sys.enable_auth_method("approle")
        logger.debug("enabling auth_method approle response=%s", enable_auth_method)
    else:
        logger.debug("auth method approle already enabled")

    # Create default policy --- this is hardcoded for kv-v1 secret engines
    # TODO: support dynamic paths
    admin_policy = """
    path "kv-v1/aci/bootcamp" {
        capabilities = ["create", "read", "update", "delete", "list"]
    }
    """
    created_policy = client.sys.create_or_update_policy("aci-access", admin_policy)
    logger.debug("created/updated policy response=%s", created_policy)

    created_role = client.create_role("bootcamp", policies="aci-access")
    logger.debug("created role response=%s", created_role)

    role_id = client.get_role_id("bootcamp")
    secret_id = client.create_role_secret_id("bootcamp")
    approle = client.auth_approle(role_id, secret_id["data"]["secret_id"])
    logger.debug("approle auth information=%s", approle)
    appclient = hvac.Client(args.vault, approle["auth"]["client_token"])
    res = appclient.write("kv-v1/aci/bootcamp", ACI_USERNAME="admin", ACI_PASSWORD="C1sco12345")
    data = appclient.read("kv-v1/aci/bootcamp")
    logger.debug("data=%s", data["data"])
    logger.info("vault_client_token=%s", approle["auth"]["client_token"])
    logger.info("vault_mount_path=%s", "kv-v1/aci/bootcamp")


