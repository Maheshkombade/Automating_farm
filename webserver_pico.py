import re
import network
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led
import machine
import  _thread
from machine import  ADC, Pin

import utime

## soil sensors
soil_sensors = [ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26))] # Soil moisture Pin

relay_outputs = [Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT)]

lock = _thread.allocate_lock()

readDelay = 0.5



ssid =""
password = ""

num_sensors=3
curr_values=[0,0,0]
curr_setpoints=[0,0,0]
pump_state=[0,0,0]
control_state = "OFF"

with open('wifi.txt', 'r') as f:
    # Read the first line and remove the newline character
    ssid = f.readline().rstrip('\n')
    # Read the second line and remove the newline character
    password = f.readline().rstrip('\n')
print(ssid)

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection
    
def make_string_sensors(n,curr_value,curr_setpoints): #curr_value list of n sensors
    out_str = ""
    for i in range(n):
        out_str+=f""" <tr>
                      <td>Moisture sensor_{i+1}</td>
                      <td name = "current value">{curr_value[i]}</td>
                      <td name="currentsetpoints">{curr_setpoints[i]}</td>

                      <form action="./setpoints" method="POST">
                      <td><input type="text" name="moist_sensor_{i}" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                    </form>
                    </tr>"""
        
    return out_str


def make_string_pumps(n,pump_state): #curr_value list of n sensors
    out_str = ""
    for i in range(n):
        out_str+=f""" <tr>
                      <td>Pump_{i+1}</td>
                    
                      <td name="currentstate">{"ON" if pump_state[i]==1 else "OFF"}</td>

                      <form action="./pump_{i}_on" method="POST">
                      
                      <td><button type="submit">ON</button></td>
                        </form>

                        <form action="./pump_{i}_off" method="POST">
                      
                      <td><button type="submit">OFF</button></td>
                        </form>

                    </tr>"""
        
    return out_str


def read_sensors():
    global num_sensors
    global soil_sensors
    global curr_values
    
    for i in range(num_sensors):
        curr_values[i]=soil_sensors[i].read_u16()
        
        
        
def control_system():
    global relay_outputs
    global curr_values
    global curr_setpoints
    global  pump_state
    threshold = 0.2
    for i in range(len(curr_setpoints)):
        error = curr_setpoints[i]-curr_values[i]
        
        lock.acquire()
        if control_state=="ON":
            if error > threshold:
                pump_state = "ON"
                relay_outputs[i].value = 1
                #turn on the motor or solenoid
            else:
                pump_state="OFF"
                #turn off the motor or solenoid
                relay_outputs[i].value=0
        elif control_state=="OFF":
            if pump_state=="ON":
                pass
            
        lock.release()
        
def webpage():
    global num_sensors
    global curr_values
    global curr_setpoints
    global pump_state
    
    #Template HTML
    html = f"""
            <!DOCTYPE html>
            <html lang="en-us">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width">
                
                <title>Farm Auto</title>
               
              </head>
              <body>
              
                    <h2>Automatic or Manual</h2>

                    <form action="./automatic">
                        <input type="submit" value="Automatic" />
                    </form>

                    <form action="./manual">
                        <input type="submit" value="Manual" />
                    </form>
              
              
              
                <form action="./sensors" method="get">
                    <div>
                      <label for="say">Number of Moisture sensor</label>
                      <input name="num_sensors" id="say" placeholder="Enter number 1 to 6" />
                    </div>
                    <div>
                      <button type="submit">Submit</button>
                    </div>
                  </form>

                <h1>Table</h1>
                <table>
                    <tr>
                      <td><h1>Attributes</h1></td>
                      <td><h1>Current values</h1></td>
                      <td><h1>Current-Setpoints</h1> </td>
                      <td><h1>New-Setpoints</h1> </td>
                      <td> <h1> Submit</h1></td>
                    </tr>

                    {make_string_sensors(num_sensors,curr_values,curr_setpoints)}
                    
                  <br>
                  <br>

                  {make_string_pumps(num_sensors,pump_state)}
                  </table>

                    

                    <br>
                    <br>
                    <br>

                    <form action="./wifi" method="get">
                        <div>
                          <label for="say">WIFI SSID</label>
                          <input name="wifi_ssid" id="say" placeholder="Enter Your SSID" />
                        </div>
                        <div>
                          <label for="to">WIFI PASSWORD</label>
                          <input name="wifi_password" id="to" placeholder="Enter Your password" />
                        </div>
                        <div>
                          <button type="submit">Save the wifi info</button>
                        </div>
                      </form>
                <p>Connected WIFI is {ssid}</p>
              </body>
            </html>
            """
    return str(html)
    
def decode_wifi_id_pass(id,passw):
    special_chars = {
        '%21': '!',
        '%23': '#',
        '%24': '$',
        '%26': '&',
        '%27': "'",
        '%28': '(',
        '%29': ')',
        '%2A': '*',
        '%2B': '+',
        '%2C': ',',
        '%2F': '/',
        '%3A': ':',
        '%3B': ';',
        '%3D': '=',
        '%3F': '?',
        '%40': '@',
        '%5B': '[',
        '%5D': ']',
        '%7B': '{',
        '%7D': '}'
    }

    

    encoded_str_id = id
    encoded_str_pass = passw

    # Use regular expressions to replace percent-encoded sequences with their corresponding characters
    encoded_str_id = encoded_str_id.replace("+", " ")
    for key, value in special_chars.items():
        encoded_str_id = re.sub(key, value, encoded_str_id)
        encoded_str_pass = re.sub(key, value, encoded_str_pass)
    return([encoded_str_id,encoded_str_pass])
    
    
    

def serve(connection):

    pico_led.off()

    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        print(request)
        
#         for i in request.split():
#             global curr_setpoints
#             global curr_values
#             global num_sensors
#             global pump_state
#             if "num_sensors" in i:
#                 data = i.split("num_sensors")[1]
#                 print(data[1:-1]) #number of sensors
#                 num_sensors = int(data[1:-1])
#                 curr_setpoints=[i-i for i in range(num_sensors)]
#                 curr_values = [i-i for i in range(num_sensors)]
#                 pump_state = [i-i for i in range(num_sensors)]
#                 print(data)
# 
#             elif "moist_sensor_" in i:
#                 data = i.split("moist_sensor_")[1]
#                 print(data[:-1].split("=")) #sensor id and setpoints
#                 
#                 sensor_id , sensor_setpoint = data[:-1].split("=")
#                 
#                 curr_setpoints[int(sensor_id)] = int(sensor_setpoint)
#                 
#                 print(data)
#                 print(curr_setpoints)
#             
#             elif "wifi_ssid" in i:
#                 
#                 data = i.split("wifi_ssid")[1]
#                 data = data.split("&wifi_password=")
#                 print(data[0][1:],data[1][0:-1]) #wifi id and password
#                 
#                 wifi_id,wifi_pass = decode_wifi_id_pass(data[0][1:],data[1][0:-1]) #decoded wifi
#                 print(wifi_id,wifi_pass)
#                 with open('wifi.txt', 'w') as f:
#                     f.write(wifi_id + '\n')
#                     f.write(wifi_pass + '\n')
#                     print("done writing")
#                 
#                 
#         try:
#             request = request.split()[1]
#             print(request)
#         except IndexError:
#             pass
#         global  control_state
#         if request == '/automatic?':
#             pico_led.on()
#             control_state = 'ON'
#         elif request =='/manual?':
#             pico_led.off()
#             control_state = 'OFF'
#         
#         for i in range(num_sensors):
#             
#             if request == f'/pump_{i}_on':
#                 if control_state =='OFF':
#                     pump_state[i] = 1
#                     print(f'/pump_{i}_on ------------' )
#             elif request == f'/pump_{i}_off':
#                 if control_state == "OFF":
#                     pump_state[i] = 1
#                     print(f'/pump_{i}_off ------------' )
#         
#                 
#             
#             
#         temperature = pico_temp_sensor.temp
        html = webpage()
        client.send(html)
        client.close()
        
        
try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()