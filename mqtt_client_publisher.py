import paho.mqtt.client as mqtt #import the client1
import time
import cv2


broker_address="192.168.43.102" 
port  = 1883
#broker_address="iot.eclipse.org" #use external broker
client = mqtt.Client("P1") #create new instance
client_security = mqtt.Client("security")
client_security.connect(broker_address,port)
client.connect(broker_address,port) #connect to broker

cam_nir = cv2.VideoCapture(0) #change the index according the camera
cam_nir.set(3, 320); #width
cam_nir.set(4, 240); #height
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


water_level = 0

security_camera = "off"

water_pump="off"

def on_message(client, userdata, message):
    msg = str(message.payload.decode("utf-8"))
    global security_camera
    global water_pump
    if msg =="on":
        security_camera="on"
    elif msg =="off":
        security_camera="off"

    elif msg=="1":
        print("Water pump is on , start watering")
        client.publish("farm/pump","Sp")
        water_pump = "on"

    elif msg =="0":
        client.publish("farm/pump","t")
        print("Water pump is off")
        water_pump ="off"

client.on_message=on_message #attach function to callback
client_security.on_message = on_message

while True:

    if water_pump =="on":
        client.publish("farm/water_level",water_level)#publish

        water_level+=1
        

    if water_level == 100:
        water_level=0
    #print(f"water level is {water_level}")

    client.loop_start() #start the loop
    #print("Subscribing to topic","house/bulbs/bulb1")
    client.subscribe("farm/motor")
    client.loop_stop()

    client_security.loop_start()
    client_security.subscribe("farm/security")
    client.loop_stop()

    
    if security_camera =="on":
        _,frame_nir = cam_nir.read()
        result, frame_nir = cv2.imencode('.jpg',frame_nir,encode_param)

        filename = "test.jpg"
        with open(filename,'wb') as new_file:
            new_file.write(frame_nir)

        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    time.sleep(1)


