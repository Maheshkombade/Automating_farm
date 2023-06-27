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
control_pump_state = [0,0,0]
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

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_{i}" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                    </form>
                    </tr>"""
        
    return out_str


def make_string_pumps(n,control_state_pump): #curr_value list of n sensors
    print(control_pump_state)
    out_str_pump = ""
    for i in range(n):
        out_str_pump+=f""" <tr>
                      <td>Pump_{i+1}</td>
                    
                      <td name="currentstate">{"ON" if control_state_pump[i]==1 else "OFF"}</td>

                      <form action="./pump_{i}_on" method="POST">
                      
                      <td><button type="submit">ON</button></td>
                        </form>

                        <form action="./pump_{i}_off" method="POST">
                      
                      <td><button type="submit">OFF</button></td>
                        </form>

                    </tr>"""
        
    return out_str_pump


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
    global control_pump_state
    threshold = 0.2
    while True:
        lock.acquire()
        for i in range(len(curr_setpoints)):
            
            read_sensors()
            error = curr_setpoints[i]-curr_values[i]
            
            if control_state=="ON":
                for i in range(len(pump_state)):
                    pump_state[i]=0
                if error > threshold:
                    control_pump_state[i] = 1
                    relay_outputs[i](0)
                    print(f"turn on the motor or solenoid {i}")
                elif error< threshold:
                    control_pump_state[i] = 0
                    #turn off the motor or solenoid
                    relay_outputs[i](1)
                    print(f"turn off the motor or solenoid {i}")
            elif control_state=="OFF":
                control_pump_state= pump_state.copy()
                if pump_state[i]==1:
                    relay_outputs[i](0)

                elif pump_state[i]==0:
                    relay_outputs[i](1)
            print(error,"control state ",control_pump_state)
            print("pump state ",pump_state)
        lock.release()
      
        utime.sleep(1)




def webpage():
    global num_sensors
    global curr_values
    global curr_setpoints
    global control_pump_state
    global control_state
    
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

                    <p>{"Automatic" if control_state=="ON" else "Manual"}</p>
              
              
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

                  {make_string_pumps(num_sensors,control_pump_state)}
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
    
def decode_wifi_id_pass(id):
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


    # Use regular expressions to replace percent-encoded sequences with their corresponding characters
    if "+" in encoded_str_id:
        encoded_str_id = encoded_str_id.replace("+", " ")
    for key, value in special_chars.items():
        encoded_str_id = re.sub(key, value, encoded_str_id)
       
    return(encoded_str_id)
    
    
    
def process_request(request):

    req = request.split()[1]
    req = req.split("?")
    data_dict = {}
    if len(req)>1 and req[1]!="":
        print(req[0])
        data=req[1].split("&")

        if len(data)==2:

            id_list = data[0].split("=")
            data_dict[id_list[0]] = decode_wifi_id_pass(id_list[1])
            pass_wd_list = data[1].split("=")
            data_dict[pass_wd_list[0]] = decode_wifi_id_pass(pass_wd_list[1])
            
            return ["wifi",data_dict]

        elif len(data)==1:

            id_list = data[0].split("=")
            data_dict[id_list[0]] = decode_wifi_id_pass(id_list[1])
            
            return ["value_pair",data_dict]
    if (len(req)>1 and req[1]=="") or (len(req)==1):

        return ["one",req[0]]

def serve(connection):
    global num_sensors
    global curr_setpoints
    global curr_values
    global pump_state
    global control_state
    global control_pump_state
    pico_led.off()

    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)

        data_type , data = process_request(request)

        if data_type =="wifi":
            if list(data.values())[0]=="":
                pass
            else:
                wifi_id = data['wifi_ssid']
                wifi_pass = data['wifi_password']
                print(wifi_id,wifi_pass)
                with open('wifi.txt', 'w') as f:
                    f.write(wifi_id + '\n')
                    f.write(wifi_pass + '\n')
                    print("done writing")
        
        lock.acquire()
        if data_type =="value_pair":
            key = list(data.keys())[0]
            if key =="num_sensors":
                
                num_sensors = int(data["num_sensors"])
                print(num_sensors)

                curr_setpoints=[i-i for i in range(num_sensors)]
                curr_values = [i-i for i in range(num_sensors)]
                pump_state = [i-i for i in range(num_sensors)]
                control_pump_state=[i-i for i in range(num_sensors)]
                print(curr_setpoints)
                print(curr_values)
                print(pump_state)
                

            elif "moist_sensor" in key:
                
                print(key[13:])
                curr_setpoints[int(key[13:])] = int(list(data.values())[0])
                print(curr_setpoints)
               
        elif data_type =="one":
        
            if data=="/manual":
                
                control_state ="OFF"
            elif data=="/automatic":
                control_state="ON"
            elif "pump_" in data:

                index =int(data.split("_")[1])
                value = data.split("_")[2]
                pump_state[index]=0 if value=="off" else 1
                print("here is the inside pump state ",pump_state)
            print(control_state)
           
            

      
        html = webpage()
        lock.release()
        client.send(html)
        client.close()

        print("one cycle complete")
        
        
try:
    _thread.start_new_thread(control_system,())
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()




