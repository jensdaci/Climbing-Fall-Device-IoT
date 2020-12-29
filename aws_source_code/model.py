import pymongo
import numpy as np
import pandas as pd
from sklearn import svm
from joblib import dump, load
import math
from sklearn import svm
from joblib import dump, load
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import normalize

'''This code is used to train the machine learning model (SVM) on the AWS instance, which is where
the training data is stored in a mongoDB.'''

N = 2   

myclient = pymongo.MongoClient("mongodb://superuser:iotgroup9@localhost:27017/safeClimb?authSource=admin")
mydb = myclient["safeClimb"]
mycol = mydb["training2"]

data = {}

rows = mycol.find()

#append all rows of the same run into 1
for row in rows:

    if row['run_id'] in data.keys():
        data[row['run_id']]['x'] += list(row['x'])
        data[row['run_id']]['y'] += list(row['y'])
        data[row['run_id']]['z'] += list(row['z'])
    else:
        data[row['run_id']] = {'x':list(row['x']),'y':list(row['y']),'z':list(row['z']),'label':row['label']}

#trim all rows to that length and split into N segments
for row in data:
    length_ = len(data[row]['x'])
    data[row]['x'] = np.split(np.array(data[row]['x']),N)
    data[row]['x_fft'] = [np.real(np.fft.rfft(i)) for i in data[row]['x']] 
    data[row]['y'] = np.split(np.array(data[row]['y']),N)
    data[row]['y_fft'] = [np.real(np.fft.rfft(i)) for i in data[row]['y']]
    data[row]['z'] = np.split(np.array(data[row]['z']),N)
    data[row]['z_fft'] = [np.real(np.fft.rfft(i)) for i in data[row]['z']]

training_data = {}
labels = {}

for row in data:
    temp_x = []
    temp_y = []
    temp_z = []
    for i in range(1,len(data[row]['x'])):
        temp_x.append(np.concatenate([data[row]['x'][i],data[row]['x'][i-1]]))
        temp_y.append(np.concatenate([data[row]['y'][i],data[row]['y'][i-1]]))
        temp_z.append(np.concatenate([data[row]['z'][i],data[row]['z'][i-1]]))
    
    
    temp_x_ = []
    temp_y_ = []
    temp_z_ = []
    for i in range(1,len(data[row]['x_fft'])):
        temp_x_.append(np.concatenate([data[row]['x_fft'][i],data[row]['x_fft'][i-1]]))
        temp_y_.append(np.concatenate([data[row]['y_fft'][i],data[row]['y_fft'][i-1]]))
        temp_z_.append(np.concatenate([data[row]['z_fft'][i],data[row]['z_fft'][i-1]]))

    data[row]['x_fft'] = temp_x_
    data[row]['y_fft'] = temp_y_
    data[row]['z_fft'] = temp_z_
    data[row]['x'] = temp_x
    data[row]['y'] = temp_y
    data[row]['z'] = temp_z

    training_data[row] = {}
    labels[row] = data[row]['label']

    training_data[row]['x_mean_fft'] = np.array([np.mean(np.abs(i)) for i in data[row]['x']])
    training_data[row]['y_mean_fft'] = np.array([np.mean(np.abs(i)) for i in data[row]['y']])
    training_data[row]['z_mean_fft'] = np.array([np.mean(np.abs(i)) for i in data[row]['z']])
    
    training_data[row]['x_std_fft'] = np.array([np.std(i) for i in data[row]['x_fft']])
    training_data[row]['y_std_fft'] = np.array([np.std(i) for i in data[row]['y_fft']])
    training_data[row]['z_std_fft'] = np.array([np.std(i) for i in data[row]['z_fft']])
    
    
    training_data[row]['x_max'] = np.array([np.max(np.abs(i)) for i in data[row]['x']])
    training_data[row]['y_max'] = np.array([np.max(np.abs(i)) for i in data[row]['y']])
    training_data[row]['z_max'] = np.array([np.max(np.abs(i)) for i in data[row]['z']])
    
    training_data[row]['x_energy'] = np.array([np.sum(np.square(i))/(2*N) for i in data[row]['x']])
    training_data[row]['y_energy'] = np.array([np.sum(np.square(i))/(2*N) for i in data[row]['y']])
    training_data[row]['z_energy'] = np.array([np.sum(np.square(i))/(2*N) for i in data[row]['z']])
    
features = {}
for row in training_data:
    features[row] = []
    for vec in training_data[row].values():
        features[row] += list(vec)


x_train = pd.DataFrame.from_dict(features,orient='index').reset_index(drop=True)
y_train = pd.DataFrame.from_dict(labels,orient='index').reset_index(drop=True)

x_test = x_train.sample(n=5)
y_test = y_train.loc[x_test.index]

#x_train = x_train.drop(x_test.index,axis=0)
#y_train = y_train.drop(x_test.index,axis=0)
columns = x_train.columns

for column in range(0,len(x_train.columns),3):
    print(column)
    x = x_train[columns[column]].values
    y = x_train[columns[column+1]].values
    z = x_train[columns[column+2]].values
    fig = plt.figure()
    ax = Axes3D(fig)
    colors = {'walk':'red','rest':'blue','climb':'yellow'}
    ax.scatter(x,y,z,c=y_train[0].map(colors))
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_title("{}_{}_{}".format(columns[column],columns[column+1],columns[column+2]))
    plt.savefig("{}_{}_{}.png".format(columns[column],columns[column+1],columns[column+2]))
print(colors)

unique, counts = np.unique(y_train, return_counts=True)
print(dict(zip(unique, counts)))

clf = svm.SVC(kernel='linear',class_weight="balanced")
clf.fit(x_train.values,y_train.values.ravel())


dump(clf,'svm.joblib')

y_pred = clf.predict(x_test.values)

print('prediction: ',y_pred)
print('true: ',[i[0] for i in y_test.values])
