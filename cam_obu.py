import Util
from datetime import datetime

#Fucntion resonsible for generating the CA messages
def generateCamMessage(NodeID, gpsInfo, messageID):

	messageToSend = {'Type': 'CAM', 'ID': NodeID, 'Coordinates': gpsInfo, 'Timestamp': str(datetime.now()),'Message_ID': messageID}
	return messageToSend