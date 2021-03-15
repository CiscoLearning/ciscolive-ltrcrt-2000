#!/usr/bin/env bash

gitlab_host="http://10.10.20.50"
gitlab_user="root"
gitlab_password="C1sco12345"
gitlab_wait_time=45
vault_host="http://10.10.20.50:1234"
vault_backend_type="kv-v1"
# prints colored text
success () {
    COLOR="92m"; # green
    STARTCOLOR="\e[$COLOR";
    ENDCOLOR="\e[0m";
    printf "$STARTCOLOR%b$ENDCOLOR" "done\n";
}

echo ""
printf "Launching Gitlab CE and Vault..."
docker-compose up -d 2> gitlab_setup.log
success

printf "Waiting for Gitlab CE to become available..."

until $(curl --output /dev/null --silent --head --fail ${gitlab_host}); do
    printf '.'
    sleep 10
done
success

printf "Configuring external URL for GitLab..."
docker-compose exec gitlab /bin/bash -c "echo external_url \'${gitlab_host}\' >> /etc/gitlab/gitlab.rb"
docker-compose exec gitlab gitlab-ctl reconfigure 2>&1 >> gitlab_setup.log
success

printf "Registering GitLab Runner, waiting ${gitlab_wait_time} second(s) for gitlab to become available..."
sleep ${gitlab_wait_time}
docker-compose exec runner1 gitlab-runner register 2>&1 >> gitlab_setup.log
success

echo "Configuring Vault"
printf "Extracting Root Token..."
root_token=$(docker-compose logs vault | grep -oP 'Root Token: \K.*')
success

printf "Extracting Unseal Key..."
unseal_key=$(docker-compose logs vault | grep -oP 'Unseal Key: \K.*')
success

printf "Configuring Vault..."
pip install -r requirements.txt &>> gitlab_setup.log
python init.py --log DEBUG --vault "${vault_host}" --vault_token "${root_token}" --vault_keys "${unseal_key}" --vault_backend_type ${vault_backend_type} &>> gitlab_setup.log
success

client_token=$(cat gitlab_setup.log | grep -oP 'vault_client_token=\K.*')
mount_path=$(cat gitlab_setup.log | grep -oP 'vault_mount_path=\K.*')

printf """
Vault Client Token: ${client_token}
Vault Mount Path  : ${mount_path}

"""

printf """
Vault Client Token: ${client_token}
Vault Mount Path  : ${mount_path}

""" >> gitlab_setup.log



# printf "Creating user 'developer' ..."
# create_gitlab_token 2>&1 >> gitlab_setup.log
# curl -s --header "PRIVATE-TOKEN: $personal_access_token" -d "email=developer@lab.devnetsandbox.local&password=C1sco12345&username=developer&name=developer&skip_confirmation=true" "${gitlab_host}/api/v4/users" 2>&1 >> gitlab_setup.log
# success
