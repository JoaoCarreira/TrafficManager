import struct
import socket
import sys
import time
import uuid
#from hashlib import blake2s
import threading
import datetime
import cam_obu
import json
import uuid
RASPBERRY = False
import sys, json
if RASPBERRY == True:
	import RPi.GPIO as GPIO
from time import sleep
import time
import threading


MCAST_GRP = "224.0.0.1"
MCAST_PORT = 10000


##################################################


FREQUENCY = 100
MIN_SPEED = 0
MAX_SPEED = 100
MAX_FORWARD_SPEED = 60
MAX_BACKWARD_SPEED =60
SLEEP_TIME = 2
Timer=0
X=int(0)
Y=int(0)
Co=[X,Y]
DIR="direçao"
EstaAndar=False
lock1 = threading.Lock()

######################################
#mac_addr = hex(uuid.getnode()).replace('0x', '')
#NodeID = ':'.join(mac_addr[i : i + 2] for i in range(0, 11, 2))

NodeID = 0

messageID = 0

table_of_nodes=[]

lock= threading.Lock()

def main():

	global lock
	global NodeID
	NodeID = sys.argv[1]
	print("Your node is: " + str(NodeID))

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()
	threadAndar = ThreadAndar("Thread-andar")
	threadAndar.start()
	threadsender = ThreadSender("Thread-sender")
	threadsender.start()
	thread1 = myThread("Thread-clock")
	thread1.start()


def sender():

	time_increment=False

	timeToSendMessage = time.time()

	while True:

		number_of_nodes=len(table_of_nodes)

		if number_of_nodes==0:

			while time.time() > timeToSendMessage:
				
				
				gpsInfo=getCoordenadas()
				
				generate_messageID()

				messageToSend = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.datetime.now())}
				
				print("Message to send: " + str(messageToSend))

				data = json.dumps(messageToSend)

				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 5
				#time_increment=True

		else:

			while time.time() > timeToSendMessage:
				gpsInfo=getCoordenadas()
				messageToSend = {'Type': 'CAM', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.datetime.now())}
				data = json.dumps(messageToSend)
				print("Message to send: " + str(messageToSend))
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 5
				

def receiver():

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((MCAST_GRP, MCAST_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
 
	while True:
		
		exist=False
		data=sock.recv(1024)
		messageReceived=data.decode()
		node_info=json.loads(messageReceived)
		node_info.update({'Received': str(datetime.datetime.now())})

		if node_info['ID'] == NodeID:
			continue

		else:
			print("Received the following message: \n" + str(node_info))
			if node_info['Type']=='Beacon':
				add_table(node_info)

			if node_info['Type']=='CAM':
				add_table(node_info)
				cam_obu.process_CAM(node_info)

def generate_messageID():
	
	global messageID
	messageID += 1

def add_table(node_info):

	global table_of_nodes

	counter=-1
	flag_exist=False

	lock.acquire()
	try:
		if len(table_of_nodes) > 0:

			for i in table_of_nodes:
				counter += 1
				if node_info['ID']==i['ID']:
					if convertStringIntoDatetime(node_info['Timestamp']) > convertStringIntoDatetime(i['Timestamp']):
						print("Encontrei um com ID igual")
						table_of_nodes[counter]=node_info
						flag_exist=True
						break

			if flag_exist==False:
				table_of_nodes.append(node_info)
				
		else:
			table_of_nodes.append(node_info)

		print("Tabela:" + str(table_of_nodes))

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


class ThreadReceiver (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		receiver()

class ThreadSender (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		sender()

class ThreadAndar(threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		TocaAndar(int(float(sys.argv[2])),int(float(sys.argv[3])),int(float(sys.argv[4])),sys.argv[5])

#-------------------------------------#
#          Movimento do carro         #
#-------------------------------------#

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
	gpio_data = read_gpio_conf('gpio_pins')

	pwm_motor = {}
	gpio_init(gpio_data, pwm_motor)

	#thread1 = myThread("Thread-1")
	#thread1.start()

	andar(gpio_data,int(coordenadas),pwm_motor)
	'''Actualiza coordenadas actuais'''
	
	
	X=Co[0]
	Y=Co[1]
	#sleep(3)
	#andar(gpio_data,int(coordenadas),pwm_motor)
	if RASPBERRY == True:
		GPIO.cleanup()


def threadClock():
	global table_of_nodes

	while True:
		counter = 0

		for i in table_of_nodes:

			if (convertStringIntoDatetime(i['Received']) + datetime.timedelta(seconds=5)) < datetime.datetime.now():
				
				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
				print("TIMEOUT \nDeleting the table entry of the NodeID=" + table_of_nodes[counter]['ID']+ " ...")
				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")                  
				del(table_of_nodes[counter])
				continue

			counter += 1


################################
def read_gpio_conf(field):
	print('read_gpio_conf')
	with open('gpio_pins.txt') as json_data:
		data = json.load(json_data)
		print('gpio_pins  data: ', data)
		json_data.close()
	return data[field]


def gpio_init(gpio_data, pwm_motor):
	print ('gpio_init')
	gpio_data = read_gpio_conf('gpio_pins')
	if RASPBERRY == True:
	   GPIO.setmode(GPIO.BOARD)
	print('GPIO.setmode(GPIO.BOARD)')
	reset_gpio(gpio_data)
	reset_pwm_motor(gpio_data, pwm_motor)
	return (gpio_data, pwm_motor)

def reset_gpio(gpio_data):
	for key, val in list(gpio_data.items()):
		if key != 'stop':
			if RASPBERRY == True:
				GPIO.setup(val,GPIO.OUT)
				GPIO.output(val,GPIO.LOW)
			print ('GPIO.setup(',val,',GPIO.OUT)')
			print ('GPIO.output(',val,',GPIO.LOW)')


def reset_pwm_motor(gpio_data, pwm_motor):
	for key, val in list(gpio_data.items()):
		if key in ('enable_dir'):
			if RASPBERRY == True:
				pwm_motor[key] = GPIO.PWM(val, FREQUENCY)
				pwm_motor[key].start(MIN_SPEED)
			print ('pwm_motor[',key,'] = GPIO.PWM(',val,',',FREQUENCY,')')
			print ('pwm_motor[',key,'].start(',MIN_SPEED,')')
	return pwm_motor

def tempoParaAndar(coordenadas):
	tempo=0
	if coordenadas == 1:
		tempo=1.185
	if coordenadas == 2:
		tempo=1.76
	if coordenadas == 3:
		tempo=2.062
	if coordenadas == 4:
		tempo=2.584
	if coordenadas == 5:
		tempo=2.964
	if coordenadas>5:
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



def getCoordenadas():
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
