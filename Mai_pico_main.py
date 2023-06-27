#Importing libraries
import _thread
from time import sleep
from machine import  ADC, Pin
import re
import network
import socket
import machine
from machine import I2C
from ssd1306 import SSD1306_I2C

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)




# writing text
#tft.text((0, 0), "Wifi Available", TFT.WHITE, sysfont, 1)
sleep(1)
oled.text("Smart Agri", 0, 0)

oled.show()
#Sensors
soil_sensor_pin = ADC(Pin(26)) # Soil moisture Pin

#soil_sensors = [0,0,0,0]
#Relay signal pins
relay_outputs = [Pin(12,Pin.OUT),Pin(11,Pin.OUT),Pin(10,Pin.OUT),Pin(9,Pin.OUT)]
multiplexer = [Pin(19,Pin.OUT),Pin(20,Pin.OUT),Pin(21,Pin.OUT)] 
#Lock for multiprocessing
sLock = _thread.allocate_lock()

#wifi info
ssid =""
password = ""

used_wifi=''
used_ip = ''
#number of sensors with default value 3
num_sensors=3
#current values of the sensors
curr_values=[0,0,0,0,0,0]
#current sensors of the sensors
curr_setpoints=[0,0,0,0,0,0]
#Current Pump state
# 0 -> OFF , 1 -> ON
pump_state=[0,0,0,0,0,0]
#Controlled state of the pump - automatic controlled
# 0 -> OFF , 1 -> ON

#State of control system - either automatic and manual
# 0 -> OFF , 1 -> ON
control_state = 0 

a=0
# First we need to get the name of wifi and password of the wifi
#to connect to the network

#Read the ssid and password

with open('wifi.txt', 'r') as f:
    # Read the first line and remove the newline character
    ssid = f.readline().rstrip('\n')
    # Read the second line and remove the newline character
    password = f.readline().rstrip('\n')
print("Connecting to Wifi name ",ssid)


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
def connect(ssid,password):
    global wlan 
    global used_ip
    global used_wifi
    global tft
    accesspoints = wlan.scan()

    sleep(0.5)

    wifi_list =[["Farm",""],[ssid,password]]

    for i in range(len(accesspoints)):
        wifi_list.append([str(accesspoints[i][0],'UTF-8'),'' ])
    
    for i in range(len(wifi_list)):

        wlan.connect(wifi_list[i][0], wifi_list[i][1])
        #tft.text((0,10*(i+1)), str(i)+" "+wifi_list[i][0], TFT.WHITE, sysfont, 1)
        count = 0
        while wlan.isconnected() == False:
            print('Waiting for connection...')
            sleep(0.5)
            count+=1
            if count>20:
                print("10 secs pass away!!")
                break
        
               
        if wlan.isconnected() != False:  
            used_wifi = wifi_list[i][0]
            break    

    if wlan.isconnected() != False:
        ip = wlan.ifconfig()[0]
        used_ip = ip
        print(f'Connected on {ip}')
        sleep(1)
        address = (ip, 80)
        connection = socket.socket()
        connection.bind(address)
        connection.listen(1)
        return connection
    else:
        return None

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
    

def webpage():

    global num_sensors
    global curr_setpoints
    global curr_values
    global pump_state
    global control_state
 
    global ssid
    global used_ip

    html = f'''

    <!DOCTYPE html>
            <html lang="en-us">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width">
                <meta http-equiv="refresh" content="10;URL=''"/>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
                <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Trirong">
                <title>Smart Irrigo</title>
                <style>
                  body {{font-family: "Trirong", serif;}}
                </style>
               
              </head>
              <body>
              <div class="container-fluid bg-secondary row">
                <h1 class="text-center py-5 fw-bold">Smart Irrigo</h1>
                    <!-- <h2>Automatic or Manual</h2> -->

                    <form class="col-md-3 offset-md-2" action="./automatic">
                        <input class="btn btn-primary" type="submit" value="Automatic" />
                    </form>

                    <form class="col-md-3 offset-md-1" action="./manual">
                        <input class="btn btn-primary" type="submit" value="Manual" />
                    </form>
                    <br>
                    {"Automatic"if control_state else "Manual"}
              
                    
                <form class="col-md-5 mt-5" action="./sensors" method="get">
                    <div class="input-group mb-3">
                      <label class="input-group-text" for="say">Number of Moisture sensor</label>
                      <input class="form-control" name="num_sensors" id="say" placeholder="Enter number 1 to 6" />
                      <div>
                        <button class="btn border" type="submit">Submit</button>
                      </div>
                    </div>
                    
                  </form>
                  
                  <br><br><br><br>
                  Number of active sensors is {num_sensors}
                  <br>
                </div>
                <div class="container">
                <!-- <h1>Table</h1> -->
                <table class="table table-hover table-striped">
                    <tr class="fw-bolder">
                      <td>Attributes</td>
                      <td>Current values</td>
                      <td>Current-Setpoints</td>
                      <td>New-Setpoints</td>
                      <td>Submit</td>
                    </tr>

                    <tr>
                      <td>Moisture sensor_1</td>
                      <td name = "current value">{int(curr_values[0])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[0]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_1" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_2</td>
                      <td name = "current value">{int(curr_values[1])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[1]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_2" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    
                    <tr>
                      <td>Moisture sensor_3</td>
                      <td name = "current value">{int(curr_values[2])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[2]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_3" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_4</td>
                      <td name = "current value">{int(curr_values[3])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[3]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_4" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_5</td>
                      <td name = "current value">{int(curr_values[4])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[4]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_5" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_6</td>
                      <td name = "current value">{int(curr_values[5])}%</td>
                      <td name="currentsetpoints">{curr_setpoints[5]}%</td>

                      <form action="./setpoints" method="get">
                      <td><input class="form-control" type="text" name="moist_sensor_6" placeholder="new setpoints" id=""></td>
                      <td><button class="btn border" type="submit">submit</button></td>
                      </form>
                    </tr>
                    
                    
                  <br>
                  <br>
                  <tr>
                    <td>Pump_1</td>
                  
                    <td name="currentstate">{"ON" if pump_state[0] else "OFF" }</td>

                    <form action="./pump_1_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_1_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_2</td>
                  
                    <td name="currentstate">{"ON" if pump_state[1] else "OFF" }</td>

                    <form action="./pump_2_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_2_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>

                  <tr>
                    <td>Pump_3</td>
                  
                    <td name="currentstate">{"ON" if pump_state[2] else "OFF" }</td>

                    <form action="./pump_3_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_3_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_4</td>
                  
                    <td name="currentstate">{"ON" if pump_state[3] else "OFF" }</td>

                    <form action="./pump_4_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_4_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_5</td>
                  
                    <td name="currentstate">{"ON" if pump_state[4] else "OFF" }</td>

                    <form action="./pump_5_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_5_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>

                  <tr>
                    <td>Pump_6</td>
                  
                    <td name="currentstate">{"ON" if pump_state[5] else "OFF" }</td>

                    <form action="./pump_6_on" method="POST">
                    
                    <td><button class="btn border" type="submit">ON</button></td>
                      </form>

                      <form action="./pump_6_off" method="POST">
                    
                    <td><button class="btn border" type="submit">OFF</button></td>
                      </form>

                  </tr>
                  
                  </table>
                </div>
                <div class="container">
                <form action="./wifi" method="get">
                    <div class="mb-3">
                      <label for="say" class="form-label">WIFI SSID</label>
                      <input class="form-control" name="wifi_ssid" id="say" placeholder="Enter Your SSID" />
                    </div>
                    <div class="mb-3">
                      <label for="to" class="form-label">WIFI PASSWORD</label>
                      <input class="form-control" name="wifi_password" id="to" placeholder="Enter Your password" />
                    </div>
                    <div>
                      <button class="btn border" type="submit">Save the wifi info</button>
                    </div>
                  </form>
                <p>Connected WIFI is {ssid}</p>
              </div>
                <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js" integrity="sha384-IQsoLXl5PILFhosVNubq5LC7Qb9DXgDA9i+tQ8Zj3iwWAwPtgFTxbJ8NT4GN1R8p" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.min.js" integrity="sha384-cVKIPhGWiC2Al4u+LWgxfKTRIcfu0JTxR+EQDz/bgldoEyl4H0zUF0QKbrJ0EcQF" crossorigin="anonymous"></script>
              </body>
            </html>
    '''
    return html

def serve(connection):
    global a
    global num_sensors
    global curr_setpoints
    global curr_values
    global pump_state
    global control_state
    

    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        #retrive data and data type from socket
        data_type , data = process_request(request)

        ##############################
        #write the wifi data to file for future use
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

        ##################################

        # Acquire lock so that synchronous data is transfered
        sLock.acquire()

        #####################################
        # Get the data of number of senosrs

        if data_type =="value_pair":
            key = list(data.keys())[0]
            if key =="num_sensors":
                
                num_sensors = int(data["num_sensors"])
                print("Number of registered sensors",num_sensors)


            ##################################
            #Get Moisture sensors setpoints

            elif "moist_sensor" in key:
                
                print("Index -> ",int(key[13:]))
                print("value -> ",list(data.values())[0])
                curr_setpoints[int(key[13:])-1] = int(list(data.values())[0])
                print("Current setpoints of the sensors \n",curr_setpoints)
            ##########################################
        #Check manual or pump command is called.
        elif data_type =="one":
        
            if data=="/manual":
                
                control_state =0
                print("System is set to manual ")
            elif data=="/automatic":
                control_state=1
                print("System is set to automatic")

            elif "pump_" in data:

                index =int(data.split("_")[1])
                value = data.split("_")[2]
                if control_state==0:
                    pump_state[index-1]=0 if value=="off" else 1
                print(data," is called")
                print("here is the inside pump state ",pump_state)
            


        html = webpage()

        try:
            client.sendall(html)
            sleep(0.0001)
            print(data,data_type)
            client.close()

        except KeyboardInterrupt:
            machine.reset() 
        
        a+=1
        
        print("Process 2 ",a)
        sLock.release()





def core_program():
    global a
    global num_sensors
    global relay_outputs
    global curr_setpoints
    global curr_values
    global pump_state
    global control_state
    
    global soil_sensors
    threshold = 0.2
    while  True:
        sLock.acquire()
        print("moisture value is ", curr_values[0])
        for i in range(len(curr_setpoints)):
            if i<num_sensors-1:
                continue
            else:
                curr_setpoints[i] =0
                curr_values[i]=0
                pump_state[i]=0
        for i in range(num_sensors):
            
            if i ==0:
                multiplexer[0](0)
                multiplexer[1](0)
                multiplexer[2](0)
            elif i ==1:
                multiplexer[0](1)
                multiplexer[1](0)
                multiplexer[2](0)
            elif i ==2:
                multiplexer[0](0)
                multiplexer[1](1)
                multiplexer[2](0)
            elif i ==3:
                multiplexer[0](1)
                multiplexer[1](1)
                multiplexer[2](0)
            elif i ==4:
                multiplexer[0](0)
                multiplexer[1](0)
                multiplexer[2](1)
                
            curr_values[i] = ((43727-soil_sensor_pin.read_u16())*100)/22446
            error = curr_setpoints[i]-curr_values[i]

            if (control_state ==1) and (error>threshold) and i<len(relay_outputs):
                relay_outputs[i](0)
                pump_state[i]=1
            elif (control_state ==1) and (error<threshold)and i<len(relay_outputs):
                relay_outputs[i](1)
                pump_state[i]=0
            elif control_state ==0 and i<len(relay_outputs):
                pump_value = 0 if pump_state[i]==1 else 1
                relay_outputs[i](pump_value)
            else:
                continue
       
        
        a+=1
        
      
        if a>1000:
            a=0
        
        sLock.release()
        
        sleep(1)
        
        
_thread.start_new_thread(core_program,())


while True:
    
    try:
        
        
        connection = connect(ssid,password)
        print(used_ip,used_wifi)
        
        oled.text(f"Wifi-{used_wifi}", 0, 20)
        oled.text(f"ip {used_ip}", 0, 40)
        oled.show()

        sleep(1)


        if connection !=None:
            serve(connection)
        

    except KeyboardInterrupt:
        machine.reset()  
 
    
    













