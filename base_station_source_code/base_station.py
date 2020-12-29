# Base Station 
# LoRa Communication
# Emergency Protocol 

import json
import requests
import smtplib
import time
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x

#--- LoRa Setup Configuration
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433)
    print('success')
except RuntimeError as error:
    print('error')
	
	
#--- Emergency Protocol Functions 
def emergencyMessage(data, helper):
	str1 = "FALL EMERGENCY!!! \n"
	str2 = "Happened around:  " + data['hour'] + ":" + data['minute'] + ":" + data['second'] + " EST \n\n"
	
	str3 = "Latitude: " + data['lat'] + "\n"
	str4 = "Longitude: " + data['lon'] + "\n"
	str5 = "Altitude: " + data['alt'] + "\n\n"
	
	str6 = "In Need of Help from: " + helper + "\n"
	str7 = "#EMERGENCY  " + "#Climbing_Fall  " + "#In_Need_Of_Help\n\n"
	
	str8 = "Location: " + "https://www.google.com/maps/search/?api=1&query=" + str(data['lat']) + "," + str(data['lon'])
	
	msg_long = str1 + str2 + str3 + str4 + str5 + str6 + str7 + str8
	msg_short = str1 + str2 + str3 + str4 + "\n" + str6
	
	return msg_long, msg_short

def sendEmergencyEmail(data, contact):
	gmail_user = 'iotgroup999@gmail.com'
	gmail_password = 'IOTgroup999'
	
	msg1, msg2 = emergencyMessage(data, str(contact["Name"]))
	
	sent_from = gmail_user
	to = contact["Email Account"]
	subject = 'FALL EMERGENCY'
	body = msg1
	
	
	try:
		server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
		server.ehlo()
		server.login(gmail_user, gmail_password)
		server.sendmail(sent_from, to, body)
		server.close()

		print ('Email sent!')
		
	except Exception as e:
		print ('Something went wrong...')
		print(e)
		
def sendTweet(data, contact):	
	msg1, msg2 = emergencyMessage(data, contact["Twitter Account"])
	message = msg1

	post_data = json.dumps({'api_key': '3EN642RNK8XO8ARX', 'status': message})
	req_url = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update'
	res = requests.post(req_url, headers = {'content-type': 'application/json'}, data = post_data).json()
	
	print (str(res))
	
def sendTextMessage(data, contact):
	msg1, msg2 = emergencyMessage(data, str(contact["Name"]))
	message = msg2
	phone = contact["Phone Number"]

	post_data = json.dumps({'phone': phone, 'message': message, 'key': 'textbelt'})
	req_url = 'https://textbelt.com/text'
	res = requests.post(req_url, headers = {'content-type': 'application/json'}, data = post_data).json()
	
	print(str(res) + "\n\n" + message)
	


# ---------------------------MAIN--------------------------------
while True:
	packet = None
	
	packet = rfm9x.receive()
	if packet is not None:
            
            prev_packet = packet
            packet_text = str(prev_packet, "utf-8")
            hour = packet_text[0:2]
            minute = packet_text[2:4]
            second = packet_text[4:6]
            
            lat = packet_text[6:18]
            lon = packet_text[18:30]
            alt = packet_text[30:40]
            status = packet_text[40:41]
            device_id = packet_text[41:45]
            
            data = {"device_id":device_id,"hour":hour,"minute":minute,"second":second,"lat":str(lat),"lon":str(lon),"alt":str(alt),"status":str(status)}
            
            print(data)
		
            if data["status"] == "1": 
                
                print('Entered Emergency Procedure')
                url = "http://ec2-3-87-228-201.compute-1.amazonaws.com:5002/get_contact/" + data["device_id"]
                print("url: ",url)
                r = requests.get(url)                
                result = r.content
                print(result)
                encoding = "utf-8"
                contact = json.loads(result.decode(encoding))
                
                print(contact)
                sendTweet(data, contact)
                sendEmergencyEmail(data, contact)
                sendTextMessage(data, contact)
                break
	










	

