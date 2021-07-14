import sys
from socket import *

# This function parses arguments to the executable to ensure validity and correctness
def check_arguments():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print('Usage: \'py server.py <req_code>\', where <req_code> is an integer.')
        sys.exit()

# This function returns a random available port between 1025 and 65535
def get_available_port():
    temp_socket = socket(AF_INET, SOCK_STREAM)
    temp_socket.bind(('', 0))
    temp_socket.listen(1)
    rPort = temp_socket.getsockname()[1]
    temp_socket.close()
    return rPort

# This function responds to the client in the negotiation phase with the random port number if the reqCode matched
def tcp_reply(serverPort, reqCode):
    serverSocket = socket(AF_INET, SOCK_STREAM)

    # This try-except block ensures that the fixed port is not in use. If so, a new port is generated for the TCP connection
    try:
        serverSocket.bind(('', serverPort))
    except error as msg:
        serverPort = get_available_port()
        serverSocket.bind(('', serverPort))

    # Prints the fixed server port as per assignment 1 specification during negotiation phase
    print("SERVER_PORT=" + str(serverPort))

    serverSocket.listen(1)

    while True:
        connectionSocket, addr = serverSocket.accept()
        message = connectionSocket.recv(1024).decode()
        if (message == reqCode):
            rPort = get_available_port()
            connectionSocket.send(str(rPort).encode())
            connectionSocket.close()
            break
        
        connectionSocket.close()
    return rPort

# This function responds to the client in the transaction phase with the reversed version of the client's message to the random port
def udp_reply(rPort):
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', rPort))

    while True:
        message, clientAddress = serverSocket.recvfrom(2048)
        modifiedMessage = message.decode()[::-1]
        serverSocket.sendto(modifiedMessage.encode(), clientAddress)

# First, check if the command line arguments are valid and correct
check_arguments()

# serverPort is the fixed port, reqCode is the server-specified request code inputted via command line arguments
serverPort = 52500
reqCode = str(sys.argv[1])

# Replies to the client with the random port if reqCodes match; continues listening otherwise
rPort = tcp_reply(serverPort, reqCode)

# Replies to the client with the reversed version of client's message at rPort
udp_reply(rPort)
