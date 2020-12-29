import time
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x

CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433)
    print('success')
except RuntimeError as error:
    print('error')


while True:
    packet = None
    
    packet = rfm9x.receive()
    if packet is not None:
        prev_packet = packet
        packet_text = str(prev_packet, "utf-8")
        hour = packet_text[0:2]
        minute = packet_text[2:4]
        second = packet_text[4:6]

        lat = packet_text[6:18]
        lon = packet_text[18:30]
        alt = packet_text[30:40]

        data ={"hour":hour,"minute":minute,"second":second,"lat":lat,"lon":lon,"alt":alt}

        print(data)
