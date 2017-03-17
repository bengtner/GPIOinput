GPIO Input read daemon

This script reads GPIO input pins and updates corresponding virtual switches in Domoticz

Each input must have a corresponding virtual switch defined in Domoticz. See Domoticz Wiki how to do this. The switch type must be On/Off'. 'Contact' doesn't work.
The switch - input pin mapping is done by adding the following keyword in the switch description field:
 
%pin=<n>      where n should be replaced by the corresponding BCM pin number.

Example:
%pin=17
 
 
Various option can be set by command line parameters.

python GPIOinput.py -h

will explain the options.


I have also included a service definition file to install the script as a systemd service, which means it starts up and runs as a daemon at boot. Execution is also monitored and daemon is restarted if it fails for any reason. 

Edit GPIOinput.service for your choice of command line options, update the directory to where GPIOinput.py resides, and change the user name. Copy 
GPIOinput.service to /etc/systemd/system. Set permissions like other files in this directory.  Finally, install by

sudo systemctl daemon-reload
sudo systemctl enable GPIOinput
sudo systemctl start GPIOinput

You can check status by:

sudo systemctl status GPIOinput

This is a very simple python daemon that interacts with Domoticz through Domoticz JSON API.
