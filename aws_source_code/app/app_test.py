from flask import Flask, Response, request
from flask import jsonify
from flask_pymongo import PyMongo
import json
from joblib import dump, load
import numpy as np
import pandas as pd
from sklearn import svm

'''This code is used for testing the machine learning model'''

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'safeClimb'
app.config['MONGO_URI'] = 'mongodb://superuser:iotgroup9@localhost:27017/safeClimb?authSource=admin'
mongo = PyMongo(app)


@app.route("/",methods=['POST'])
def get_training_data():
    data = json.loads(request.data)
    print(data)
    x_ = [abs(float(i)) for i in data['x']]
    y_ = [abs(float(i)) for i in data['y']]
    z_ = [abs(float(i)) for i in data['z']]
    
    
    data['x'] = np.split(np.array(x_),N)
    data['y'] = np.split(np.array(y_),N)
    data['z'] = np.split(np.array(z_),N)
    
    data['x_fft'] = [np.real(np.fft.rfft(i)) for i in data['x']]
    data['y_fft'] = [np.real(np.fft.rfft(i)) for i in data['y']]
    data['z_fft'] = [np.real(np.fft.rfft(i)) for i in data['z']]


    x = []
    y = []
    z = []
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
    
    #test_data += [np.max(i) for i in x_fft]
    #test_data += [np.max(i) for i in y_fft]
    #test_data += [np.max(i) for i in z_fft]
    
    test_data += [np.max(np.abs(i)) for i in x]
    test_data += [np.max(np.abs(i)) for i in y]
    test_data += [np.max(np.abs(i)) for i in z]
    
    test_data += [np.sum(np.square(i))/(2*N) for i in x]
    test_data += [np.sum(np.square(i))/(2*N) for i in y]
    test_data += [np.sum(np.square(i))/(2*N) for i in z]
    
    pred = clf.predict(np.array(test_data).reshape(1, -1)) 
    #data_dump = {'x': x_,'y':y_,'z':z_,'label':str(pred[0])}
    #mongo.db.testing.insert(data_dump)
   
    print('Received and Predicted')

    return jsonify({'prediction':str(pred[0])})
    
if __name__ == '__main__':
    
    clf = load('../svm.joblib')
    N=2

    app.run(host='0.0.0.0',port=5001,debug=True)
