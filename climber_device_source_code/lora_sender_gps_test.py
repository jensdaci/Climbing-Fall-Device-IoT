import time
import board
import busio
import serial 
import adafruit_gps

from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x

#https://learn.adafruit.com/adafruit-ultimate-gps/circuitpython-python-uart-usage

CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

#uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=3000)

gps = adafruit_gps.GPS(uart, debug=False)

gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")

gps.send_command(b"PMTK220,1000")

last_print = time.monotonic()

while True:
    gps.update()
    current = time.monotonic()
    if current - last_print >= 60.0:
        last_print = current
        if not gps.has_fix:
            print("Waiting for fix...")
            continue

        data = ''
        
        device_id = '1'
        status = '0'
        hour = str(gps.timestamp_utc.tm_hour).zfill(2)  
        minute = str(gps.timestamp_utc.tm_min).zfill(2)  
        second = str(gps.timestamp_utc.tm_sec).zfill(2)
        
        data += hour + minute + second
        
        data += ("{0:.6f}".format(gps.latitude)).zfill(12)

        data += ("{0:.6f}".format(gps.longitude)).zfill(12)

        data += ("{0:.2f}".format(gps.altitude_m)).zfill(10)
        
        data += ("{}".format(status)).zfill(1)
        data += ("{}".format(device_id)).zfill(4)

        print(data)
        try:
            rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433)
        except RuntimeError as error:
            print('radio error')
    
        data_b=bytes(data,"utf-8")

        
        rfm9x.send(data_b)
        print("data sent")
        
                       
