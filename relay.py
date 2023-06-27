from machine import Pin

relay1 =Pin(12,Pin.OUT)
relay2 =Pin(11,Pin.OUT)


from time import sleep

while True:
    print("turn on relay 1")
    relay1(0)
    relay2(1)
    
    sleep(10)
    print("turn on relay 2")
    relay1(1)
    relay2(0)

    sleep(10)