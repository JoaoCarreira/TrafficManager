import sys
import time
import uuid
import threading
import datetime
import json
import uuid
import CarController
import Communication
import cam_obu

SLEEP_TIME = 2
Timer=0
X=int(0)
Y=int(0)
Co=[X,Y]
DIR="direçao"
EstaAndar=False
lock1 = threading.Lock()

#NodeID = hex(uuid.getnode()).replace('0x', '')

NodeID = 0

table_of_nodes=[]

lock= threading.Lock()

def main():

	global NodeID

	NodeID = sys.argv[1]
	print("Your node is: " + str(NodeID))

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()
	#threadAndar = ThreadAndar("Thread-andar")
	#threadAndar.start()
	threadsender = ThreadSender("Thread-sender")
	threadsender.start()
	thread1 = myThread("Thread-clock")
	thread1.start()

def incrementMessageID(id):
	
	return id + 1

def addToTable(node_info):

	global table_of_nodes

	counter = 0
	flag_exist=False

	lock.acquire()
	try:
		if len(table_of_nodes) > 0:
			for i in table_of_nodes:
				if node_info['ID']==i['ID']:
					if node_info['Type'] == 'CAM' and i['Type'] == 'Beacon':
						table_of_nodes[counter]=node_info
						flag_exist=True
						break
					if convertStringIntoDatetime(node_info['Timestamp']) > convertStringIntoDatetime(i['Timestamp']):
						table_of_nodes[counter]=node_info
						flag_exist=True
						break
				counter += 1


			if flag_exist==False:
				table_of_nodes.append(node_info)
				
		else:
			table_of_nodes.append(node_info)

		print("....................................")
		print("Tabela:" + str(table_of_nodes))
		print("....................................")

	finally:
		lock.release()

def convertStringIntoDatetime(string):
	return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")

class myThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		threadClock()

def threadClock():
	global table_of_nodes

	while True:
		counter = 0

		for i in table_of_nodes:

			if (convertStringIntoDatetime(i['Received']) + datetime.timedelta(seconds=10)) < datetime.datetime.now():

				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
				print("TIMEOUT \nDeleting the table entry of the NodeID=" + table_of_nodes[counter]['ID']+ " ...")
				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")                  
				del(table_of_nodes[counter])
				continue

			counter += 1

class ThreadReceiver (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		receiver()

#Function that is responsible for receiving the messages to the network
def receiver():

	sock = Communication.setReceiver()
 
	while True:
		
		node_info = json.loads(Communication.receiveMessage(sock))
		node_info.update({'Received': str(datetime.datetime.now())})

		#Filter to ignore the own messages sent
		if node_info['ID'] == NodeID:
			continue

		else:
			print("Received the following message: \n" + str(node_info))
			if node_info['Type']=='Beacon':
				addToTable(node_info)

			if node_info['Type']=='CAM':
				addToTable(node_info)
				#cam_obu.process_CAM(node_info)


class ThreadSender (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		sender()

#Function that is responsible for sending the messages to the network
def sender():

	messageID = 0

	time_increment=False

	timeToSendMessage = time.time()

	camBuffer = []

	while True:

		#If the table of neighbors is empty, then a Beacon message will be generated.
		#Otherwise, a CA message is generated.

		while time.time() > timeToSendMessage:
				
			gpsInfo=getCoordinates()
			
			messageID = incrementMessageID(messageID)

			beaconMessage = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.datetime.now())}
			
			camMessage = {'Type': 'CAM', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.datetime.now())}

			data = None

			if len(table_of_nodes) == 0:

				print("Message to send: " + str(beaconMessage))

				data = json.dumps(beaconMessage)

				counter = 0

				if len(camBuffer) == 0:
					print("First message CA on buffer")
					camBuffer.append(camMessage)

				else:

					for i in camBuffer:
						if i['Type'] == 'CAM':
							print("Updating CAM on buffer")
							i = camMessage
						
						counter += 1

			
			else:

				print("Message to send: " + str(beaconMessage))

				for i in camBuffer:
					if i['Type'] == 'CAM':
						print("Sending CAM from the buffer")
						camMessage = i
						camBuffer.remove(i)

				data = json.dumps(camMessage)

			Communication.sendMessage(data)
			timeToSendMessage = time.time() + 0.5
				

class ThreadAndar(threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		TocaAndar(int(float(sys.argv[2])),int(float(sys.argv[3])),int(float(sys.argv[4])),sys.argv[5])

def TocaAndar(x,y,co,dir):
	global X
	global Y
	global DIR
	global Co

	#X=int(float(sys.argv[1]))
	#Y=int(float(sys.argv[2]))
	X=x
	Y=y
	Co[0]=X
	Co[1]=Y
	
	#DIR=sys.argv[3]
	DIR=dir
	#coordenadas=int(sys.argv[4])
	coordenadas=co

	gpio_data = {}
	gpio_data = CarController.read_gpio_conf('gpio_pins')

	pwm_motor = {}
	CarController.gpio_init(gpio_data, pwm_motor)

	andar(gpio_data,int(coordenadas),pwm_motor)
	'''Actualiza coordenadas actuais'''
	
	X=Co[0]
	Y=Co[1]
	#sleep(3)
	#andar(gpio_data,int(coordenadas),pwm_motor)
	if RASPBERRY == True:
		GPIO.cleanup()

################################

def tempoParaAndar(coordenadas):
	tempo=0

	if coordenadas == 1:
		tempo=1.185
	elif coordenadas == 2:
		tempo=1.76
	elif coordenadas == 3:
		tempo=2.062
	elif coordenadas == 4:
		tempo=2.584
	elif coordenadas == 5:
		tempo=2.964
	elif coordenadas>5:
		tempo=(coordenadas-5)*0.4 + 2.964
	
	return tempo

def andar(gpio_data,coordenadas,pwm_motor):

	global Timer
	global EstaAndar

	if RASPBERRY == True:
		pwm_motor['enable_dir'].ChangeDutyCycle(MAX_FORWARD_SPEED)
		GPIO.output(gpio_data['forward_dir'], GPIO.HIGH)
		GPIO.output(gpio_data['backward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['enable_dir'], GPIO.HIGH)
		
	
		EstaAndar=True
		
		Timer=time.time()
		sleep (tempoParaAndar(coordenadas))
		pwm_motor['enable_dir'].ChangeDutyCycle(MAX_BACKWARD_SPEED)
		GPIO.output(gpio_data['backward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['forward_dir'], GPIO.LOW)
		GPIO.output(gpio_data['enable_dir'], GPIO.HIGH)
		sleep(0.5)
		EstaAndar=False
	
	if RASPBERRY == False:
		Timer=time.time()
		lock1.acquire()
		try:
			EstaAndar=True
		finally:
			lock1.release()

		print("Comecei a andar")
		sleep (tempoParaAndar(coordenadas))
	
		lock1.acquire()
		try:
			EstaAndar=False
		finally:
			lock1.release()

		print("Parei de andar")


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
