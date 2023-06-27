'''
Controlling an ST7735 color display with a Raspberry Pi Pico
More info:
https://electroniqueamateur.blogspot.com/2021/05/ecran-couleur-spi-st7735-et-raspberry.html
'''

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
tft.text((18, 15), "Demonstration ST7735", TFT.WHITE, sysfont, 1)

# drawing a straight line
tft.line((20, 35),(140, 35), TFT.GREEN) # start point, end point, color

#tracé of a solid rectangle
tft. fillrect((20,50), (50,50), TFT.BLUE) # starting point, width, height, color

# drawing a rectangle outline
tft.rect((20,50), (50,50), TFT.CYAN) # starting point, width, height, color

# setting an individual pixel (small dot in the center of the square
tft.pixel((45,75), TFT.WHITE)

# drawing a solid circle
tft.fillcircle((120, 73), 25, TFT.RED)

# drawing a circle outline
tft.circle((120, 73), 25, TFT.YELLOW)

# setting an individual pixel (small dot in the center of the circle
tft.pixel((120, 73), TFT.WHITE)