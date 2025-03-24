# LTRCRT-2000

## Initializing the lab environment

> [!IMPORTANT]
>
> The bootstrap and initial setup steps are **not** needed during the actual CiscoLive event.
> If you are attending the event, use the lab guide.

### Bootstrap

To bootstrap the environment, import [Devbox.yaml](https://github.com/rschmied/ciscolive-ltrcrt-2000/blob/main/helper-files/Devbox.yaml) into your CML instance, then start the imported lab and wait for the *Devbox* to install all the packages and updates. This will take a couple of minutes and it will be ready after a final reboot.

### Initial setup

The following steps will complete the installation of the *Devbox*:

1. Install the remote extension pack for Visual Studio Code (<https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack>)
2. Connect to the remote server *Devbox* using developer@198.18.1.11
3. Open a Terminal in VSCode
4. Clone this repo:

    ```sh
    git clone https://github.com/rschmied/ciscolive-ltrcrt-2000
    ```

5. Change into the cloned repository: `cd ciscolive-ltrcrt-2000`
6. Run the start script using `sh ./start`. This takes a while to complete.
7. Then, change directory to `~/cml-iac` and run `code -a .` to open that directory within the VSCode window

You should now be able to follow the instructions from the lab guide.

git checkout -b clus2025 --track origin/clus2025

## Running the lab at home

If you have your own copy of Cisco Modeling Labs, you can run this lab at home with some minor changes to the code.  First, clone this repo to your local machine.

Next, edit `helper-files/Devbox.yaml` and look for "198.18".  Change the *Devbox* IP and its default gateway to match your local network (this lab assumes the *Devbox* is connected to a bridge `ext-conn`).  The *Devbox* uses 1.1.1.1 for DNS, which you may also want to change around the same location in this file.  Finally, in this same file, search for "bridge1".  This is the bridge used by the **dCloud** external connector.  You likely want to change this to "bridge0" to be the default CML bridge.  This will allow the *Devbox* to use the IP address you set in this file.

> [!NOTE]
> It's recommended to use a static address as the embedded GitLab instance needs one!

With this file edited, import `Devbox.yaml` manually into your CML server and start the *Devbox* lab.  When the *Devbox* server is fully up, log into with credentials "developer" and password "C1sco12345".  Clone this same repo onto the *Devbox*.  Then, modify `init/virlrc` within this repo and change the IP address of the CML server and its credentials to match your local copy.

Next, edit `gitlab/setup.sh` and change the `gitlab_host` variable at the top of the file to match the public IP address of the *Devbox* on your local network.  Edit the `gitlab/docker-compose.yml` file and search for "198.18.1.11" in this file and change the instances to the public IP address of the *Devbox* on your local network.

With those changes made, you can run the `start` script as mentioned above.

> [!NOTE]
> Depending on the performance of your CML host, the default value of `gitlab_wait_time` of 45 seconds may be too short.  If you get a failure registering the GitLab runner, simply re-run `docker-compose exec runner1 gitlab-runner register` from within the `gitlab` directory.

When working through the lab guide, be sure to replace "198.18.1.11" with the IP address you chose for the *Devbox* above.  Replace "198.18.134.1" with the IP of your CML server.
