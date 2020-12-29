from flask import Flask, Response, request
from flask import jsonify
from flask_pymongo import PyMongo
import json

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'safeClimb'
app.config['MONGO_URI'] = 'mongodb://superuser:iotgroup9@localhost:27017/safeClimb?authSource=admin'
mongo = PyMongo(app)


@app.route("/get_contact/<device_id>",methods=['POST','GET'])
def get_contact(device_id):
    device = mongo.db.emergency_contacts.find_one_or_404({"device_id":device_id}, {'_id': False})
    print(device)
    return device

@app.route("/add_contact",methods=['POST'])
def add_contact():
    data = json.loads(request.data)
    mongo.db.emergency_contacts.insert(data)

    return Response('Inserted Contact')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5002',debug=True)
