#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Affective Computing with AMIGOS Dataset
'''

from argparse import ArgumentParser
import os
import pickle
import numpy as np
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, f1_score
from sklearn.feature_selection import RFE
from sklearn.svm import SVR
from mlxtend.feature_selection import SequentialFeatureSelector as SFS
from ALL_preprocess import MISSING_DATA, SUBJECT_NUM, VIDEO_NUM
from fisher import fisher, feature_selection

MISSING_DATA_IDX = []
for tup in MISSING_DATA:
    MISSING_DATA_IDX.append((tup[0] - 1) * 16 + tup[1] - 1)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


def main():
    ''' Main function '''
    parser = ArgumentParser(description='Affective Computing with AMIGOS Dataset')
    parser.add_argument('--feature', type=str,
                        choices=['eeg', 'ecg', 'gsr', 'all'], default='all', help='choose type of modality')
    args = parser.parse_args()

    with open(os.path.join('data', 'features.p'), 'rb') as pickle_file:
        amigos_data = pickle.load(pickle_file)

    train_a_accuracy_history = []
    train_v_accuracy_history = []
    train_a_f1score_history = []
    train_v_f1score_history = []
    val_a_accuracy_history = []
    val_v_accuracy_history = []
    val_a_f1score_history = []
    val_v_f1score_history = []
    
    # split labels to 0 and 1 according to their ''individual'' mean
    labels = np.genfromtxt('./data/label.csv', delimiter=',')
    labels = labels[:,:2]
    for i in range(SUBJECT_NUM): 
        a_labels_mean = np.mean(labels[i*16:i*16+16,0])
        v_labels_mean = np.mean(labels[i*16:i*16+16,1])
        for idx, label in enumerate(labels[i*16:i*16+16,:]):
            labels[idx+i*16][0] = 1 if label[0] > a_labels_mean else 0
            labels[idx+i*16][1] = 1 if label[1] > v_labels_mean else 0    

    for i in range(SUBJECT_NUM):
        print("Leaving {} Subject Out".format(i + 1))
        train_data = np.array([])
        val_data = np.array([])

        # get features for cross validation
        for s_key, data_dict in amigos_data.items():
            if args.feature == 'all':
                tmp_array = np.array([])
                for _, f_dict in data_dict.items():
                    for _, item in f_dict.items():
                        tmp_array = np.append(tmp_array, item)

                if s_key.split('_')[0] == str(i + 1):
                    val_data = np.vstack((val_data, tmp_array)) if val_data.size else tmp_array
                else:
                    train_data = np.vstack((train_data, tmp_array)
                                           ) if train_data.size else tmp_array
            else:
                tmp_array = np.array([])
                for _, item in data_dict[args.feature].items():
                    tmp_array = np.append(tmp_array, item)

                if s_key.split('_')[0] == str(i + 1):
                    val_data = np.vstack((val_data, tmp_array)) if val_data.size else tmp_array
                else:
                    train_data = np.vstack((train_data, tmp_array)
                                           ) if train_data.size else tmp_array

        # map features to [-1, 1]
        train_data_max = np.max(train_data, axis=0)
        train_data_min = np.min(train_data, axis=0)
        train_data = (train_data - train_data_min) / (train_data_max - train_data_min)
        train_data = train_data * 2 - 1
        val_data_max = np.max(val_data, axis=0)
        val_data_min = np.min(val_data, axis=0)
        val_data = (val_data - val_data_min) / (val_data_max - val_data_min)
        val_data = val_data * 2 - 1

        # get labels for cross validation
        train_a_labels = []
        train_v_labels = []
        val_a_labels = []
        val_v_labels = []
        val_idx = np.arange(16) + i * 16
        
        for idx, line in enumerate(labels):
            if idx in MISSING_DATA_IDX:
                continue
            if idx in val_idx:
                val_a_labels.append(line[0])
                val_v_labels.append(line[1])
            else:
                train_a_labels.append(line[0])
                train_v_labels.append(line[1])
            if idx == SUBJECT_NUM * VIDEO_NUM - 1:
                break
            
        ###############################################
        a_clf  = SFS(a_clf, k_features=20, forward=False, floating=False,\
        verbose=2,scoring='accuracy',cv=39)
        v_clf  = SFS(v_clf, k_features=20, forward=False, floating=False,\
        verbose=2,scoring='accuracy',cv=39)
        #################################################
        print('Training Arousal Model')
        a_clf.fit(train_data, train_a_labels)
        print('Training Valence Model')
        v_clf.fit(train_data, train_v_labels)
        
######################################################
        train_a_predict_labels = a_clf.predict(train_data)
        train_v_predict_labels = v_clf.predict(train_data)

        val_a_predict_labels = a_clf.predict(val_data)
        val_v_predict_labels = v_clf.predict(val_data)
        
        
######################################################
        train_a_labels = np.array(train_a_labels) # list to array
        train_v_labels = np.array(train_v_labels)
        val_a_labels = np.array(val_a_labels)
        val_v_labels = np.array(val_v_labels)
        
        train_a_accuracy = accuracy_score(train_a_labels, train_a_predict_labels) # array / array
        train_v_accuracy = accuracy_score(train_v_labels, train_v_predict_labels)        
        train_a_f1score = f1_score(train_a_labels, train_a_predict_labels, average='macro')
        train_v_f1score = f1_score(train_v_labels, train_v_predict_labels, average='macro')

        val_a_accuracy = accuracy_score(val_a_labels, val_a_predict_labels)
        val_v_accuracy = accuracy_score(val_v_labels, val_v_predict_labels)        
        val_a_f1score = f1_score(val_a_labels, val_a_predict_labels, average='macro')
        val_v_f1score = f1_score(val_v_labels, val_v_predict_labels, average='macro')
        print(val_a_labels,"\n",val_a_predict_labels,"\n")
        print(val_v_labels,"\n",val_v_predict_labels,"\n")

        print('Training Result')
        print("Arousal: Accuracy: {}, F1score: {}".format(train_a_accuracy, train_a_f1score))
        print("Valence: Accuracy: {}, F1score: {}".format(train_v_accuracy, train_v_f1score))

        print('Validating Result')
        print("Arousal: Accuracy: {}, F1score: {}".format(val_a_accuracy, val_a_f1score))
        print("Valence: Accuracy: {}, F1score: {}".format(val_v_accuracy, val_v_f1score))

        train_a_accuracy_history.append(train_a_accuracy)
        train_v_accuracy_history.append(train_v_accuracy)
        train_a_f1score_history.append(train_a_f1score)
        train_v_f1score_history.append(train_v_f1score)
        val_a_accuracy_history.append(val_a_accuracy)
        val_v_accuracy_history.append(val_v_accuracy)
        val_a_f1score_history.append(val_a_f1score)
        val_v_f1score_history.append(val_v_f1score)

        with open(os.path.join(MODEL_DIR, "a_model_{}.p".format(i + 1)), 'wb') as pickle_file:
            pickle.dump(a_clf, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

        with open(os.path.join(MODEL_DIR, "v_model_{}.p".format(i + 1)), 'wb') as pickle_file:
            pickle.dump(v_clf, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

    print('\nAverage Training Result')
    print("Arousal: Accuracy: {}, F1score: {}".format(
        np.mean(train_a_accuracy_history), np.mean(train_a_f1score_history)))
    print("Valence: Accuracy: {}, F1score: {}".format(
        np.mean(train_v_accuracy_history), np.mean(train_v_f1score_history)))

    print('Average Validating Result')
    print("Arousal: Accuracy: {}, F1score: {}".format(
        np.mean(val_a_accuracy_history), np.mean(val_a_f1score_history)))
    print("Valence: Accuracy: {}, F1score: {}".format(
        np.mean(val_v_accuracy_history), np.mean(val_v_f1score_history)))

if __name__ == '__main__':

    main()