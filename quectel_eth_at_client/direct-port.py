import socket
import time

SERVER_IP = "192.168.226.1"
SERVER_PORT = 1555
BUFFER_SIZE = 2048 * 4

def ql_rgmii_manager_server_fd_state(n):
    if n == -1 and (errno == EAGAIN or errno == EWOULDBLOCK):
        return 1
    if n < 0 and (errno == EINTR or errno == EINPROGRESS):
        return 2
    else:
        return 0

def main(argv):
    buffer_send = bytearray(BUFFER_SIZE)
    buffer_recv = bytearray(BUFFER_SIZE)
    buffer_temp = bytearray(BUFFER_SIZE)
    rv = 0
    count = 0
    length = 0
    i = 0
    datap = None

    if len(argv) == 2:
        if BUFFER_SIZE - 3 - 2 <= len(argv[1]):
            return 0
        buffer_send[3:3+len(argv[1])] = argv[1].encode()
        buffer_send[3+len(argv[1]):3+len(argv[1])+2] = b"\r\n"
    elif len(argv) == 1:
        buffer_send[3:] = b"at\r\n"
    else:
        return 0

    buffer_send[0] = 0xa4
    buffer_send[1] = (len(buffer_send[3:]) >> 8) & 0xff
    buffer_send[2] = len(buffer_send[3:]) & 0xff

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.bind(("", 0))

    server_addr = (SERVER_IP, SERVER_PORT)

    client_socket.setblocking(False)

    print(f"RGMII-AT Client Up => {SERVER_IP}:{SERVER_PORT}")
    while True:
        try:
            client_socket.connect(server_addr)
            break
        except Exception as e:
            print(f"Can Not Connect To => {SERVER_IP}:{SERVER_PORT}")
            time.sleep(2)

    if True:
        rv = client_socket.send(buffer_send[:3+len(buffer_send[3:])])
        print("\n\nsend:\n\n====================================> send all:", rv)
        print("==> length=", len(buffer_send[3:]), " head=0x%02x" % buffer_send[0])
        print("\"" + buffer_send[3:].decode() + "\"")
        if rv != 3 + len(buffer_send[3:]):
            print("Send buf not complete")
            # return 0

    print("\n\nrecv:")
    while True:
        try:
            rv = client_socket.recv(BUFFER_SIZE)
            if len(rv) >= 3:
                print("\n\n====================================> recv all:", len(rv))

                datap = rv
                while True:
                    length = (datap[1] << 8) | (datap[2] & 0xff)
                    buffer_temp[:length] = datap[3:3+length]

                    print("==> length=", length, " head=0x%02x" % datap[0])
                    print("\"" + buffer_temp[:length].decode() + "\"")
                    for i in range(length):
                        # print("0x%02x " % buffer_temp[i], end="")
                        pass
                    print()

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

        if count == 300:
            break

    print()
    client_socket.close()
    return 0

if __name__ == "__main__":
    import sys
    main(sys.argv)
