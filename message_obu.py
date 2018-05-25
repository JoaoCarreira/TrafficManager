import sys
import time
import uuid
import threading
import datetime
import json
import uuid
import Communication
import cam_obu
import CarGPIO
import Util

RASPBERRY = False
if RASPBERRY == True:
	import RPi.GPIO as GPIO

MAX_FORWARD_SPEED = 60
MAX_BACKWARD_SPEED = 60

SLEEP_TIME = 2
Timer = 0
X = int(0)
Y = int(0)
Co = [X,Y]
DIR = ""
EstaAndar=False
lock1 = threading.Lock()

#To be able to run the program in the same machine, we can't have all the ids of the nodes being 
#dependent on the MAC address.
#In case the various OBUs and RSU are run in different machines, just uncomment the following line.
#NodeID = hex(uuid.getnode()).replace('0x', '')

NodeID = 0

table_of_nodes=[]

lock= threading.Lock()

def main():

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()
	threadAndar = Threadmove("Thread-andar")
	threadAndar.start()
	threadsender = ThreadSender("Thread-sender")
	threadsender.start()
	thread1 = ThreadClock("Thread-clock")
	thread1.start()

#Fucntion used to increment the message id number
def incrementMessageID(id):
	
	return id + 1
########################################################################################
# Thread that is responsible of checkig if a node present on a table should be removed #
########################################################################################
class ThreadClock (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		threadClock()

def threadClock():
	global table_of_nodes

	while True:
		counter = 0

		#Iterate over the table of nodes
		for i in table_of_nodes:
			#If an entry of the table has been sitting there without any update for more than 10 seconds, 
			# the node is considered to be inactive and its entry is removed from the table
			if (Util.convertStringIntoDatetime(i['Received']) + datetime.timedelta(seconds=10)) < datetime.datetime.now():

				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
				print("TIMEOUT \nDeleting the table entry of the NodeID = " + table_of_nodes[counter]['ID']+ " ...")
				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")                  
				del(table_of_nodes[counter])
				continue

			counter += 1
#######################################################################
# Thread that is responsible of receiveng the messages of the network #
#######################################################################
class ThreadReceiver (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		receiver(sys.argv[1])

def receiver(NodeID):

	global table_of_nodes

	sock = Communication.setReceiver()
 
	while True:
		
		node_info = json.loads(Communication.receiveMessage(sock))

		#When a message is received, a field is added to it indicating the 
		#timestamp of when the message was received
		node_info.update({'Received': str(datetime.datetime.now())})

		#Ignore the own messages sent
		if node_info['ID'] == NodeID:
			continue

		else:
			lock.acquire()
			print("Received the following message: \n" + str(node_info))
			if node_info['Type']=='Beacon':
				try:
					table_of_nodes = Util.addToTable(node_info, table_of_nodes, 0)
				finally:
					lock.release()

			if node_info['Type']=='CAM':
				try:
					table_of_nodes = Util.addToTable(node_info, table_of_nodes, 0)
				finally: 
					lock.release()
#####################################################################
# Thread that is responsible of sending the messages to the network #
#####################################################################
class ThreadSender (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		sender(sys.argv[1])

def sender(NodeID):

	messageID = 0

	timeToSendMessage = time.time()

	camBuffer = []

	print("Your node is: " + str(NodeID))

	while True:

		#Both the Beacon and CA messages are generated at the same time.
		while time.time() > timeToSendMessage:
				
			gpsInfo=getCoordinates()
			
			messageID = incrementMessageID(messageID)

			timeGenerated = datetime.datetime.now()

			beaconMessage = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(timeGenerated)}
			
			camMessage = cam_obu.generateCamMessage(NodeID, gpsInfo, messageID)

			data = None

			#If the table of neighbors is empty, then it is the Beacon message that is sent.
			if len(table_of_nodes) == 0:

				print("Message to send: " + str(beaconMessage))

				data = json.dumps(beaconMessage)

				counter = 0

				#If the buffer of CA messages is empty, then the generated CA message is saved there.
				if len(camBuffer) == 0:
					print("First CA message on buffer")
					camBuffer.append(camMessage)

				#If the buffer of CA messages is not empty, then the one that is there is replaced by the newly generated.
				else:
					for i in camBuffer:
						if i['Type'] == 'CAM':
							print("Updating CA message on buffer")
							i = camMessage
						
						counter += 1

			#If the table of neighbors is not empty, then it is the CA message present in the buffer that is sent.
			else:

				print("Message to send: " + str(beaconMessage))

				for i in camBuffer:
					if i['Type'] == 'CAM':
						print("Sending CAM from the buffer")
						camMessage = i
						#When the CA message in the buffer is sent, it is removed from there.
						camBuffer.remove(i)

				data = json.dumps(camMessage)

			Communication.sendMessage(data)
			timeToSendMessage = time.time() + 0.5
				
################################################
# Thread that is responsible of moving the car #
################################################

class Threadmove(threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		moveCar(int(float(sys.argv[2])),int(float(sys.argv[3])),int(float(sys.argv[4])),sys.argv[5])

def moveCar(x,y,co,dir):
	global X
	global Y
	global DIR
	global Co

	X=x
	Y=y
	Co[0]=X
	Co[1]=Y
	
	DIR=dir

	coordinates=co

	gpio_data = {}
	gpio_data = CarGPIO.read_gpio_conf('gpio_pins')

	pwm_motor = {}
	CarGPIO.gpio_init(gpio_data, pwm_motor, RASPBERRY)

	move(gpio_data,int(coordinates),pwm_motor)
	input("press enter to move again")
	X=Co[0]
	Y=Co[1]
	move(gpio_data,int(coordinates),pwm_motor)

	if RASPBERRY == True:
		GPIO.cleanup()

#Fucntion that is responible for, given the number of coordinates that we want the car to move, 
#calculate the time that that movement will take.
#After measurements were made, there are values, in time, well defined for the movement of until 5 coordinates.
#After those 5 coordinates, the time that the car took to move, was constant.
def timeToMove(coordinates):
	tempo=0

	if coordinates == 1:
		tempo=1.185
	elif coordinates == 2:
		tempo=1.76
	elif coordinates == 3:
		tempo=2.062
	elif coordinates == 4:
		tempo=2.584
	elif coordinates == 5:
		tempo=2.964
	elif coordinates>5:
		#Formula for moving more than 5 coordinates.
		tempo=(coordinates-5)*0.4 + 2.964
	
	return tempo

def move(gpio_data,coordinates,pwm_motor):

	global Timer
	global EstaAndar

	if RASPBERRY == True:
		pwm_motor['enable_dir'].ChangeDutyCycle(MAX_FORWARD_SPEED)
		GPIO.output(gpio_data['forward_dir'], GPIO.HIGH)
		GPIO.output(gpio_data['backward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['enable_dir'], GPIO.HIGH)
		
		EstaAndar=True
		
		Timer=time.time()
		time.sleep (timeToMove(coordinates))
		pwm_motor['enable_dir'].ChangeDutyCycle(MAX_BACKWARD_SPEED)
		GPIO.output(gpio_data['backward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['forward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['enable_dir'], GPIO.HIGH)
		time.sleep(0.5)
		EstaAndar=False
	
	if RASPBERRY == False:
		Timer=time.time()
		lock1.acquire()
		try:
			EstaAndar=True
		finally:
			lock1.release()

		time.sleep(timeToMove(coordinates))
	
		lock1.acquire()
		try:
			EstaAndar=False
		finally:
			lock1.release()

def getCoordinates():
	global Timer
	global EstaAndar
	global X
	global Y
	global DIR
	global Co
	coordenada = 0
	
	lock1.acquire()
	try:
		if EstaAndar==True:

			tempo = time.time()-Timer
			if 0.5<tempo<1.5:
				coordenada = 1
			if 1.5<tempo<2:
				coordenada = 2
			if 2<tempo<2.4:
				coordenada =3
			if 2.4<tempo<2.8:
				coordenada =4
			if 2.8<tempo<3:
				coordenada = 5
			if tempo>=3:
				coordenada = int(((tempo-3)//0.4)+5)
			if DIR=="x":
				a=coordenada+X
				Co[0]=a
			if DIR == "y":
				b=coordenada+Y
				Co[1]=b

	finally:
		lock1.release()

	return (Co[0],Co[1])

################################

if __name__ == '__main__':
	main() 
