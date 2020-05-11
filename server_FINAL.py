#Authors: Peter Pekkanen & Vahe Sanasarian
#Course: DVA243
#Examinated & approved: 2020-05-06
import socket

#Creat socket for server using IPv4 & UDP
server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

#Declare server IP and port
udp_host = "192.168.1.234"	#Needs to be changed before executing script
udp_port = 9999				#Any free UDP port


#Binding socket to IP and Port
server_socket.bind((udp_host,udp_port))
print("Waiting for message!")
ON = '1'
OFF = '0'

while True:
    print("Waiting for client...")

    #Reciving data from clients. Will include the data & address from sender.
    data,addr = (server_socket.recvfrom(1024))
    print("***Server***")
    print("Received Message: " + data.decode() + "\nFrom the sensor" + str(addr))
    var = int(data.decode())
    print(type(var))
    print(var)
    #Sending encoded data to the sending client. Able to input more values for a more complex solution.
    if var == 1:
        print("Sending ON message")
        server_socket.sendto(ON.encode(), (addr))   #ON message is in here
    elif var == 0:
        print("Sending OFF message")
        server_socket.sendto(OFF.encode(), (addr))  #OFF message is in here
    else:
        print("Error: Invalid value")
    print('************')
