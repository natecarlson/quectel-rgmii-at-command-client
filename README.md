> :warning: **This doesn't work yet**: I don't have a RM520N in one of these adapters yet, and it doesn't work yet. LOL.

# quectel-rgmii-at-command-client
This is a Python script to send AT commands to Quectel RM5xx modems that are connected via a RGMII Ethernet interface (aka a "RJ45 to M.2" or "Ethernet to M.2" adapter board). Their AT interface doesn't just accept plain AT commands, so this is trying to reimplement the protocol they give a (poor) example of in the reference C app.

Should work with any RM520/RM530 modems. Does not appear to work with RM500Q-GL, firmware RM500QGLABR13A02M4G. That modem opens the port, but doesn't seem to respond to anything. I have heard that it will work with RM502Q-AE's at least.

*VERY* little error checking; if something breaks, you can keep both pieces.

## Requirements:
Your modem should be installed in an M.2-to-ethernet sled, and the modem should already be configured through the USB port, and working properly. You will then need to enable the AT port:

* Use a terminal emulator to connect to the modem's USB port
* Run `AT+QETH="eth_at","enable"` to enable the AT port

## Usage
* Download the script
* Run the script like: `python quectel_rgmii_at_client.py --modem-ip=192.168.225.1 --modem-port=1555 --at-command=ATI` (run --help to see defaults.)
* It should print the output

If you are running a command that needs double-quotes, be sure to enclose the full command in single quotes.. IE:
`python3 quectel_rgmii_at_client.py --at-command='AT+QENG="servingcell"'`
