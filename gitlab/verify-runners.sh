#!/usr/bin/env bash

gitlab_host="http://devbox"
gitlab_user="root"
gitlab_password="C1sco12345"

personal_access_token=""

# create gitlab personal access token
# https://gist.github.com/michaellihs/5ef5e8dbf48e63e2172a573f7b32c638
create_gitlab_token() {
    # 1. curl for the login page to get a session cookie and the sources with the auth tokens
    body_header=$(curl -k -c cookies.txt -i "${gitlab_host}/users/sign_in" -s)

    # grep the auth token for the user login for
    #   not sure whether another token on the page will work, too - there are 3 of them
    csrf_token=$(echo "$body_header" | grep -o 'name="authenticity_token" value="[^"]*"' | head -n1 | sed 's/.*value="\([^"]*\)".*/\1/')
    # echo "$csrf_token"

    # 2. send login credentials with curl, using cookies and token from previous request
    curl -k -b cookies.txt -c cookies.txt -i "${gitlab_host}/users/sign_in" \
        --data-urlencode "user[login]=${gitlab_user}" \
        --data-urlencode "user[password]=${gitlab_password}" \
        --data-urlencode "authenticity_token=${csrf_token}"

    # 3. send curl GET request to personal access token page to get auth token
    body_header=$(curl -k -H 'user-agent: curl' -b cookies.txt -i "${gitlab_host}/-/user_settings/personal_access_tokens" -s)
    # echo "$body_header"
    csrf_token=$(echo "$body_header" | grep -o 'name="csrf-token" content="[^"]*"' | head -n1 | sed 's/.*content="\([^"]*\)".*/\1/')
    # echo "$csrf_token"

    # 4. curl POST request to send the "generate personal access token form"
    #      the response will be a redirect, so we have to follow using `-L`
    body_header=$(curl -k -L -b cookies.txt "${gitlab_host}/-/user_settings/personal_access_tokens" \
        --request POST \
        --header "Content-Type: application/x-www-form-urlencoded" \
        --header "X-CSRF-Token: ${csrf_token}" \
        --data-urlencode "authenticity_token=${csrf_token}" \
        --data-urlencode "personal_access_token[name]=golab-generated" \
        --data-urlencode "personal_access_token[expires_at]=" \
        --data-urlencode "personal_access_token[scopes][]=api")

    # 5. Scrape the personal access token from the response HTML
    personal_access_token=$(echo "$body_header" | grep -o '"new_token":"[^"]*"' | sed 's/"new_token":"\([^"]*\)"/\1/')
}

create_gitlab_token &>/dev/null
curl -L --header "PRIVATE-TOKEN: $personal_access_token" "$gitlab_host/api/v4/runners/all"
echo
