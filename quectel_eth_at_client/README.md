# quectel-rgmii-at-command-client

**NOTE**: This is a work-in-progress that I never got fully working. I prefer the [AT Telnet Daemon](https://github.com/natecarlson/quectel-rgmii-at-command-client/tree/main/at_telnet_daemon) instead. It does require adb to install, but it provides a full telnet interface to the modem, and is much more reliable. I may continue to work on this at some point, but I'm not sure. Pull requests always welcome!

This is a Python script to send AT commands to Quectel RM5xx modems that are connected via a RGMII Ethernet interface (aka a "RJ45 to M.2" or "Ethernet to M.2" adapter board). Their AT interface doesn't just accept plain AT commands, so this is trying to reimplement the protocol they give a (poor) example of in the reference C app.

Should work with any RM520/RM530 modems. Also _sometimes_ works with my RM500Q.

*VERY* little error checking; if something breaks, you can keep both pieces.

If you're interested in more general documentation on these ethernet sleds, I've posted some at:
https://github.com/natecarlson/quectel-rgmii-configuration-notes

If you would like to support my work to provide public resources for these Quectel modems, and help me purchase additional hardware for more hacking (without having to take one of my active modems down), you can click the link below. To be clear, please only do this if you actually want to; any future work I do will always be publicly available, and I'm not going to gate anything behind this! Well, unless you want remote support to set something up, I suppose.

<a href="https://www.buymeacoffee.com/natecarlson" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

## Requirements

Your modem should be installed in an M.2-to-ethernet sled, and the modem should already be configured through the USB port, and working properly. You will then need to enable the AT port:

* Use a terminal emulator to connect to the modem's USB port
* Run `AT+QETH="eth_at","enable"` to enable the AT port

## Usage

* Download the script
* Run the script like: `python quectel_rgmii_at_client.py --modem-ip=192.168.225.1 --modem-port=1555 --at-command=ATI` (run --help to see defaults.)
* It should print the output

If you are running a command that needs double-quotes, be sure to enclose the full command in single quotes.. IE:
`python3 quectel_rgmii_at_client.py --at-command='AT+QENG="servingcell"'`
