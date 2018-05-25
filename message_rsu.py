import sys
import time
import uuid
import threading
import datetime
import json
import uuid
RASPBERRY=False
if RASPBERRY == True:
	import RPi.GPIO as GPIO
	gpio.setmode(gpio.BOARD)
	gpio.setwarnings(False)
	gpio.setup(38,gpio.OUT)
	gpio.setup(40,gpio.OUT)
	gpio.setup(36,gpio.OUT)
import Communication
import Util

TIME_CHANGE_WITHOUT_CARS=10
TIME_YELLOW=1

NodeID = hex(uuid.getnode()).replace('0x', '')

table_of_nodes=[]

lock= threading.Lock()
lock_app= threading.Lock()

#Dictionary for every traffic light
trafficLight_1={'table':[],'state':"red",'ROI':[[4,7],[5,7],[6,7],[7,7]],'cars':0}
trafficLight_2={'table':[],'state':"red",'ROI':[[10,8],[11,8],[12,8],[13,8]],'cars':0}
trafficLight_3={'table':[],'state':"red",'ROI':[[9,6],[9,5],[9,4],[9,3]],'cars':0}
trafficLight_4={'table':[],'state':"red",'ROI':[[8,9],[8,10],[8,11],[8,12]],'cars':0}

number_of_cars={'cars_in_1':0,'cars_in_2':0,'cars_in_3':0,'cars_in_4':0}

old_state=""

#Fixed coordinates of the RSU
gpsInfo= [8,8]

#Used to the breadboard and leds
#gpio.setmode(gpio.BOARD)
#gpio.setwarnings(False)
#gpio.setup(38,gpio.OUT)
#gpio.setup(40,gpio.OUT)
#gpio.setup(36,gpio.OUT)

def main():

	print("Your node is: " + str(NodeID))

	threadSender = ThreadSender("Thread-sender")
	threadSender.start()
	threadReceiver = ThreadReceiver("Thread-receiver")
	threadReceiver.start()
	threadAlgorithm=ThreadAlgorithm("Thread-algorithm")
	threadAlgorithm.start()
	thread1 = ThreadClock("Thread-1")
	thread1.start()
#####################################################################
# Thread that is responsible of sending the messages to the network #
#####################################################################
class ThreadSender (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
      sender()

def sender():

	timeToSendMessage = time.time() +0.5

	while True:

		lock.acquire()
		try:
			number_of_nodes=len(table_of_nodes)
		finally:
			lock.release()

		while time.time() > timeToSendMessage:

			messageToSend = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.datetime.now())}
		
			data = json.dumps(messageToSend)

			Communication.sendMessage(data)
			timeToSendMessage = time.time() + 0.5

#######################################################################
# Thread that is responsible of receiveng the messages of the network #
#######################################################################
class ThreadReceiver (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
      receiver()

def receiver():

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
			if node_info['Type']=='Beacon':
				try:
					table_of_nodes = Util.addToTable(node_info, table_of_nodes, 1)
				finally:
					lock.release()

			if node_info['Type']=='CAM':
				try:
					table_of_nodes = Util.addToTable(node_info, table_of_nodes, 1)
				finally:
					lock.release()
				process_CAM(node_info)

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
				print("TIMEOUT \nDeleting the table entry of the NodeID=" + table_of_nodes[counter]['ID']+ " ...")
				print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")                  
				del(table_of_nodes[counter])
				continue

			counter += 1

def process_CAM(node_info):

	pos=node_info['Coordinates']

	filtro(node_info,pos)

#Function used to filter messages that are outside of the ROI of every traffic light
def filtro (node,posicao):

	global trafficLight_1
	global trafficLight_2
	global trafficLight_3
	global trafficLight_4

	#In case the received message is inside of the ROI of one traffic light, add that to the number of cars in it
	if posicao in trafficLight_1['ROI']:
		trafficLight_1['table']=addTrafficLightTable(node,"trafficLight_1")

	elif posicao in trafficLight_2['ROI']:
		trafficLight_2['table']=addTrafficLightTable(node,"trafficLight_2")

	elif posicao in trafficLight_3['ROI']:
		trafficLight_3['table']=addTrafficLightTable(node,"trafficLight_3")

	elif posicao in trafficLight_4['ROI']:
		trafficLight_4['table']=addTrafficLightTable(node,"trafficLight_4")

	#If the received message is outside the ROI but that node is in the table of any of the traffic lights, 
	# we have to remove it, since it is already out of the ROI
	else:
		print("Out of the ROI")

		counter=0
		#Iterate over the trafficLight_1 table and remove if the node was there
		for no in trafficLight_1['table']:
			if no['ID'] == node['ID']:
				lock_app.acquire()
				try:
					del trafficLight_1['table'][counter]
				finally:
					lock_app.release()
				return

			counter+=1

		counter=0
		#Iterate over the trafficLight_2 table and remove if the node was there
		for no in trafficLight_2['table']:
			if no['ID'] == node['ID']:
				lock_app.acquire()
				try:
					del trafficLight_2['table'][counter]
				finally:
					lock_app.release
				return

			counter+=1

		counter=0
		#Iterate over the trafficLight_3 table and remove if the node was there
		for no in trafficLight_3['table']:
			if no['ID'] == node['ID']:
				lock_app.acquire()
				try:
					del trafficLight_3['table'][counter]
				finally:
					lock_app.release()
				return

			counter+=1

		counter=0
		#Iterate over the trafficLight_4 table and remove if the node was there
		for no in trafficLight_4['table']:
			if no['ID'] == node['ID']:
				lock_app.acquire()
				try:
					del trafficLight_4['table'][counter]
				finally:
					lock_app.release()
				return

			counter+=1

#Function used to add a node to a specific traffic light table
def addTrafficLightTable(node_info,trafficLight):

	if trafficLight=="trafficLight_1":
		table=trafficLight_1['table']
	elif trafficLight=="trafficLight_2":
		table=trafficLight_2['table']
	elif trafficLight=="trafficLight_3":
		table=trafficLight_3['table']
	else:
		table=trafficLight_4['table']

	lock_app.acquire()
	try:
		table = Util.addToTable(node_info, table, 1)
	finally:
		lock_app.release()

	return table

#Function used to count the number of cars in each traffic light
def countCars():

	global number_of_cars

	number_of_cars['cars_in_1']=len(trafficLight_1['table'])
	number_of_cars['cars_in_2']=len(trafficLight_2['table'])
	number_of_cars['cars_in_3']=len(trafficLight_3['table'])
	number_of_cars['cars_in_4']=len(trafficLight_4['table'])

	print(number_of_cars)
###########################################################################################
# Thread that is responsible of running the algorithm to manage the traffic lights colors #
###########################################################################################
class ThreadAlgorithm (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
      decideColor()

def decideColor():

	global trafficLight_1
	global trafficLight_2
	global trafficLight_3
	global trafficLight_4
	global old_state

	countCars()
	last_vehicle=""
	mostCars=max(number_of_cars,key=number_of_cars.get)

	#Case either the traffic light 1 or 2 have the most cars in it
	if mostCars=="cars_in_1" or mostCars=="cars_in_2":

		new_state="trafficLight_1_2"

		if mostCars=="cars_in_1" and len(trafficLight_1['table'])!=0:
			#Chose the last car to the trafficLight_1
			last_vehicle=trafficLight_1['table'][-1]['ID']

		elif mostCars=="cars_in_2" and len(trafficLight_2['table'])!=0:
			#Chose the last car to the trafficLight_2
			last_vehicle=trafficLight_2['table'][-1]['ID']
		else:
			old_state=changeState(new_state)
			time.sleep(TIME_CHANGE_WITHOUT_CARS)
			new_state="trafficLight_3_4"

	#Case either the traffic light 3 or 4 have the most cars in it
	elif mostCars=="cars_in_3" or mostCars=="cars_in_4":

		new_state="trafficLight_3_4"

		if mostCars=="cars_in_3" and len(trafficLight_3['table'])!=0:
			#Chose the last car to the trafficLight_3
			last_vehicle=trafficLight_3['table'][-1]['ID']
		elif mostCars=="cars_in_3"and len(trafficLight_4['table'])!=0:
			#Chose the last car to the trafficLight_4
			last_vehicle=trafficLight_4['table'][-1]['ID']

	#Change the state accordingly to the traffic ligths that have more cars in it
	old_state=changeState(new_state)
	
	print(trafficLight_1['state'],trafficLight_2['state'],trafficLight_3['state'],trafficLight_4['state'])

	timer_trafficLight(new_state,last_vehicle)

#Function used to change the state of a pair of traffic lights
def changeState(state):

	if state!=old_state:
		if state=="trafficLight_1_2":

			if RASPBERRY==True:
				gpio.output(40,gpio.HIGH)
				gpio.output(38,gpio.LOW)
				gpio.output(36,gpio.LOW)

			trafficLight_1['state']="green"
			trafficLight_2['state']="green"
			trafficLight_3['state']="red"
			trafficLight_4['state']="red"

		elif state=="trafficLight_3_4":

			if RASPBERRY==True:
				gpio.output(40,gpio.LOW)
				gpio.output(38,gpio.HIGH)
				gpio.output(36,gpio.LOW)

				time.sleep(TIME_YELLOW)

				gpio.output(40,gpio.LOW)
				gpio.output(38,gpio.LOW)
				gpio.output(36,gpio.HIGH)

			trafficLight_1['state']="red"
			trafficLight_2['state']="red"
			trafficLight_3['state']="green"
			trafficLight_4['state']="green"

	return state

def timer_trafficLight(state,last_vehicle):

	flag_last_car=True
	if last_vehicle!="":
		while flag_last_car==True:
			flag_last_car= False
			if state=="trafficLight_1_2":
				lock_app.acquire()
				try:
					for i in trafficLight_1['table']:
						if i['ID']==last_vehicle:
							flag_last_car=True
							break

					for i in trafficLight_2['table']:
						if i['ID']==last_vehicle:
							flag_last_car=True
							break
				finally:
					lock_app.release()
			if state=="trafficLight_3_4":
				lock_app.acquire()
				try:
					for i in trafficLight_3['table']:
						if i['ID']==last_vehicle:
							flag_last_car=True
							break

					for i in trafficLight_4['table']:
						if i['ID']==last_vehicle:
							flag_last_car=True
							break
				finally:
					lock_app.release()

	else:
		timecounter=ThreadTimeCounter("Thread-timeCounter")
		timecounter.start()
		time.sleep(TIME_CHANGE_WITHOUT_CARS + TIME_YELLOW)
		flag_last_car==False

	decideColor()
##################################################################################################
# Thread that is responsible for suggesting the recommended velocity of the first car in the ROI #
##################################################################################################
class ThreadTimeCounter (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		timeCounter()

def timeCounter():
	global counter
	counter = TIME_CHANGE_WITHOUT_CARS + TIME_YELLOW
	while counter>0:
		counter-=1
		if len(trafficLight_1['table'])>0 and counter!=0:
			coord=trafficLight_1['table'][0]['Coordinates']
			coord_x=coord[0]
			final=8-coord_x
			print("#######################################################################")
			print("Velocidade recomendada: "+str(float(final)/float(counter))+" coord/s")
			print("#######################################################################")
		time.sleep(1)

if __name__ == '__main__':
    main() 
