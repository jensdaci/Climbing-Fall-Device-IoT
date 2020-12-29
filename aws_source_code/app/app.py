from flask import Flask, Response, request
from flask import jsonify
from flask_pymongo import PyMongo
import json

'''This code is used to train the machine learning model'''

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'safeClimb'
app.config['MONGO_URI'] = 'mongodb://superuser:iotgroup9@localhost:27017/safeClimb?authSource=admin'
mongo = PyMongo(app)


@app.route("/",methods=['POST'])
def get_training_data():
    data = json.loads(request.data)
    training = mongo.db.training2.insert(data)


    print('Received: ',data)
    
    return Response('Okay')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5000',debug=True)
