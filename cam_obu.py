import sys
from datetime import datetime
import time


table_of_nodes=[]
gpsInfo= "(2,2)"
NodeID=0
def generate_message(Node,messageID):
	global NodeID
	messageToSend = {'Type': 'CAM', 'ID': Node, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now()),'Message_ID': messageID}
	NodeID=Node
	return messageToSend

def process_CAM(node_info):

	add_table(node_info)

	print("Tabela da CAM: "+str(table_of_nodes))


def add_table(node_info):
	counter = -1

	if len(table_of_nodes) > 0:
		for i in table_of_nodes:
			counter += 1
			if node_info['ID']==i['ID']:
				if convertStringIntoDatetime(node_info['Timestamp']) > convertStringIntoDatetime(i['Timestamp']):
					table_of_nodes[counter]=node_info
					break
			table_of_nodes.append(node_info)
				
	else:
		table_of_nodes.append(node_info)

	return table_of_nodes

def convertStringIntoDatetime(string):
	return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")