Quectel Modem Remote AT Command Support
=======================================

This repo was originally just for the ETH+AT command client for Quectel modems. I never got it working right for all platforms, and I wanted something cleaner anyways.. so I build a daemon that just lets you telnet to port 5000 on the modem and do whatever you want. However, both options are still available.

* Original ETH+AT Python client: [https://github.com/natecarlson/quectel-rgmii-at-command-client/tree/main/quectel_eth_at_client](https://github.com/natecarlson/quectel-rgmii-at-command-client/tree/main/quectel_eth_at_client)
* MicroPython-based daemon (note, requires adb): [https://github.com/natecarlson/quectel-rgmii-at-command-client/tree/main/at_telnet_daemon](https://github.com/natecarlson/quectel-rgmii-at-command-client/tree/main/at_telnet_daemon)
