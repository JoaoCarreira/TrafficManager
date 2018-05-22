import struct
import socket
import sys
import time
import uuid
#from hashlib import blake2s
import threading
from datetime import datetime
import json
import uuid

MCAST_GRP = "224.0.0.1"
MCAST_PORT = 10000

#mac_addr = hex(uuid.getnode()).replace('0x', '')
#NodeID = ':'.join(mac_addr[i : i + 2] for i in range(0, 11, 2))

NodeID = 0

messageID = 0

table_of_nodes=[]

lock= threading.Lock()

semaforo_1={'table':[],'state':"red",'zona':[[4,7],[5,7],[6,7],[7,7]],'cars':0}
semaforo_2={'table':[],'state':"red",'zona':[],'cars':0}
semaforo_3={'table':[],'state':"red",'zona':[[9,6],[9,5],[9,4],[9,3]],'cars':0}
semaforo_4={'table':[],'state':"red",'zona':[],'cars':0}

number_of_cars={'cars_in_1':0,'cars_in_2':0,'cars_in_3':0,'cars_in_4':0}

def main():

	global lock
	global NodeID

	NodeID = sys.argv[1]
	print("Your node is: " + str(NodeID))

	threadsender = ThreadSender("Thread-sender")
	threadsender.start()

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()

	threadalgoritmo=ThreadAlgoritmo("Thread-algoritmo")
	threadalgoritmo.start()


def sender():

	gpsInfo= "(2,2)"
	timeToSendMessage = time.time() +0.5
	while True:

		lock.acquire()
		try:
			number_of_nodes=len(table_of_nodes)
		finally:
			lock.release()

		while time.time() > timeToSendMessage:

			generate_messageID()

			messageToSend = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now()),'Message_ID': messageID}
			
			#print("Message to send: " + str(messageToSend))

			data = json.dumps(messageToSend)

			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
			sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
			timeToSendMessage = time.time() + 0.5

def receiver():

	global table_of_nodes

	#thread1 = myThread("Thread-1")
	#thread1.start()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((MCAST_GRP, MCAST_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
 
	while True:
		
		data=sock.recv(1024)
		messageReceived=data.decode()
		node_info=json.loads(messageReceived)

		if node_info['ID'] == NodeID:
			continue

		else:
			print("Received the following message: \n" + str(json.loads(messageReceived)))
			if node_info['Type']=='Beacon':
				add_table(node_info)

			if node_info['Type']=='CAM':
				add_table(node_info)
				process_CAM(node_info)

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

def convertStringIntoDatetime(string):
	return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")


def threadClock():
	global table_of_nodes

	while True:
		counter = 0

		#for i in table_of_nodes:

  			#if i[4]==15:
  			
  				#print("TIMEOUT \nDeleting the table entry of the NodeID=" + table_of_nodes[counter][0]+ " ...")
  				#del(table_of_nodes[counter])
  				#continue

#  			table_of_nodes[counter][4] += 1 
 # 			time.sleep(1)
  #			counter += 1

#-------------------------------------#
# Tratamento das mensagens CAM na RSU #
#-------------------------------------#

def process_CAM(node_info):

	pos=node_info['Coordinates']

	filtro(node_info,pos)

def filtro (node,posicao):

	global semaforo_1
	global semaforo_2
	global semaforo_3
	global semaforo_4

	if posicao in semaforo_1['zona']:
		semaforo_1['table']=add_table_rsu(node,"semaforo_1")

	elif posicao in semaforo_2['zona']:
		semaforo_2['table']=add_table_rsu(node,"semaforo_2")
		return True

	elif posicao in semaforo_3['zona']:
		semaforo_3['table']=add_table_rsu(node,"semaforo_3")

	elif posicao in semaforo_4['zona']:
		semaforo_4['table']=add_table_rsu(node,"semaforo_4")

	else:
		print("fora da zona de interesse")

		counter=0
		id=node['ID']

		for no in semaforo_1['table']:
			if no['ID']==id:
				del semaforo_1['table'][counter]
				break

			counter+=1

		counter=0

		for no in semaforo_2['table']:
			if no['ID']==id:
				del semaforo_2['table'][counter]
				break

			counter+=1

		counter=0

		for no in semaforo_3['table']:
			if no['ID']==id:
				del semaforo_3['table'][counter]
				break

			counter+=1

		counter=0

		for no in semaforo_4['table']:
			if no['ID']==id:
				del semaforo_4['table'][counter]
				break

			counter+=1

def add_table_rsu(node_info,semaforo):
	
	counter = -1
	flag_exist=False

	if semaforo=="semaforo_1":
		table=semaforo_1['table']
	elif semaforo=="semaforo_2":
		table=semaforo_2['table']
	elif semaforo=="semaforo_3":
		table=semaforo_3['table']
	else:
		table=semaforo_4['table']

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

	return table

def count_cars():

	global number_of_cars

	number_of_cars['cars_in_1']=len(semaforo_1['table'])
	number_of_cars['cars_in_2']=len(semaforo_2['table'])
	number_of_cars['cars_in_3']=len(semaforo_3['table'])
	number_of_cars['cars_in_4']=len(semaforo_4['table'])

	print(number_of_cars)

def decide_cor():

	global semaforo_1
	global semaforo_2
	global semaforo_3
	global semaforo_4

	count_cars()


	maior=max(number_of_cars,key=number_of_cars.get)

	if maior=="cars_in_1" or maior=="cars_in_2":
		semaforo_1['state']="green"
		semaforo_2['state']="green"
		semaforo_3['state']="red"
		semaforo_4['state']="red"

	elif maior=="cars_in_3" or maior=="cars_in_4":
		semaforo_1['state']="red"
		semaforo_2['state']="red"
		semaforo_3['state']="green"
		semaforo_4['state']="green"

	print(semaforo_1['state'],semaforo_2['state'],semaforo_3['state'],semaforo_4['state'],"\n")
	time_semaforo=1
	timer_semaforo(time_semaforo)

def timer_semaforo(timer):

	time.sleep(timer)	
	
	decide_cor()

class ThreadAlgoritmo (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
      decide_cor()

if __name__ == '__main__':
    main() 