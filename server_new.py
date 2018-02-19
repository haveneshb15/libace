# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import paho.mqtt.client as mqtt
import datetime
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer

gevent.monkey.patch_all()

from flask import Flask, request, Response, render_template
from gpiozero import LED, Buzzer
from rpi_lcd import LCD
from time import sleep
space1_green = LED(12)
space1_red = LED(16)
space2_green = LED(20)
space2_red = LED(21)
bz = Buzzer(5)

host = "XXXXXXXXXXXXX.iot.region-code-number.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"
my_rpi = AWSIoTMQTTClient("libacePubTest")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath) 
my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()

def ledOn():
	space1_green.on()
	space1_red.on()
	space2_green.on()
	space2_red.on()
	return "LEDs have been turned on!"

def ledOff():
	space1_green.off()
	space1_red.off()
	space2_green.off()
	space2_red.off()
	return "LEDs have been turned off!"

def buzzOn():
	mqtt_message = "1"
	my_rpi.publish("admin/buzz", mqtt_message, 1)
	print("MQTT Sent")
        sleep(2)

def buzzOff():
	mqtt_message = "0"
	my_rpi.publish("admin/buzz", mqtt_message, 1)
	print("MQTT Sent")
        sleep(2)

def lcdOn():
	mqtt_message = "This is a test."
    	my_rpi.publish("admin/lcd", mqtt_message, 1)
	print("MQTT Sent")
        sleep(2)

def lcdOff():
	mqtt_message = "off"
    	my_rpi.publish("admin/lcd", mqtt_message, 1)
	print("MQTT Sent")
        sleep(2)

app = Flask(__name__)

@app.route("/")
def index():
	return render_template('index.html')

@app.route("/writeLED/<status>")
def writePin(status):
	if status == 'On':
		response = ledOn()
	else:
		response = ledOff()

	templateData = {
		'title': 'Status of LED',
		'response': response
	} 

	return render_template("pin.html", **templateData)


@app.route("/writeBuzz/<status>")
def writePinBuzz(status):
	if status == 'On':
		response = buzzOn()
	else:
		response = buzzOff()

	templateData = {
		'buzztitle': 'Status of Buzzer',
		'buzzresponse': response
	} 

	return render_template("pinbuzz.html", **templateData)

@app.route("/writeLcd/<status>")
def writePinLcd(status):
	if status == 'On':
		response = lcdOn()
	else:
		response = lcdOff()

	templateData = {
		'lcdtitle': 'Status of LCD',
		'lcdresponse': response
	} 

	return render_template("pinlcd.html", **templateData)



if __name__ == '__main__':
	try:
		http_server = WSGIServer(('0.0.0.0',8002), app)
		app.debug = True
		http_server.serve_forever()

	except:
		print("Exception") 
