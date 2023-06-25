#!/usr/bin/env python3

import socket
import time
import errno
from errno import EAGAIN, EWOULDBLOCK, EINPROGRESS, EINTR
import argparse

"""
Client for Quectel's QETH ETH_AT port on modems acting as a PCIe master with an ethernet port

This is a modified version of a direct ChatGPT port of RGMII_AT_Client.c to python. If the socket
communication can be simplified that would be awesome!

Basic packet format, both sending and receiving:
[identifier byte][two bytes for length][content][\r\n]

For sending packets, it appears the identifier byte needs to be 0xa4.

When receiving packets, it appears that the modem sends:
0xe0 with the RGMII_ATC_READY packet
0xa0 with the actual command output (both printing the command again, and the response.)

The --debug flag will print the parsing of the packets along with the contents.. IE:

    ====================================> recv all: 113
    ==> length= 110  head=0xa0

    +QENG: "servingcell","NOCONN","NR5G-SA","FDD",313,340,03865B04C,583,5B01,401050,70,4,-110,-14,11,0,-

    OK

The total length is 113 including the three header bytes, the length bytes are 110, and the initial byte is 0xa0.

"""

BUFFER_SIZE = 2048 * 4

def ql_rgmii_manager_server_fd_state(n):
    if n == -1 and (errno == EAGAIN or errno == EWOULDBLOCK):
        return 1
    if n < 0 and (errno == EINTR or errno == EINPROGRESS):
        return 2
    else:
        return 0

def main(args):
    SERVER_IP = args.modem_ip
    SERVER_PORT = args.modem_port
    DEBUG = args.debug

    buffer_send = bytearray(BUFFER_SIZE)
    buffer_recv = bytearray(BUFFER_SIZE)
    buffer_temp = bytearray(BUFFER_SIZE)
    rv = 0
    count = 0
    length = 0
    i = 0
    datap = None

    # If the buffer size is too small for the command, return?
    if BUFFER_SIZE - 3 - 2 <= len(args.at_command):
        return 0
    
    # Add the AT command plus \r\n to the send buffer starting at the fourth byte
    buffer_send[3:3+len(args.at_command)] = args.at_command.encode()
    buffer_send[3+len(args.at_command):3+len(args.at_command)+2] = b"\r\n"

    # First byte is always 0xa4
    buffer_send[0] = 0xa4

    # Second and third byte are the upper and lower bits of the full length of the command
    buffer_send[1] = (len(buffer_send[3:]) >> 8) & 0xff
    buffer_send[2] = len(buffer_send[3:]) & 0xff


    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #client_socket.bind(("", 0))

    server_addr = (SERVER_IP, SERVER_PORT)

    client_socket.setblocking(False)

    if DEBUG:
        print(f"RGMII-AT Client Up => {SERVER_IP}:{SERVER_PORT}")
    while True:
        try:
            client_socket.connect(server_addr)
            break
        except BlockingIOError as e:
            # This usually happens?
            pass
        except Exception as e:
            print(f"Can Not Connect To => {SERVER_IP}:{SERVER_PORT}")
            print(e)
            time.sleep(2)

    if True:
        rv = client_socket.send(buffer_send[:3+len(buffer_send[3:])])
        if DEBUG:
            print("\n\nsend:\n\n====================================> send all:", rv)
            print("==> length=", len(buffer_send[3:]), " head=0x%02x" % buffer_send[0])
        #print("SENDING: " + "\"" + buffer_send[3:].decode() + "\"")
        print("SENDING: " + buffer_send[3:].decode())
        if rv != 3 + len(buffer_send[3:]):
            print("Send buf not complete")
            # return 0

    print("\nReceived:")
    while True:
        try:
            rv = client_socket.recv(BUFFER_SIZE)
            if len(rv) >= 3:

                datap = rv
                while True:
                    length = (datap[1] << 8) | (datap[2] & 0xff)
                    buffer_temp[:length] = datap[3:3+length]

                    startbyte = "0x%02x" % datap[0]

                    # The 'RGMII_ATC_READY is delivered with a start byte of 0xe0. It's there on every request,
                    # so we don't need to print this. Might be good to check for it to validate that the protocol
                    # is working properly, though. So, DEBUG will print it.
                    if (DEBUG or not int(startbyte, 16) == 0xe0):
                        # Headers if DEBUG..
                        if DEBUG:
                            print("\n\n====================================> recv all:", len(datap))
                            print("==> length=", length, " head=0x%02x" % datap[0])
                        
                        print(buffer_temp[:length].decode())

                    rv = rv[length+3:]
                    if len(rv) > 0:
                        datap = rv
                    if len(rv) < 0:
                        print("client_socket recv not complete")

                    if len(rv) <= 0:
                        break

                buffer_recv[:]
            elif len(rv) > 0:
                print("client_socket recv error internal")
                break
            else:
                if not ql_rgmii_manager_server_fd_state(len(rv)):
                    print("client_socket recv error")
                    break
        except BlockingIOError:
            pass

        count += 1
        time.sleep(10 / 1000)

        # This is kind of a lame way to do it. Just iterates X times then bombs.
        # TODO: Watch how long it's been since the last response, and kill it more quickly.
        if count == 1000:
            break

    print()
    client_socket.close()
    return 0

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Execute AT commands over ethernet with a Quectel RM5xx modem")
    argparser.add_argument(
        "--modem-ip",
        type=str,
        default="192.168.225.1",
        required=False,
        help="Modem IP Address",
        dest="modem_ip",
    )
    argparser.add_argument(
        "--modem-port",
        type=int,
        default=1555,
        required=False,
        help="Modem Port",
        dest="modem_port",
    )
    argparser.add_argument(
        "--at-command",
        type=str,
        default="ATI",
        required=False,
        help="AT Command to execute",
        dest="at_command",
    )
    argparser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Print additional protocol debugging information",
    )

    args = argparser.parse_args()

    main(args=args)
