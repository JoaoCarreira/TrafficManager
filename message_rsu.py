import struct
import socket
import sys
import time
import uuid
#from hashlib import blake2s
import threading
from datetime import datetime
import cam_rsu
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

def main():

	global lock
	global NodeID

	NodeID = sys.argv[1]
	print("Your node is: " + str(NodeID))

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()
	sender()


def sender():

	gpsInfo= "(2,2)"
	timeToSendMessage = time.time() + 2
	while True:

		lock.acquire()
		try:
			number_of_nodes=len(table_of_nodes)
		finally:
			lock.release()

		while time.time() > timeToSendMessage:

			generate_messageID()

			messageToSend = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now())}
			
			print("Message to send: " + str(messageToSend))

			data = json.dumps(messageToSend)

			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
			sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
			timeToSendMessage = time.time() + 10

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
		
		exist=False
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
				cam_rsu.process_CAM(node_info)

def generate_messageID():
	
	global messageID
	messageID += 1

def add_table(node_info):
	counter = -1

	lock.acquire()
	try:
		if len(table_of_nodes) > 0:

			for i in table_of_nodes:
				counter += 1
				if node_info['ID']==i['ID']:
					print("Encontrei um com ID igual")
					if convertStringIntoDatetime(node_info['Timestamp']) > convertStringIntoDatetime(i['Timestamp']):
						table_of_nodes[counter]=node_info
						break
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

if __name__ == '__main__':
    main() 
