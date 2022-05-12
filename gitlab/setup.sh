#!/usr/bin/env bash

gitlab_host="http://198.18.1.11"
gitlab_user="root"
gitlab_password="C1sco12345"
gitlab_wait_time=45
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

printf "Setting default branch name..."
token=$(curl -s -X POST -H "Content-type: application/json" --data-raw "{\"grant_type\": \"password\", \"username\": \"${gitlab_user}\", \"password\": \"${gitlab_password}\"}" ${gitlab_host}/oauth/token | jq -r .access_token)
echo "Token in ${token}"
output=$(curl -s -X PUT -H "Authorization: Bearer ${token}" -H "Content-type: application/json" --data-raw "{\"default_branch_name\": \"main\"}" ${gitlab_host}/api/v4/application/settings)
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
