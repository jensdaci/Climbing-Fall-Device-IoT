import time
import board
import busio
import sys
import adafruit_adxl34x
from datetime import datetime
import requests
import json

'''This code is used to tset whether the SVM model is correctly classifying motions'''

def main():
    
    i2c = busio.I2C(board.SCL, board.SDA)
    accelerometer = adafruit_adxl34x.ADXL345(i2c)

    count = 0
    x = []
    y = []
    z = []
    
    time.sleep(1)
    print('go')
    while True:
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        while count < 500:
            x_,y_,z_ = accelerometer.acceleration
            x.append(x_)
            y.append(y_)
            z.append(z_)
            count += 1
            time.sleep(0.01)
            
        data_ = json.dumps({'timestamp':timestamp,'x' : x, 'y' : y, 'z': z}) 
        r = requests.post("http://ec2-3-87-228-201.compute-1.amazonaws.com:5001", data = data_)
        
        data = r.content
        encoding = 'utf-8'
        
        str_data = json.loads(data.decode(encoding))#.replace("'", '"'))

        print(str_data)
        
        x,y,z = [],[],[]
        count = 0 
        
if __name__ == '__main__':
    main()
