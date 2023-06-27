import paho.mqtt.client as mqtt 
from random import randrange, uniform
import time

mqttBroker ="mqtt.eclipseprojects.io" 

client = mqtt.Client("Temperature_Inside")
client.connect(mqttBroker) 

while True:
    randNumber = uniform(20.0, 21.0)
    client.publish("nigger_TEMPERATURE", 'nigger')
    print("Just published " + 'nigger' + " to topic TEMPERATURE")
    time.sleep(1)