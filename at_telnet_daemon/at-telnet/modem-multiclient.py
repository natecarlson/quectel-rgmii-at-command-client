#!/usrdata/micropython/micropython

# Add the /usrdata/micropython directory to sys.path so we can find the external modules.
# TODO: Move external modules to lib?
# TODO: Recompile Micropython with a syspath set up for our use case.
import sys
# Remove the home directory from sys.path.
if "~/.micropython/lib" in sys.path:
    sys.path.remove("~/.micropython/lib")
sys.path.append("/usrdata/micropython")

import uos
import usocket as socket
import _thread as thread
import serial
import select
import traceback
import logging
import re
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s: %(levelname)s/%(msecs)ims] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# Globally define client_sockets and serialport. That way, we can access them from handle_output and make it a separate thread, so responses (and unsolicited responses) can come in while we're waiting for input.
global client_sockets, serialport
client_sockets = []
# We are referencing one of the two ports exposed by our socat command. The other one is /dev/ttyIN, and two running "cat" commands are keeping it sync'd with /dev/smd11.
serialport = serial.Serial("/dev/ttyOUT", baudrate=115200)

# This routine pulls data from the serial port and sends it to all connected clients.
def handle_output():
    while True:
        # Make data an empty bytes list
        data = b''

        try:
            while serialport.in_waiting > 0:
                data += serialport.read(1)
        except Exception as e:
            # This will keep trying.
            print(f"Exception reading data from serialport: {e}")
            traceback.print_exc()

        if data:
            logging.info(f"Got data from modem: {data}")
            for client_socket in client_sockets:
                client_socket.send(data)

# Start the server on the specified port, listen for clients, etc.
def start_at_server(port):

    # Server initialization stuff
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr_info = socket.getaddrinfo("0.0.0.0", port)
        addr = addr_info[0][4]
        server_socket.bind(addr)
        server_socket.listen(1)

        logging.info(f"AT Server listening on TCP port {port}")

        # Disable echo so user doesn't see a second copy of all their commands.
        serialport.write("ATE0\r\n")
        # time.sleep() segfaults?! ugh.
        uos.system("sleep 0.025s")
        # wait for an OK
        out=b''
        while serialport.in_waiting > 0:
            out += serialport.read(1)

        if "OK" not in str(out):
            logging.warning(f"Did not get expected OK when running ATE0. Result: {str(out)}")

    except Exception as e:
        logging.error("Error initializing server: {e}")
        traceback.print_exc()
        raise

    # Start the output handler in its own thread
    try:
        thread.start_new_thread(handle_output, ())
    except Exception as e:
        print("Error with output handler:", e)
        traceback.print_exc()
        raise

    # Set up a select.poll object to listen for input from the server socket and all client sockets.
    # Logic mostly from https://pymotw.com/2/select/
    try:
        poll_obj = select.poll()
        poll_obj.register(server_socket, select.POLLIN)

        # Register the server socket in the fd_to_socket dict; this will also be used to register the rest of the clients.
        fd_to_socket = { server_socket.fileno(): server_socket,
                       }

        while True:
            events = poll_obj.poll()

            for fd, flag in events:
                logging.debug(f"Pool loop event. fd: {fd} flag: {flag} fd_to_socket.keys(): {fd_to_socket.keys()}")

                # Check if the client already exists in the fd_to_socket dict.
                if fd.fileno() in fd_to_socket.keys():
                    s = fd_to_socket[fd.fileno()]
                    logging.debug("Event matches existing socket.")
                else:
                    s = fd
                    logging.debug(f"Event doesn't match existing socket. fd: {fd} fd_to_socket: {fd_to_socket}")

                # If the flag is POLLIN, then we have data to process.
                if flag & (select.POLLIN):
                    # If the server socket is ready to read, then we have a new client connection.
                    if s is server_socket:
                        # Accept the connection.
                        client_socket, client_address = s.accept()
                        # TODO: This gives a garbled IP. Figure it out.
                        #client_address_translated = socket.inet_ntop(socket.AF_INET, client_address)
                        logging.info(f"New connection")

                        # Set the client socket to non-blocking, and add it to the list of client sockets.
                        # TODO: trim down to just storing one copy of the client sockets..
                        client_socket.setblocking(0)
                        fd_to_socket[ client_socket.fileno() ] = client_socket
                        client_sockets.append(client_socket)
                        poll_obj.register(client_socket, select.POLLIN)

                        # Send a good 'ol hello message to the client.
                        client_socket.send("** Welcome to the AT server!\r\n".encode())
                        client_socket.send("** Note that your commands are interleaved with any other connected clients,\r\n** so responses may appear out of order.\r\n".encode())
                        client_socket.send("** \r\n".encode())
                        client_socket.send("** You may also receive unsolicited responses (URC's) depending on the\r\n** modem configuration.\r\n".encode())
                        client_socket.send("** \r\n".encode())
                        client_socket.send("** Echo is off (ATE0); if you change it you'll see what you've typed both\r\n** locally and echo'd back.\r\n".encode())
                        client_socket.send("** \r\n".encode())
                        client_socket.send("** I have tested this with telnet.netkit and netcat on Linux. If your client\r\n** doesn't work,\r\n** please open an issue at:\r\n** https://github.com/natecarlson/quectel-rgmii-at-command-client/ **\r\n".encode())
                        client_socket.send("**\r\n".encode())
                        client_socket.send("** If you would like to support further development, you can at:\r\n** https://www.buymeacoffee.com/natecarlson **\r\n".encode())
                        client_socket.send("\r\n".encode())


                    # Otherwise, we have data from a client socket.
                    else:
                        data = s.recv(1024)
                        logging.info(f"Got data from client: {data}")
                        if data:
                            # Ensure it ends with \r\n
                            if not data.endswith("\r\n"):
                                # Just stripping \n for now; add others in the future if needed.
                                data = re.sub(b"\n$", "", data) + "\r\n"
                                logging.info(f"Modified client data to end with \\r\\n: {data}")

                            # Good client data; write out to the serial port.
                            serialport.write(data)
                            # Write out out to the rest of the clients too
                            for fd in fd_to_socket.keys():
                                if fd != server_socket.fileno() and fd != s.fileno():
                                    logging.debug(f"Writing data to other connected client: {data}")
                                    try:
                                        fd_to_socket[fd].send(data)
                                    except Exception as e:
                                        logging.info(f"Failed to write data to an additional client. Ignorning. Result: {e}")
                                        pass
                        else:
                            # Client disconnected
                            print("Client disconnected")
                            client_sockets.remove(s)
                            poll_obj.unregister(s)
                            del fd_to_socket[s.fileno()]
                            s.close()

                # Not sure if this can happen. But , if it does, we should close the socket.
                elif flag & select.POLLERR:
                    logging.warn(f"Strange connection issue with a client; closing.")
                    # Stop listening for input on the connection
                    poll_obj.unregister(s)
                    client_sockets.remove(s)
                    del fd_to_socket[s.fileno()]
                    s.close()

            # TODO: I don't believe we need this here, since the output is now handled in its own thread.
            #uos.system("sleep 0.025s")

    except Exception as e:
        print("Error after server initialization:", e)
        serialport.write("ATE1\r\n")
        traceback.print_exc()
        # I believe this will drop out of the while loop, so we'll close the sockets and exit.

    # Close client sockets and server socket
    for client_socket in client_sockets:
        client_socket.close()

    server_socket.close()

# TODO: By using the dict, we shouldn't need this code. Clean it up.
#def fd_to_socket(fd, client_sockets):
#    for client_socket in client_sockets:
#        if client_socket.fileno() == fd:
#            return client_socket
#    return None

# App startup. TODO: Make the port configurable.
if __name__ == "__main__":
    port = 5000
    start_at_server(port)
