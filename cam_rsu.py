
#-------------------------------------#
# Tratamento das mensagens CAM na RSU #
#-------------------------------------#

import sys
import threading
from datetime import datetime
import time


table_semaforo_1=[]
table_semaforo_2=[]
table_semaforo_3=[]
table_semaforo_4=[]

state_semaforo_1="red"
state_semaforo_2="red"
state_semaforo_3="red"
state_semaforo_4="red"

zona_semaforo_1=["(2,2)"]
zona_semaforo_2=[]
zona_semaforo_3=[]
zona_semaforo_4=[]

number_of_cars={"cars_in_1":0,"cars_in_2":0,"cars_in_3":0,"cars_in_4":0}

time_semaforo=0

lock= threading.Lock()

def process_CAM(node_info):

	pos=node_info['Coordinates']

	filtro(node_info,pos)

def filtro (node,posicao):

	if posicao in zona_semaforo_1:
		table_semaforo_1=add_table(node,"semaforo_1")
		return True

	elif posicao in zona_semaforo_2:
		table_semaforo_2=add_table(node,"semaforo_2")
		return True

	elif posicao in zona_semaforo_3:
		table_semaforo_3=add_table(node,"semaforo_3")
		return True

	elif posicao in zona_semaforo_4:
		table_semaforo_4=add_table(node,"semaforo_4")
		return True

	else:
		return False

def add_table(node_info,semaforo):
	counter = -1

	if semaforo=="semaforo_1":
		table_of_nodes=table_semaforo_1
	elif semaforo=="semaforo_2":
		table_of_nodes=table_semaforo_2
	elif semaforo=="semaforo_3":
		table_of_nodes=table_semaforo_3
	else:
		table_of_nodes=table_semaforo_4

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

		print("Tabela:" + str(table_of_nodes))

	return table_of_nodes

def count_cars():

	number_of_cars['cars_in_1']=len(table_semaforo_1)
	number_of_cars['cars_in_2']=len(table_semaforo_2)
	number_of_cars['cars_in_3']=len(table_semaforo_3)
	number_of_cars['cars_in_4']=len(table_semaforo_4)

	print(number_of_cars)

def decide_cor():

	global time_semaforo
	global state_semaforo_1
	global state_semaforo_2
	global state_semaforo_3
	global state_semaforo_4

	count_cars()

	maior=max(number_of_cars,key=number_of_cars.get)

	threadprint = ThreadPrint("Thread-print")
	threadprint.start()

	threadsemaforo = ThreadSemaforo("Thread-semaforo")

	lock.acquire()
	try:
		if maior=="cars_in_1" or maior=="cars_in_2":
			state_semaforo_1="green"
			state_semaforo_2="green"
			state_semaforo_3="red"
			state_semaforo_4="red"

		if maior=="cars_in_3" or maior=="cars_in_4":
			state_semaforo_1="red"
			state_semaforo_2="red"
			state_semaforo_3="green"
			state_semaforo_4="green"
	finally:
		lock.release()

	print(state_semaforo_1,state_semaforo_2,state_semaforo_3,state_semaforo_4)

	lock.acquire()
	try:
		time_semaforo=5
	finally:
		lock.release()

	threadsemaforo.start()

def timer_semaforo():

	global state_semaforo_1
	global state_semaforo_2
	global state_semaforo_3
	global state_semaforo_4

	time_init=time.time()

	while True:
		if (time.time()-time_init)==time_semaforo:
			lock.acquire()
			try:
				state_semaforo_1="red"
				state_semaforo_2="red"
				state_semaforo_3="red"
				state_semaforo_4="red"
		
			finally:
				lock.release()
			break
	
	decide_cor()

def convertStringIntoDatetime(string):
	return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")

class ThreadSemaforo (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
   	  timer_semaforo()

class ThreadPrint (threading.Thread):
   def __init__(self, threadID):
      threading.Thread.__init__(self)
      self.threadID = threadID
   def run(self):
      while True:
      	print(state_semaforo_1,state_semaforo_2,state_semaforo_3,state_semaforo_4)
      	print(table_semaforo_1,table_semaforo_2,table_semaforo_3,table_semaforo_4)
      	time.sleep(3)


if __name__ == '__main__':
	
	decide_cor()

	
	
		







