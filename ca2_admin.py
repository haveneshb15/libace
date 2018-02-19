# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from gpiozero import LED, Button
from time import sleep
import sys, json

space1_green = LED(12)
space1_red = LED(16)

space2_green = LED(20)
space2_red = LED(21)

button1 = Button(19, pull_up = False)
button2 = Button(26, pull_up = False)

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	if message.payload == '1':
		space1_red.on()
		space1_green.off()
	elif message.payload == '0':
		space1_red.off()
		space1_green.on()
	else:
		space1_red.blink()
	print("From topic: ")
	print(message.topic)
	print("--------------\n\n")
	
def publishBtn():
	mqtt_message = "1"
	my_rpi.publish("admin/space1/unbook", mqtt_message, 1)
	print("MQTT Sent")
        sleep(2)

host = "XXXXXXXXXXXX.iot.region-code-number.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

space1_green.on()
space1_red.off()

try:
    my_rpi = AWSIoTMQTTClient("libacePubSub")
    my_rpi.configureEndpoint(host, 8883)
    my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath) 
    my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
    my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
    my_rpi.configureMQTTOperationTimeout(5)  # 5 sec
       
    # Connect and subscribe to AWS IoT
    my_rpi.connect()
    
    my_rpi.subscribe("room1/booking", 1, customCallback)
    button1.when_pressed = publishBtn
    sleep(2)
  
except:
    print("Unexpected error:", sys.exc_info()[0])


while True:
    try:   
        print("Waiting for messages to come in");
        sleep(5)
    except:
        print("Unexpected error in while True")
