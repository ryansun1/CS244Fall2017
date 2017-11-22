import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
import pdb

ACTIVITIES = np.arange(1,6)

def plot_xyz(time, x,y,z, activity):
    plt.figure()
    plt.plot(time, x, label='X')
    plt.plot(time, y, label='Y')
    plt.plot(time, z, label='Z')

    plt.title("activity = {}".format(activity))
    plt.xlabel('Time (Seconds)')
    plt.grid(True)
    plt.axis('tight')
    plt.legend(loc='upper left')
    
def graph_all_features(time: np.array, csv: "csv format"):
    for activity in ACTIVITIES:
        x, y, z, _ = extract_activity(csv, activity)
        plot_xyz(time, x, y, z, activity)
    plt.show(False)    

def extract_activity(csv: "csv format", activity:int):
    return csv.T[1+(activity-1)*4:5+(activity-1)*4]

def split_data(data, seed = 0):
    ''' shuffle and split the data into a training and validation dataset
    inspired by the ml library from cs 273a
    '''
    np.random.seed(seed)
    pi = np.random.permutation(data.shape[0])
    shuffled_data = data[pi,:]
    split = int(data.shape[0]*0.8)
    training_data = data[pi,:][:split]
    validation_data = data[pi,:][split:]

    return training_data, validation_data

def compute_window(X, window_size = 10, func = np.mean):
    window = np.zeros(X.shape)
    for i in range(X.shape[0]):
        window[i] = func(X[max(0, i-window_size):min(X.shape[0]-1, i+window_size)], axis = 0)
    return np.concatenate((X, window), axis = 1)

def calculate_feature_mean(csv, window_size):
    features = np.empty(shape = (0, 7))
    for i in ACTIVITIES:
        activity_i = extract_activity(csv, i).T
        features_i = np.concatenate((compute_window(activity_i[:,:-1]), activity_i[:,-1, np.newaxis]), axis = 1)
        features = np.concatenate((features, features_i), axis = 0)
    return features    

def evaluate_learner(clf, training_data, validation_data):
    training_MSE = np.mean(
                    np.where(clf.predict(training_data[:,:-1]) != training_data[:,-1], 1, 0) ** 2
                    )
    validation_MSE = np.mean(
                    np.where(clf.predict(validation_data[:,:-1]) - validation_data[:,-1], 1, 0) ** 2
                    )
    training_MAE = np.where(clf.predict(training_data[:,:-1]) != training_data[:,-1])[0].shape[0] / training_data.shape[0]
    validation_MAE = np.where(clf.predict(validation_data[:,:-1]) != validation_data[:,-1])[0].shape[0] / validation_data.shape[0]
    print("MSE", training_MSE, validation_MSE)
    print("MAE", training_MAE, validation_MAE)

if __name__ == '__main__':
    csv = np.genfromtxt("takashin_[Students]assignment5_sampleXYZ.csv",
                         delimiter=',', skip_header=1)
    time = csv.T[0]
    #graph_all_features(time, csv)
    features = calculate_feature_mean(csv, 1000)
    training_data, validation_data = split_data(features, seed=0)
    #train on partial data
    training_data = training_data[::2]

    clf = svm.SVC()
    clf.fit(training_data[:,:-1], training_data[:,-1])
    evaluate_learner(clf, training_data, validation_data)

    sensor_reading = np.genfromtxt("sensor.csv",
                         delimiter=',', skip_header=1, usecols=(1, 2, 3))
    test_data = compute_window(sensor_reading)

    Yte = np.full(test_data.shape[0], 5, test_data.dtype)
    Yte_hat = clf.predict(test_data)
    test_MSE = np.mean((Yte_hat - Yte) ** 2)
    print("test MSE", test_MSE)
