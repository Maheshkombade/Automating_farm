import paho.mqtt.client as mqtt 
from random import randrange, uniform
import time

mqttBroker ="mqtt.eclipseprojects.io" 

client = mqtt.Client("Temperature_Inside")
client.connect(mqttBroker) 

i = 0
while True:
    randNumber = uniform(20.0, 21.0)
    client.publish("nigger_TEMPERATURE", i)
    i+=1
    print("Just published " + str(i) + " to topic TEMPERATURE")
    time.sleep(0.5)