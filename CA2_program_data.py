from gpiozero import LED, Buzzer

from time import time
from time import sleep
import datetime
import json
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import MFRC522
import signal
import sys
import Adafruit_DHT
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from rpi_lcd import LCD
import telepot

# Global Variable Here
my_bot_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
book_time = 0
lcdmsg = "AVAILABLE!"

#Define gpiozero ports and parts here
uid = None
prev_uid = None
current_uid = None
continue_reading = True
bz = Buzzer(5)
pin = 21
lcd = LCD()


# This is the Publisher
client = mqtt.Client()
client.connect("localhost",1883,60)


# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	if message.payload == "1":
		global book_time
		global lcdmsg
		global current_uid
		print("Space has been unbooked")
		bz.on()
		sleep(3)
		bz.off()
		current_uid = None
		lcd.text("Space's unbooked",1)
		lcd.text("by Admin!",2)
		sleep(5)
		book_time = 0
		current_uid = None
		lcdmsg = "AVAILABLE!"
		lcd.text(lcdmsg,2)
		my_rpi.publish("room1/booking", "0",1)
	print("--------------\n\n")

# Custom MQTT message callback
def callLCD(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	if message.payload == "off":
		lcd.clear()
	else:
		lcd.text(message.payload,1)
		lcd.text("",2)

def callBuzz(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	if message.payload == "1":
		bz.on()
	else:
		bz.off()

host = "XXXXXXXXXXXXXXXXXXXXX.iot.region-code-number.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("basicPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing

my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()

#Subscribe to Admin Channel	
my_rpi.subscribe("admin/space1/unbook", 1, customCallback)
my_rpi.subscribe("admin/lcd",1,callLCD)
my_rpi.subscribe("admin/buzz",1,callBuzz)

#Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
	global continue_reading
	print("Ctrl+C captured, ending read.")
	contine_reading = False
	GPIO.cleanup()

#Hook the SIGINT
signal.signal(signal.SIGINT,end_read)

#Create an object of the class MFRC522
mfrc522 = MFRC522.MFRC522()

#welcome message
print("Welcome to the MFRC522 data read example")
print("Press Ctrl-C to stop")

def respondToMsg(msg):
	global temperature_value
	chat_id = msg['chat']['id']
	command = msg['text']

	print('Got command: {}'.format(command))

	if command == '/space1':
		bot.sendMessage(chat_id, 'Space 1 is now: %s' % (lcdmsg))
		bot.sendMessage(chat_id, 'Temperature at Room 1: %s degree celsius' % (temperature_value))

bot = telepot.Bot(my_bot_token)
bot.message_loop(respondToMsg)

# this loop keeps checking for chips
# if one is near it will get the UID


while True:
	update = True
	old_time = time()
	new_time = time()
	#scan for cards
	lcd.text('Space is',1)
	lcd.text(lcdmsg,2)
	(status,TagType) = mfrc522.MFRC522_Request(mfrc522.PICC_REQIDL)
	if status == mfrc522.MI_OK:
  	# get the UID of the card
		(status,uid) = mfrc522.MFRC522_Anticoll()
		if current_uid == None:
			book_time = time()
			print("Spaced Booked by card with UID of {}".format(uid))
			bz.on()
			sleep(3)
			bz.off()
			current_uid = uid	
			my_rpi.publish("room1/booking", "1",1)
			# my_rpi.publish("room2/booking","1",1)
			lcdmsg = "BOOKED!"  
			lcd.text(lcdmsg,2)     	
			try:
				print("")
			except KeyboardInterrupt:
				update = False
		elif uid != current_uid:
			print("Space has been booked by card with UID of {}".format(current_uid))
			bz.on()
			sleep(3)
			bz.off()
		elif uid == current_uid:
			print("Space has been unbooked")
			bz.on()
			sleep(3)
			bz.off()
			current_uid = None
			lcdmsg = "AVAILABLE!"
			lcd.text(lcdmsg,2)
			book_time = 0
			my_rpi.publish("room1/booking", "0",1)
			# my_rpi.publish("room2/booking","0",1)		
			try:
				print("")
			except KeyboardInterrupt:
				update = False
	if book_time > 1:
		con_time = time()
		print(con_time)
		print(book_time)
		time_diff = con_time - book_time
		if time_diff > 15:
			my_rpi.publish("space1/alert", "Booking at Space 1 is too Long, Check on Space." ,1)
			print("Booking Over")
			lcd.text("Please Unbook",1)
			lcd.text("Now",2)
			my_rpi.publish("room1/booking", "2",1)
			# my_rpi.publish("room2/booking","2",1)	
			bz.on()
			sleep(2)
			bz.off()
	humidity,temperature = Adafruit_DHT.read_retry(11,pin)
	temperature_value = temperature
	humidity_value = humidity
	print('Temperature:',temperature_value)
	print('Humidity:',humidity_value)		   	
	sleep(3)
	if temperature_value > 15:
		try:
			print("")
		except KeyboardInterrupt:
			update = False
	old_time = new_time
	new_time = time()

	print("Wait 5 secs before getting next temperature values...")
	sleep(5)
