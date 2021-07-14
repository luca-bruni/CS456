from socket import *
import sys
from packet import *

# Input variables to be set in parse_arguments(), read-in through command line arguments. Set to default values as globals variables.
emulator_address = ''
emulator_backward_port = 0
receivers_receiving_port = 0
output_file_name = ''

# Parses command line arguments and ensuring valid input before executing parts of the Receiver program
def parse_arguments():
    global emulator_address
    global emulator_backward_port
    global receivers_receiving_port
    global output_file_name
    
    # Check if incorrect # of arguments, print usage statements if so
    if len(sys.argv) != 5:
        print_usage()
        quit()

    # Attempt to read command line input into their respective expected variables, throw specific exception if bad input
    try:
        emulator_address = str(sys.argv[1])
    except:
        print("Error: <emulator's network address> must be of hostname or IP format.")
    try:
        emulator_backward_port = int(sys.argv[2])
    except:
        print("Error: <emulator's receiving UDP port number in the backward (receiver) direction> must be a valid port #.")
    try:
        receivers_receiving_port = int(sys.argv[3])
    except:
        print("Error: <receiver's receiving UDP port number> must be a valid port #.")
    try:
        output_file_name = str(sys.argv[4])
    except:
        print("Error: <output file> must be a valid file name.")

# Tells the user how to use the Receiver program
def print_usage():
     print("Usage: \'py receiver.py <emulator's network address>")
     print("<emulator's receiving UDP port number in the backward (receiver) direction>")
     print("<receiver's receiving UDP port number>")
     print("<output file>\'")

# Sends packet to the emulator's network address at the <emulator's receiving UDP port number in the backward (receiver) direction>
def send_packet(packet):
    receiver_socket.sendto(packet.encode(), (emulator_address, emulator_backward_port))

# Constants
packet_size_extras = 512
arrival_file_name = 'arrival.log'

# Other variables
receiver_socket = socket(AF_INET, SOCK_DGRAM)
expected_seqnum = 0
buffer = [None] * 32

# Main Program

# Handle command line arguments
parse_arguments()

# Create or open and overwrite arrival.log file with empty string, reopen file with append permission
arrival_file = open(arrival_file_name, "w")
arrival_file.write('')
arrival_file.close()

arrival_file = open(arrival_file_name, "a")

# Bind socket once command line input has the proper address/port
receiver_socket.bind(('', receivers_receiving_port))

# Opens output file with 'write' permission to overwrite potential existing contents
file = open(output_file_name, "w")
file.write('')
file.close()

file = open(output_file_name, "a")

while (True):
    sender_packet_enc, addr = receiver_socket.recvfrom(packet_size_extras)
    sender_packet = Packet(sender_packet_enc)
    current_seqnum = sender_packet.seqnum

    # Log arrived packet's seqnum in arrival.log
    arrival_file.write(str(current_seqnum) + "\n")

    if current_seqnum == expected_seqnum:
        # If received EOT packet from sender, reply with EOT packet and exit the program
        if sender_packet.typ == 2:
            EOT_packet = Packet(2, current_seqnum % 32, 0, '')
            # Log EOT after arrived EOT packet received in arrival.log
            arrival_file.write("EOT\n")
            send_packet(EOT_packet)
            # Close files and sockets
            file.close()
            arrival_file.close()
            receiver_socket.close()
            quit()
        else:
            # Overwrite the file, then open with 'append' permission in order to append packet output instead of overwriting each time
            file.write(sender_packet.data)

            # Set buffer at expected sequence number to None
            buffer[expected_seqnum] = None

            while (True):
                # Increment expected sequence number, handle rollover at 32
                expected_seqnum = (expected_seqnum + 1) % 32

                # Repeat steps of checking buffer at next sequence number, writing potential packet's data to output file and setting that buffer position to None
                if buffer[expected_seqnum] is not None:
                    next_packet = buffer[expected_seqnum]
                    buffer[expected_seqnum] = None
                    file.write(next_packet.data)
                # Send ACK as per cumulative acknowledgement guidelines
                else:
                    ACK_packet = Packet(0, (expected_seqnum - 1) % 32, 0, '')
                    send_packet(ACK_packet)
                    break
    else:
        # If packet does not have expected sequence number but is within the next 10 sequence numbers, set buffer at that position to the sender packet
        if (current_seqnum - (expected_seqnum % 32)) % 32 < 10:
            buffer[current_seqnum] = sender_packet
        
        # Send ACK packet after receiving this packet
        ACK_packet = Packet(0, (expected_seqnum - 1) % 32, 0, '')
        send_packet(ACK_packet)

