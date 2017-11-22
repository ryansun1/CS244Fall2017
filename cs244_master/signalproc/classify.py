import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
import pdb

ACTIVITIES = np.arange(1,6)

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
    laying_data = np.genfromtxt("Ryan_laying.csv",
                         delimiter=',', skip_header=0, usecols=(0, 1, 2))
    sitting_data = np.genfromtxt("Ryan_sitting.csv",
                         delimiter=',', skip_header=0, usecols=(0, 1, 2))

    #compute window for the training data
    laying_data = np.concatenate((compute_window(laying_data), 
                                    np.full((laying_data.shape[0], 1), 
                                1, dtype=laying_data.dtype)), axis = 1)
    sitting_data = np.concatenate((compute_window(sitting_data),
                                     np.full((sitting_data.shape[0], 1), 
                                2, dtype=laying_data.dtype)), axis = 1)
    features = np.concatenate((laying_data, sitting_data), axis = 0)
    training_data, validation_data = split_data(features, seed=0)
    #train on partial data
    training_data = training_data[::2]

    clf = svm.SVC()
    clf.fit(training_data[:,:-1], training_data[:,-1])
    evaluate_learner(clf, training_data, validation_data)

    #test data is sitting 
    sensor_reading = np.genfromtxt("sensor.csv",
                         delimiter=',', skip_header=0, usecols=(0, 1, 2))
    test_data = compute_window(sensor_reading)

    Yte = np.full(test_data.shape[0], 2, test_data.dtype)
    Yte_hat = clf.predict(test_data)
    test_MSE = np.mean((Yte_hat - Yte) ** 2)
    print("test MSE", test_MSE)
