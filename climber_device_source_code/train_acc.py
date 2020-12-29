        
import time
import board
import busio
import sys
import adafruit_adxl34x
from datetime import datetime
import requests
import json

''' This code is used to train the SVM to recognize climbing,walking and resting motions'''
def main(label,f):
    
    i2c = busio.I2C(board.SCL, board.SDA)
    accelerometer = adafruit_adxl34x.ADXL345(i2c)

    count = 0
    x = []
    y = []
    z = []
    
    time.sleep(3)
    print('go')
    while True:
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        while count < 100:
            x_,y_,z_ = accelerometer.acceleration
            x.append(x_)
            y.append(y_)
            z.append(z_)
            count += 1
            time.sleep(0.01)
            
        data_ = json.dumps({'timestamp':timestamp,'x' : x, 'y' : y, 'z': z, 'label' : label}) 
        r = requests.post("http://ec2-3-87-228-201.compute-1.amazonaws.com:5000", data = data_)
        f.write(data_)
        f.write('\n')
        print(r)
        count = 0
        x,y,z = [],[],[]
        
        
if __name__ == '__main__':
    try:
        f = open("log.txt", "a+")
        main(sys.argv[1],f)
    except KeyboardInterrupt:
        f.close()