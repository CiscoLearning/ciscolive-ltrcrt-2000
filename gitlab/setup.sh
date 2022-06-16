#!/usr/bin/env bash

gitlab_host="http://198.18.1.11"
gitlab_user="root"
gitlab_password="C1sco12345"
gitlab_wait_time=45
devbox_user="developer"
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

printf "Generating SSH key for ${gitlab_user}..."
mkdir -p ~${devbox_user}/.ssh
output=$(/usr/bin/ssh-keygen -b 4096 -N "" -t rsa -f ~${devbox_user}/.ssh/id_rsa 2>&1)
chown -R ${devbox_user} ~${devbox_user}/.ssh
chmod 0700 ~${devbox_user}/.ssh
key=$(cat ~${devbox_user}/.ssh/id_rsa.pub)
if [ $? != 0 ]; then
    echo "FAIL!"
    echo "Result = ${output}"
else
    success
fi

printf "Setting default branch name..."
token=$(curl -s -X POST -H "Content-type: application/json" --data-raw "{\"grant_type\": \"password\", \"username\": \"${gitlab_user}\", \"password\": \"${gitlab_password}\"}" ${gitlab_host}/oauth/token | jq -r .access_token)
output=$(curl -s -X PUT -H "Authorization: Bearer ${token}" -H "Content-type: application/json" --data-raw "{\"default_branch_name\": \"main\"}" ${gitlab_host}/api/v4/application/settings)
if [ $? != 0 ]; then
    echo "FAIL!"
    echo "Result = ${output}"
else
    success
fi

printf "Adding SSH key for ${devbox_user} to GitLab user ${gitlab_user}..."
output=$(curl -s -X POST -H "Authorization: Bearer ${token}" -H "Content-type: application/json" --data-raw "{\"name\": \"Devbox\", \"key\": \"${key}\"}" ${gitlab_host}/api/v4/user/keys)
if [ $? != 0 ]; then
    echo "FAIL!"
    echo "Result = ${output}"
else
    success
fi

printf "Configuring external URL for GitLab..."
docker-compose exec gitlab /bin/bash -c "echo external_url \'${gitlab_host}\' >> /etc/gitlab/gitlab.rb"
docker-compose exec gitlab gitlab-ctl reconfigure >> gitlab_setup.log 2>&1
success

printf "Registering GitLab Runner, waiting ${gitlab_wait_time} second(s) for gitlab to become available..."
sleep ${gitlab_wait_time}
docker-compose exec runner1 gitlab-runner register >> gitlab_setup.log 2>&1
success
