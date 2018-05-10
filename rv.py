import struct
import socket
import sys
import time
import uuid
#from hashlib import blake2s
import threading
import time
from datetime import datetime
import cam_rsu

MCAST_GRP = "224.0.0.1"
MCAST_PORT = 10000

NodeID = "0"

messageID = 0

test = False

table_of_nodes=[]

lock= threading.Lock()

def main():

	global lock

	if "-s" in sys.argv[1:]:
		
		threadreceiver = ThreadReceiver("Thread-receiver")
		threadreceiver.start()
		sender()


def sender():

	global test

	#generate_nodeID()

	time_increment=False

	while True:

		lock.acquire()
		try:
			number_of_nodes=len(table_of_nodes)
		finally:
			lock.release()

		if number_of_nodes==0:

			if time_increment==False:
				timeToSendMessage = time.time() + 
				2

			while time.time() > timeToSendMessage:

				gpsInfo= "(2,2)"

				generate_messageID()

				messageToSend = "Beacon" + "," + NodeID + "," + gpsInfo + "," + str(datetime.now())
				data = messageToSend.encode()
				print("Beacon")
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data, (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 10
				time_increment=True

		else:

			if time_increment==True:
				timeToSendMessage = time.time() + 2

			while time.time() > timeToSendMessage:
				messageToSend = "CAM" + "," + NodeID + "," + gpsInfo + "," + str(datetime.now())
				data = messageToSend.encode()
				print("CAM")
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
				sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
				sock.sendto(data, (MCAST_GRP, MCAST_PORT))
				timeToSendMessage = time.time() + 10
				time_increment=False


def receiver():

	global test

	thread1 = myThread("Thread-1")
	thread1.start()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((MCAST_GRP, MCAST_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
 
	while True:
		
		exist=False
		data=sock.recv(1024)
		messageReceived=data.decode()
		if test == True:
			print("Received the following message: \n" + messageReceived)
		node_info=messageReceived.split(',')

		node_info.append(0)

		print(table_of_nodes)

		if node_info[0]=='Beacon':
			node_info.pop(0)

			counter = 0

			lock.acquire()
			try:
				for i in table_of_nodes:
  					if node_info[0]==i[0]:
  						table_of_nodes[counter]=node_info
  						exist=True
  						counter += 1

				if exist!=True and node_info[0]!=NodeID:
					table_of_nodes.append(node_info)

			finally:
				lock.release()

		if node_info[0]=='CAM':
			cam_rsu.process_CAM()

def generate_messageID():
	
	global messageID
	messageID += 1



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



def threadClock():
	global table_of_nodes
	global test

	while True:
		counter = 0

		for i in table_of_nodes:
  			if i[4]==15:
  			
  				print("TIMEOUT \nDeleting the table entry of the NodeID=" + table_of_nodes[counter][0]+ " ...")
  				del(table_of_nodes[counter])
  				continue

  			table_of_nodes[counter][4] += 1 
  			time.sleep(1)
  			counter += 1


if __name__ == '__main__':
    main() 
