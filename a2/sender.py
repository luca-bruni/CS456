from socket import *
import sys
from packet import *
import threading

# Input variables to be set in parse_arguments(), read-in through command line arguments
emulator_address = ''
emulator_forward_port = 0
senders_receiving_port = 0
timeout = 0
file_name = ''

# Parses command line arguments and ensuring valid input before executing parts of the Sender program
def parse_arguments():
    global emulator_address
    global emulator_forward_port
    global senders_receiving_port
    global timeout
    global file_name
    
    # Check if incorrect # of arguments, print usage statements if so 
    if len(sys.argv) != 6:
        print_usage()
        quit()

    # Attempt to read command line input into their respective expected variables, throw specific exception if bad input
    try:
        emulator_address = str(sys.argv[1])
    except:
        print("Error: <emulator's network address> must be of hostname or IP format.")
    try:
        emulator_forward_port = int(sys.argv[2])
    except:
        print("Error: <emulator's receiving UDP port number in the forward (sender) direction> must be a valid port #.")
    try:
        senders_receiving_port = int(sys.argv[3])
    except:
        print("Error: <sender's receiving UDP port number> must be a valid port #.")
    try:
        timeout = int(sys.argv[4])
    except:
        print("Error: <timeout in milliseconds> must be a positive integer.")
    try:
        file_name = str(sys.argv[5])
    except:
        print("Error: <input file> must be a valid file name.")

# Tells the user how to use the Sender program
def print_usage():
     print("Usage: \'py sender.py <emulator's network address>")
     print("<emulator's receiving UDP port number in the forward (sender) direction>")
     print("<sender's receiving UDP port number>")
     print("<timeout in milliseconds>")
     print("<input file>\'")

# Sends packet to the emulator's network address at the <emulator's receiving UDP port number in the forward (sender) direction>
def send_packet(packet):
    global timestamp
    sender_socket.sendto(packet.encode(), (emulator_address, emulator_forward_port))
    # Log packet's seqnum in seqnum.log after sending packet
    seqnum_file.write("t=" + str(timestamp) + " " + str(packet.seqnum) + "\n")
    # Increment timestamp at packet send; handles packet send in handle_timeout() as well
    timestamp += 1

# Handles timeouts using the Timer as per assignment 2 specifications.
def handle_timeout():
    global window_size

    lock.acquire()

    if last_ACK_received + 1 >= len(packets):
        lock.release()
        return

    window_size = 1
    N_file.write("t=" + str(timestamp) + " " + str(window_size) + "\n")
    send_packet(packets[last_ACK_received + 1])
    start_timer()

    lock.release()


# Intializes and starts Timer of <timeout in milliseconds> parameter in seconds. 
#   When Timer runs out, handle_timeout() is called.
def start_timer():
    timer = threading.Timer(timeout_seconds, handle_timeout)
    timer.start()

# ACK_receiver is a thread that runs and listens for ACKs sent by the Receiver. 
#   ACK_receiver notifies the main program when an ACK has been received, and
#   updates fields of the protocol as specified by assignment 2.
class ACK_receiver (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # Name thread for debugging purposes
        self.name = "ACK Receiver Thread"

    def run(self):
        global last_ACK_received
        global window_size
        global timestamp
        global ack_file

        # Bind receiving socket
        ACK_receiving_socket = socket(AF_INET, SOCK_DGRAM)
        ACK_receiving_socket.bind(('', senders_receiving_port))

        while (True):
            # Receive encoded packet, decode using method in packet.py of constructing new packet with encoded one
            ACK_packet_enc, addr = ACK_receiving_socket.recvfrom(packet_size_extras)
            ACK_packet = Packet(ACK_packet_enc)

            lock.acquire()

            # If packet received from Receiver is EOT
            if ACK_packet.typ == 2:
                # Log EOT in ack.log and increment timestamp, break since program has completed under assumptions
                ack_file.write("t=" + str(timestamp) + " EOT\n")
                timestamp += 1
                lock.release()
                break

            ACK_seqnum = ACK_packet.seqnum

            # Log ACK packet's seqnum in ack.log
            ack_file.write("t=" + str(timestamp) + " " + str(ACK_seqnum) + "\n")

            # For the received ACK, compute the index of the ACK'd packet in the packets array, use this to check if in outstanding_packets
            potential_ACK_received = last_ACK_received + (ACK_seqnum - (last_ACK_received % 32)) % 32

            if potential_ACK_received in outstanding_packets:
                timer.cancel()
                last_ACK_received = potential_ACK_received

                # Pop off all packets with lesser indices in outstanding_packets by cumulative ACKnowledgements.
                #   This can only be done under the assumption that index numbers are increasing in the array.
                while (len(outstanding_packets) > 0 and outstanding_packets[0] <= last_ACK_received):
                    outstanding_packets.pop(0)

                # Start the timer if there is are outstanding_packets remaining after the purging as per assignment 2 specification
                if len(outstanding_packets) > 0:
                    start_timer()
                # Ensure window_size does not exceed 10
                if window_size < max_window_size:
                    window_size += 1
                    # Log window_size in N.log and do not increment timestamp as per assignment specification
                    N_file.write("t=" + str(timestamp) + " " + str(window_size) + "\n")
                cv.notify()

            timestamp += 1
            lock.release()
        ACK_receiving_socket.close()

# Constants
packet_size = 500
packet_size_extras = 512
max_window_size = 10
N_file_name = 'N.log'
ack_file_name = 'ack.log'
seqnum_file_name = 'seqnum.log'

# Other variables
sender_socket = socket(AF_INET, SOCK_DGRAM)
lock = threading.Lock()
cv = threading.Condition(lock)
packets = []
outstanding_packets = []
window_size = 1
current_packet_index = 0
last_ACK_received = -1
timestamp = 0

# Main Program

# Handle command line input
parse_arguments()

# Create or open and overwrite log files with empty string, reopen files with append permission
N_file = open(N_file_name, "w")
N_file.write('')
N_file.close()
ack_file = open(ack_file_name, "w")
ack_file.write('')
ack_file.close()
seqnum_file = open(seqnum_file_name, "w")
seqnum_file.write('')
seqnum_file.close()

N_file = open(N_file_name, "a")
ack_file = open(ack_file_name, "a")
seqnum_file = open(seqnum_file_name, "a")

# Handle edge cases

# Log initial window_size in N.log and increment timestamp to kick off the program
N_file.write("t=" + str(timestamp) + " " + str(window_size) + "\n")
timestamp += 1

# Initialize Timer
timeout_seconds = timeout / 1000.0
timer = threading.Timer(timeout_seconds, handle_timeout)

# Open input file, separate into packets, store packets into packets array, close file
file = open(file_name, "r")
file_packet = file.read(packet_size)
sequence_number = 0
while (len(file_packet) != 0):
    packet = Packet(1, sequence_number % 32, len(file_packet), file_packet)
    packets.append(packet)
    sequence_number += 1
    file_packet = file.read(packet_size)
file.close()

# Initialize and start ACK_receiver to be running as the main Sender program executes
ACK_rcvr = ACK_receiver()
ACK_rcvr.start()

# Send data packets to the Receiver, waits when window is full. 
#   Will be notified when ACK has been received
while (last_ACK_received < len(packets) - 1):
    lock.acquire()
    # While requirements are satisfied to send a packet
    while (len(outstanding_packets) < window_size and current_packet_index < len(packets)):
        send_packet(packets[current_packet_index])
        
        # Start timer if there are no outstanding packets
        if len(outstanding_packets) == 0:
            start_timer()

        # Add the just-sent packet's index to outstanding_packets array
        outstanding_packets.append(current_packet_index)
        current_packet_index += 1
    # Wait for the ACK_receiver to notify main program that it has received an ACK from Receiver
    cv.wait()
    lock.release()

# End of sending data packets, create and send EOT packet to Receiver
EOT_packet = Packet(2, sequence_number % 32, 0, '')
send_packet(EOT_packet)

ACK_rcvr.join()

sender_socket.close()

# Close all the log files to save the logs
N_file.close()
ack_file.close()
seqnum_file.close()
