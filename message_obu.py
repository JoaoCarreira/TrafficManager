import struct
import socket
import sys
import time
import uuid
#from hashlib import blake2s
import threading
from datetime import datetime
import cam_obu
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

gpsInfo= "(2,2)"

def main():

	global lock
	global NodeID

	NodeID = sys.argv[1]
	print("Your node is: " + str(NodeID))

	threadreceiver = ThreadReceiver("Thread-receiver")
	threadreceiver.start()
	sender()


def sender():

	buffer_messages=[None]

	time_increment=False

	while True:

		lock.acquire()
		try:
			number_of_nodes=len(table_of_nodes)
		finally:
			lock.release()

		generate_messageID()

		if number_of_nodes==0:

			messageToSend = cam_obu.generate_message(NodeID,messageID)
			buffer_messages[0]=messageToSend
			print(str(buffer_messages))

			if time_increment==False:
				timeToSendMessage = time.time() + 2
				time_increment = True

			while time.time() > timeToSendMessage:

				generate_messageID()

				messageToSend = {'Type': 'Beacon', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now()),'Message_ID': messageID}
				
				print("Message to send: " + str(messageToSend))

				data = json.dumps(messageToSend)

				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 10

		else:

			if len(buffer_messages)>0:
				messageToSend=buffer_messages[0]
				timeToSendMessage = time.time()

			else:
				messageToSend = cam_obu.generate_message(NodeID)
				timeToSendMessage = time.time() + 2
				time_increment=False

			while time.time() > timeToSendMessage:
				data = json.dumps(messageToSend)
				print("Message to send: " + str(messageToSend))
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data.encode(), (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 10	

		time.sleep(5)
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
				cam_obu.process_CAM(node_info)

def generate_messageID():
	
	global messageID
	lock.acquire()
	try:
		messageID += 1
	finally:
		lock.release()

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
