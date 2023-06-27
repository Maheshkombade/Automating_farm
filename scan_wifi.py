import utime
import network

from time import sleep

import machine

wlan=network.WLAN(network.STA_IF)
wlan.active(True)
accesspoints = wlan.scan()


from ST7735 import TFT # https://github.com/boochow/MicroPython-ST7735
from sysfont import sysfont # https://github.com/GuyCarver/MicroPython/blob/master/lib/sysfont.py 
from machine import SPI,Pin

spi = SPI(0, baudrate=20000000, polarity=0, phase=0, sck=Pin(6), mosi=Pin(7), miso=Pin(4))
tft=TFT(spi,13,14,15) # AO: GP 13, RST: GP 14, CS: GP 15
tft.initr()
tft.rgb(True) # try False if wrong colors

tft.rotation(3) # portrait (0 or 2) or landscape (1 or 3)

tft.fill(TFT.BLACK) # black background

# writing text
tft.text((0, 0), "Wifi Available", TFT.WHITE, sysfont, 1)
utime.sleep(1)
#tft.text((0, 0), "                     ", TFT.WHITE, sysfont, 1)

row_index = 0
for i,ap in enumerate(accesspoints):
    
    tft.text((0,10*(i+1)), str(i)+" "+str(ap[0],'UTF-8'), TFT.WHITE, sysfont, 1)
    print(ap[0])
    row_index = 10*(i+1)
    
    if i>2:
        break
    utime.sleep(1)
    
tft.text((0,row_index+10),"Choose the wifi",TFT.RED,sysfont,1)
utime.sleep(1)
print("choose the wifi")

wifi_index = int(input())

wifi= str(accesspoints[wifi_index][0],'UTF-8')

tft.text((0,row_index+20),"You choose "+wifi,TFT.GREEN,sysfont,1)

utime.sleep(1)
ssid = wifi
password = ''




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


try:
    ip = connect()
    tft.text((0,row_index+30),"Your IP address is "+ip,TFT.BLUE,sysfont,1)
    for i in range(10):
        tft.text((0,row_index+60),str(i),TFT.WHITE,sysfont,1)
        utime.sleep(1)
        tft.text((0,row_index+60),"   ",TFT.WHITE,sysfont,1)
        
    
except KeyboardInterrupt:
    machine.reset()

    