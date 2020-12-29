import time
import board
import busio
import sys
import adafruit_adxl34x
from datetime import datetime
import requests
import json
import serial 
import adafruit_gps
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x
from joblib import dump, load
import numpy as np
import pandas as pd
from sklearn import svm


''' Model handler for the web server communication '''
def get_prediction(x,y,z,clf):
    
    # Use this code for aws model returns
    # timestamp = datetime.now().strftime("%H:%M:%S")
    # data_ = json.dumps({'timestamp':timestamp,'x' : x, 'y' : y, 'z': z}) 
    # r = requests.post("http://ec2-3-87-228-201.compute-1.amazonaws.com:5001", data = data_)

    # data = r.content
    # encoding = 'utf-8'
    # str_data = json.loads(data.decode(encoding))
    
    # return str_data["prediction"]
    
    #On device model returns
    
    
    N=2
    data = {}
    
    x_ = [abs(float(i)) for i in x]
    y_ = [abs(float(i)) for i in y]
    z_ = [abs(float(i)) for i in z]
    
    # Split into Frames
    data['x'] = np.split(np.array(x_),N)
    data['y'] = np.split(np.array(y_),N)
    data['z'] = np.split(np.array(z_),N)
    
    # FFT
    data['x_fft'] = [np.real(np.fft.rfft(i)) for i in data['x']]
    data['y_fft'] = [np.real(np.fft.rfft(i)) for i in data['y']]
    data['z_fft'] = [np.real(np.fft.rfft(i)) for i in data['z']]


    x = []
    y = []
    z = []
    
    # Concat consecutive frames
    for i in range(1,len(data['x'])):
        x.append(np.concatenate([data['x'][i],data['x'][i-1]]))
        y.append(np.concatenate([data['y'][i],data['y'][i-1]]))
        z.append(np.concatenate([data['z'][i],data['z'][i-1]]))

    x_fft = []
    y_fft = []
    z_fft = []
    for i in range(1,len(data['x'])):
        x_fft.append(np.concatenate([data['x_fft'][i],data['x_fft'][i-1]]))
        y_fft.append(np.concatenate([data['y_fft'][i],data['y_fft'][i-1]]))
        z_fft.append(np.concatenate([data['z_fft'][i],data['z_fft'][i-1]]))

    test_data = []
    test_data += [np.mean(np.abs(i)) for i in x_fft]
    test_data += [np.mean(np.abs(i)) for i in y_fft]
    test_data += [np.mean(np.abs(i)) for i in z_fft]
    
    test_data += [np.std(i) for i in x_fft]
    test_data += [np.std(i) for i in y_fft]
    test_data += [np.std(i) for i in z_fft]
        
    test_data += [np.max(np.abs(i)) for i in x]
    test_data += [np.max(np.abs(i)) for i in y]
    test_data += [np.max(np.abs(i)) for i in z]
    
    test_data += [np.sum(np.square(i))/(2*N) for i in x]
    test_data += [np.sum(np.square(i))/(2*N) for i in y]
    test_data += [np.sum(np.square(i))/(2*N) for i in z]
    
    pred = clf.predict(np.array(test_data).reshape(1, -1)) 
    
    return pred
    


''' Get the accelerometer data for 5 seconds, send to the model handler,
and return the prediction to the main function '''        
def read_motion(accelerometer,free_fall_alert,alert,alert_count,count,clf):
    x,y,z = [],[],[]
    
    
    while count < 500:
        
        if free_fall_alert and (alert_count == 0) and accelerometer.events["freefall"]:
            print("free_fall_detected")
            alert = 1
            
        x_,y_,z_ = accelerometer.acceleration
        x.append(x_)
        y.append(y_)
        z.append(z_)
        count += 1
        time.sleep(0.01)
        
    prediction = get_prediction(x,y,z,clf)
    
    return alert,alert_count,prediction

''' Get the users coordinates using the GPS device '''
def get_coordinates(gps):
    now = datetime.now()
    hour = str(now.hour).zfill(2)  
    minute = str(now.minute).zfill(2) 
    second = str(now.second).zfill(2)
    
    time = hour + minute + second
    
    if gps.has_fix:
        lat = ("{0:.6f}".format(gps.latitude)).zfill(12)
        lon = ("{0:.6f}".format(gps.longitude)).zfill(12)
        alt = ("{0:.2f}".format(gps.altitude_m)).zfill(10)
    else:
        lat = ("{0:.6f}".format(0)).zfill(12)
        lon = ("{0:.6f}".format(0)).zfill(12)
        alt = ("{0:.2f}".format(0)).zfill(10)
    
    return time,lat,lon,alt


''' Handler for sending the coordinates and status through LoRa '''
def lora_send(data,spi,CS,RESET):
    
    try:
        rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433)
    except RuntimeError as error:
        print('radio error')

    data_b=bytes(data,"utf-8")
    rfm9x.send(data_b)
    
    print("data sent")
    return


def main():
    #get model
    #clf = load('svm.joblib')
    clf = 0
    #initialize variables
    free_fall_alert = 0
    alert = 0
    alert_count = 0
    history = []
    device_id = '1'
    status = '0'
    lora_counter = 0
    
    # Initialize LoRa
    CS = DigitalInOut(board.CE1)
    RESET = DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    
    #Initialize GPS
    uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=3000)
    gps = adafruit_gps.GPS(uart, debug=False)
    gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
    gps.send_command(b"PMTK220,1000")
    last_print = time.monotonic()

    # Initialize the accelerometer
    i2c = busio.I2C(board.SCL, board.SDA)
    accelerometer = adafruit_adxl34x.ADXL345(i2c)

    time.sleep(1)
    print('Go')
    
    while True:
        
        #Connect the GPS
        gps.update()
        current = time.monotonic()
        if current - last_print >= 10.0:
           last_print = current
           if not gps.has_fix:
               print("Waiting for fix...")
               continue
           
        #Set the free fall detection if the user is climbing
        if (free_fall_alert) == 1 and (0 == alert_count):
            accelerometer.enable_freefall_detection(threshold=12, time=30)
            print("Sensor: Free fall detection active")
        
        # Get the current motion reads
        alert,alert_count,prediction = read_motion(accelerometer,free_fall_alert,alert,alert_count,0,clf)
        
        print("Prediction: ", prediction)
        history.append(prediction)
        
        # Trim short history for efficient memory usage
        if len(history) > 10:
            history = history[1:]
        
        # Set the free fall detector if the user is climbing
        if len(history) > 3 and "climb" in history[-3:]:
            free_fall_alert = 1
            
        
        # Turn off the free fall detector if user has not climbed in the last 15 seconds
        if len(history) > 3 and "climb" not in history[-3:]:
            free_fall_alert = 0
        
        # Debounce the emergency for 30 seconds
        if (alert==1) and (0 < alert_count < 6):
            # Deactivate the emergency if a motion other than rest has been detected
            if prediction != "rest":
                print('Emergency Debounced: No Emergency')
                alert = 0
                alert_count = 0
            
            # Continue the debounce
            else:
                print("Alert countdown: ", 6 - alert_count)
                alert_count += 1
        
        # Alert the user that the Emergency Debounce has started (BUZZER)
        if (alert==1) and (alert_count == 0):
            print("Debouncing Emergency")
            print("Alert countdown: ", 6 - alert_count)
            accelerometer.disable_freefall_detection()
            alert_count+=1
                
        # Emergency successfully debounced: activate the emergency protocol at the base station
        if alert_count == 6:
            
            status = 1
            while True:
                data =''
                time_,lat,lon,alt = get_coordinates(gps)
                data = time_ + lat + lon + alt
                data += ("{}".format(status)).zfill(1)
                data += ("{}".format(device_id)).zfill(4)
                print(data)
                lora_send(data,spi,CS,RESET)
                time.sleep(10)
            
            
        if lora_counter == 3:
        
            # Format and send data through LORA
            data =''
            time_,lat,lon,alt = get_coordinates(gps)
            data = time_ + lat + lon + alt
            data += ("{}".format(status)).zfill(1)
            data += ("{}".format(device_id)).zfill(4)
            print(data)
            lora_send(data,spi,CS,RESET)
            
        
            lora_counter = 0
        lora_counter += 1 

if __name__ == '__main__':
    main()
