from datetime import datetime

#Function that converts a string into a datetime object
def convertStringIntoDatetime(string):
	return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")

#Fucntion that adds a message received to the table of nodes
def addToTable(node_info, table, mode):

	counter = 0
	exist = False

	#If the table of nodes has any entry, iterate over it.
	if len(table) > 0:
		for i in table:
			#If the message received was from a node that already exists on the table
			#add it to the table iff the received message has a higher timestamp, meaning that it is more recent.
			if node_info['ID']==i['ID']:
				#If the node already exists on the table, we signal it with a flag
				exist = True
				#If the node only has a Beacon associated with it and a CA message was received, update the table
				if node_info['Type'] == 'CAM' and i['Type'] == 'Beacon':
						table[counter]=node_info
						break
				if convertStringIntoDatetime(node_info['Timestamp']) > convertStringIntoDatetime(i['Timestamp']):
					table[counter]=node_info
					break
			counter += 1

		#If the node does not exist on the table, we simply add that message to it.
		if exist == False:
			table.append(node_info)
	
	#If the table is empty, simply add the message	
	else:
		table.append(node_info)

	if mode == 0:
		print("....................................")
		print("Tabela:" + str(table))
		print("....................................")

	return table
