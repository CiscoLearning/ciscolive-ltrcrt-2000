# LTRCRT-2000

## Steps Prior to Starting the Lab

1. Install the remote extension pack for Visual Studio Code (<https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack>)
2. Connect to the remote developer@198.18.1.11
3. Open a Terminal in VSCode (which should be on the Devbox)
4. Clone this repo:

```sh
git clone https://github.com/CiscoLearning/ciscolive-ltrcrt-2000
```

## Starting the Lab

To prepare the lab environment, call the `start` script with the desired lab from a Terminal pane within VSCode. e.g.:

```sh
sh start
```

Then, change directory to `~/ciscolive-lrtcrt-2000` and run `code -a .` to open that directory within the VSCode window.

## Running the Lab At Home

If you have your own copy of Cisco Modeling Labs, you can run this lab at home with some minor changes to the code.  First, modify `init/virlrc` and change the IP address of the CML server and its credentials to match your local copy.

Next, edit `helper-files/Devbox.yaml` and look for "198.18".  Change the Devbox IP and its default gateway to match your network.  The Devbox uses 1.1.1.1 for DNS, which you may also want to change around the same location in this file.  Finally, in this same file, search for "bridge1".  This is the bridge used by the **dCloud** external connector.  You likely want to change this to "bridge0" to be the default CML bridge.  This will allow the Devbox to use the IP address you set in this file.

With those changes made, you can run the `start` script as mentioned above.

When working through the lab guide, be sure to replace "198.18.1.11" with the IP address you chose for the Devbox above.  Replace "198.18.134.1" with the IP of your CML server.
