#Authors: Peter Pekkanen & Vahe Sanasarian
#Course: DVA243
#Examinated & approved: 2020-05-06
import RPi.GPIO as GPIO
import time
import glob
import os
import threading
import socket
import sys
from random import randint		#Used for random integers in artificial packet-loss
try:                            #Compability Error
        import queue
except ImportError:
        import Queue as queue

acuator_data = 5        #Global variable which holds 1 or 0 for the acuator. Value = 5 is the default value which will not activate anything.
                        #When the first package arrives containing 1 or 0, the system will assign that value to the global variable and run like intended.
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)  #Socket definition
udp_server = ('192.168.1.234', 9999)                    #Server IP

os.system('modprobe w1-gpio')                   #Used to check temperature
os.system('modprobe w1-therm')                  #Used to check temperature

base_dir = '/sys/bus/w1/devices/'               #Used to check temperature
device_folder = glob.glob(base_dir + '28*')[0]  #Used to check temperature
device_file = device_folder + '/w1_slave'       #Used to check temperature

GPIO.setwarnings(False)                                                 #Stops error messeages if GPIO is used in other places.

GPIO.setmode(GPIO.BCM)          #Mode for the GPIO pins
#mode = GPIO.getmode()          #Used to detect which mode is active, which we already know.
#print (mode)                   #Prints out the GPIO mode used.

GPIO.setup(9, GPIO.OUT)         #LED1
GPIO.setup(11, GPIO.OUT)        #LED2
GPIO.setup(14, GPIO.IN)         #Sensor

GPIO.output(9, 0)               #Turns off any active LEDs if still active from previous executions.
GPIO.output(11, 0)
#Start of sensor Functions#
def read_temp_raw():                            #Gathers raw data from sensor
    f = open(device_file, 'r')                  #Opens raw input from sensor as read only
    lines = f.readlines()
    f.close()
    return lines                                #Returns the raw data

def read_temp():                                #Reads data from read_temp_raw and converts it into appropiate temperature
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c                           #Data of temperature is returned in celsius.

def random_number(choice):
        #choice '0' is for random packet-loss , '1' is for burst error which will only send between 1-2 packages
        #'2' will severly harm the communication and send no packages.
        value = 0     	          		#Defines variable used for 'return'
        if choice == 0:
                value = randint(3, 5)	#Between 3 and 5 packages will be sent. "Minimal packet-loss"
                return value
        elif choice == 1:
                value = randint(1, 2)	#Between 1 and 2 packages will be sent. "Severe packet-loss"
                return value
        elif choice == 2:				#0 packages will be sent. "Burst-error"
                return 0
        else:
                print("Error")

def temp_trigger():
        threshold = 26					#Changeable threshold variable
        temperature_input = 0
        send_data = 0                                                                                                                   #Used as a barrier to seperate the two modes from overlapping.
        if read_temp() > threshold:                                                                                                     #If its over %treshold celsius as the code starts running, then need to lower temperature for functionality.
                send_data = 1
                print("Code started when its over the threshold at: " + str(threshold))
                print("Lower temperature for functionality")
        while True:
                messages_to_send = random_number(randint(0, 1)) #Random amount of packages to sent, used to simulate random packet-loss over ethernet.
				#messages_to_send = 5							#The error-free solution.
                temperature_input = read_temp()
                sent_messages = 0                               #Resets number of sent messages
                if (int(temperature_input) > threshold) and (send_data == 0):
                        print("Sending '1'")
                        msg = '1'
                        while (sent_messages < messages_to_send):
                                sock.sendto(msg.encode(), (udp_server))
                                sent_messages = (sent_messages + 1)
                        print("Complete : sent %d messages containing '1'" % (sent_messages))
                        send_data = 1

                if (int(temperature_input) <= threshold) and (send_data == 1):
                        print("Sending '0'")
                        msg = '0'
                        while (sent_messages < messages_to_send):
                                sock.sendto(msg.encode(), (udp_server))
                                sent_messages = (sent_messages + 1)
                        print("Complete : sent %d messages containing '0'" % (sent_messages))
                        send_data = 0
#End of the sensor functions#
#Start of acuator Functions#
def time_count(toggle, toggle_var):     #Function for acuator 2 - if the latest package been 1 for 5 seconds, then turn on
        foo = 0
        global acuator_data
        while (int(foo) < 5) and (int(toggle) == 0):
                foo = int(foo + 1)
                print(foo)
                time.sleep(1)
        if (acuator_data == 1) and (foo == 5):          #Additional check for acuator 2
                print("Activating acuator 2...")
                GPIO.output(11, 1)
                toggle_var.put(1)                                       #Returns value for the toggle variable.
        return 0

def server_response():                                                  #Data recieved from the server
        while True:
                global acuator_data
                print("Global data is: " + str(acuator_data))
                print("Listening for packages ...")
                data,addr = sock.recvfrom(1024)
                #print("Data retrieved: " + data.decode())              #Debugging message
                converted_data = int(data.decode())
                if acuator_data != converted_data:                      #If the latest package is not the same as our current value, then overwrite the global variable with the newest value.
                        acuator_data = converted_data
                        print("New data retrieved")
                time.sleep(1)

def acuator():
        toggle_var = queue.Queue()                                      #Queue variable for the toggle variable
        toggle = 0                                                      #Indicates if the acuator is already on or not
        var = 0
        while True:
                global acuator_data
                if acuator_data == 1 and toggle == 0:
                        t4 = threading.Thread(target=time_count, args=(toggle,toggle_var,))     #Starts time function
                        print("ACTIVATING ACUATOR 1")
                        GPIO.output(9, 1)                                                       #If over 26 degrees, activates acuaotor 1
                        t4.start()                                                              #Thread for acuator 2, see time_count for closer details on the function.
                        toggle = toggle_var.get()
                elif acuator_data == 0 and toggle == 1:                                         #If its no longer over 26 degrees celsius
                        t4.join()
                        print("DEACTIVATING ACUATORS ...")
                        GPIO.output(9, 0)
                        GPIO.output(11, 0)
                        toggle = 0
                time.sleep(0.5)

def main():
        #Definition of threads
        t1 = threading.Thread(target=temp_trigger)
        t2 = threading.Thread(target=server_response)
        t3 = threading.Thread(target=acuator)
        #Starting up threads
        t1.start()
        t2.start()
        t3.start()
        #Merge of t1, t2, t3 which will never occur in this program.
        t1.join()
        t2.join()
        t3.join()
        #Cleans up old data on acuators
        GPIO.cleanup(9)
        GPIO.cleanup(11)

main()
print("return 0")
