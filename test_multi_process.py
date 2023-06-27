#Importing libraries
import _thread
from time import sleep
from machine import SPI, ADC, Pin
import re
import network
import socket
import machine


from ST7735 import TFT # https://github.com/boochow/MicroPython-ST7735
from sysfont import sysfont # https://github.com/GuyCarver/MicroPython/blob/master/lib/sysfont.py 

#Declaring global variables
spi = SPI(0, baudrate=20000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
tft=TFT(spi,13,14,15) # AO: GP 13, RST: GP 14, CS: GP 15
tft.initr()
tft.rgb(True) # try False if wrong colors

tft.rotation(3) # portrait (0 or 2) or landscape (1 or 3)

tft.fill(TFT.BLACK) # black background

# writing text
#tft.text((0, 0), "Wifi Available", TFT.WHITE, sysfont, 1)
sleep(1)



#Sensors
soil_sensors = [ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26)),ADC(Pin(26))] # Soil moisture Pin
#Relay signal pins
relay_outputs = [Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT),Pin(18,Pin.OUT)]
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

    wifi_list =[["Farm","123"],[ssid,password]]

    for i in range(len(accesspoints)):
        wifi_list.append([str(accesspoints[i][0],'UTF-8'),'' ])
    
    for i in range(len(wifi_list)):

        wlan.connect(wifi_list[i][0], wifi_list[i][1])
        tft.text((0,10*(i+1)), str(i)+" "+wifi_list[i][0], TFT.WHITE, sysfont, 1)
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

    html = f'''

    <!DOCTYPE html>
            <html lang="en-us">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width">
                <meta http-equiv="refresh" content="10" />
                
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

                    {"Automatic"if control_state else "Manual"}
              
              
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

                    <tr>
                      <td>Moisture sensor_1</td>
                      <td name = "current value">{curr_values[0]}</td>
                      <td name="currentsetpoints">{curr_setpoints[0]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_1" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_2</td>
                      <td name = "current value">{curr_values[1]}</td>
                      <td name="currentsetpoints">{curr_setpoints[1]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_2" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    
                    <tr>
                      <td>Moisture sensor_3</td>
                      <td name = "current value">{curr_values[2]}</td>
                      <td name="currentsetpoints">{curr_setpoints[2]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_3" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_4</td>
                      <td name = "current value">{curr_values[3]}</td>
                      <td name="currentsetpoints">{curr_setpoints[3]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_4" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_5</td>
                      <td name = "current value">{curr_values[4]}</td>
                      <td name="currentsetpoints">{curr_setpoints[4]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_5" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    <tr>
                      <td>Moisture sensor_6</td>
                      <td name = "current value">{curr_values[5]}</td>
                      <td name="currentsetpoints">{curr_setpoints[5]}</td>

                      <form action="./setpoints" method="get">
                      <td><input type="text" name="moist_sensor_6" placeholder="new setpoints" id=""></td>
                      <td><button type="submit">submit</button></td>
                      </form>
                    </tr>
                    
                    
                  <br>
                  <br>
                  <tr>
                    <td>Pump_1</td>
                  
                    <td name="currentstate">{"ON" if pump_state[0] else "OFF" }</td>

                    <form action="./pump_1_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_1_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_2</td>
                  
                    <td name="currentstate">{"ON" if pump_state[1] else "OFF" }</td>

                    <form action="./pump_2_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_2_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>

                  <tr>
                    <td>Pump_3</td>
                  
                    <td name="currentstate">{"ON" if pump_state[2] else "OFF" }</td>

                    <form action="./pump_3_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_3_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_4</td>
                  
                    <td name="currentstate">{"ON" if pump_state[3] else "OFF" }</td>

                    <form action="./pump_4_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_4_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>
                  <tr>
                    <td>Pump_5</td>
                  
                    <td name="currentstate">{"ON" if pump_state[4] else "OFF" }</td>

                    <form action="./pump_5_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_5_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>

                  <tr>
                    <td>Pump_6</td>
                  
                    <td name="currentstate">{"ON" if pump_state[5] else "OFF" }</td>

                    <form action="./pump_6_on" method="POST">
                    
                    <td><button type="submit">ON</button></td>
                      </form>

                      <form action="./pump_6_off" method="POST">
                    
                    <td><button type="submit">OFF</button></td>
                      </form>

                  </tr>
                  
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
        

        for i in range(num_sensors):
            curr_values[i] = soil_sensors[i].read_u16()
            error = curr_setpoints[i]-curr_values[i]

            if (control_state ==1) and (error>threshold):
                relay_outputs[i](0)
                pump_state[i]=1
            elif (control_state ==1) and (error<threshold):
                relay_outputs[i](1)
                pump_state[i]=0
            elif control_state ==0:
                pump_value = 0 if pump_state[i]==1 else 0
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
        
        tft.text((0, 0), "Scanning Wifi ...", TFT.WHITE, sysfont, 1)
        connection = connect(ssid,password)
        print(used_ip,used_wifi)

        sleep(1)
        tft.fill(TFT.BLACK) # black background
        tft.text((4, 5), "Welcome to farmAuto", TFT.WHITE, sysfont, 1)
        tft.text((0,15),"Used wifi is "+used_wifi,TFT.GREEN,sysfont,1)
        tft.text((0,35),"Your IP address is "+used_ip,TFT.BLUE,sysfont,1)

        if connection !=None:
            serve(connection)
        

    except KeyboardInterrupt:
        machine.reset()  
 
    
    













