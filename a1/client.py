import sys
from socket import *

# This function prints the usage requirements for client.py and exits the program should command line argument parsing fail
def print_usage():
        print('Usage: \'py client.py <server_address> <server_port> <req_code> <msg>\'.')
        print('<server_address> is the server\'s address in IP/hostname format.')
        print('<server_port> is the server\'s fixed port, an integer.')
        print('<req_code> is the required request code to connect with the server, an integer.')
        print('<msg> is the message you would like the server to reverse.')
        sys.exit()

# Function for initiating negotiation. Creates TCP connection with server.
# If reqCode matches that of server's intended reqCode, server will reply with a contact port.
# This function returns that port.
def tcp_request(serverAddress, serverPort, reqCode):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverAddress, serverPort))
    clientSocket.send(reqCode.encode())

    serverResponse = clientSocket.recv(1024)
    clientSocket.close()
    return int(serverResponse.decode())

# Function for initiating transaction. Initiates UDP connection with server, 
# The client sends a message string to the server, and the server replies with a reverse version of that message, stored in modifiedMsg.
# This function returns modifiedMsg.
def udp_request(serverAddress, msg, rPort):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.sendto(msg.encode(), (serverAddress, rPort))
    modifiedMsg, serverAddress = clientSocket.recvfrom(2048)
    clientSocket.close()
    return modifiedMsg

# The following lines store the required arguments for the client into variables for later usage
try:
    serverAddress = str(sys.argv[1])
    serverPort = int(sys.argv[2])
    reqCode = sys.argv[3]
    msg = str(sys.argv[4])
except:
    print_usage()

# Initiates negotiation, stores result into rPort; gracefully exits if reqCode is incorrect
try:
    rPort = tcp_request(serverAddress, serverPort, reqCode)
except:
    print('Server not running or reqCode incorrect.')
    sys.exit()

# Initiates transaction, stores result into modifiedMsg
modifiedMsg = udp_request(serverAddress, msg, rPort)

# Prints modifiedMsg, the reversed version of msg retrieved from the server as specified by assignment 1
print(modifiedMsg.decode())
