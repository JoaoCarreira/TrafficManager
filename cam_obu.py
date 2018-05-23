import sys
from datetime import datetime
import time
import threading

table_of_nodes=[]
gpsInfo= "(2,2)"
NodeID=0

lock = threading.Lock()

def generate_message(Node,messageID):
	global NodeID
	messageToSend = {'Type': 'CAM', 'ID': Node, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now()),'Message_ID': messageID}
	NodeID=Node
	return messageToSend

def process_CAM(node_info):

	add_table(node_info)

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
	return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")

