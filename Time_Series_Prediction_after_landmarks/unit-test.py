from pandas import DataFrame
from pandas import Series
from pandas import concat
from pandas import read_csv
from pandas import datetime

from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler

import numpy as np
from numpy import concatenate

import matplotlib.ticker as ticker
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from _definition import pivot_k_window,MDPP

from typing import List

# load data from .npz
# the data in ./Data/Residential_Load/ has 3 columns, meters_date, meters_time and load_data.
def load_data(filename):
    temp = np.load(filename)
    return temp["arr_0"],temp["arr_1"],temp["arr_2"]

# convert an array of values into a dataset matrix
def create_dataset(dataset, look_back=1):
    dataset = np.insert(dataset, [0] * look_back, 0)
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back):
        a = dataset[i:(i + look_back)]
        dataX.append(a)
        dataY.append(dataset[i + look_back])
    dataY = np.array(dataY)
    dataY = np.reshape(dataY, (dataY.shape[0], 1))
    dataset = np.concatenate((dataX, dataY), axis=1)
    return dataset

# create a differenced series
def difference(dataset, interval=1):
    diff = list()
    # diff.append(0)
    for i in range(interval, len(dataset)):
        value = dataset[i] - dataset[i - interval]
        diff.append(value)
    return Series(diff)

# invert differenced value
def inverse_difference(history, yhat, interval=1):
    ori = list()
    for i in range(len(yhat)):
        value=yhat[i]+history[-interval+i]
        ori.append(value)
    return Series(ori).values

# scale train and test data to [-1, 1]
def scale(train, test):
    # fit scaler
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaler = scaler.fit(train)
    # transform train
    train = train.reshape(train.shape[0], train.shape[1])
    train_scaled = scaler.transform(train)
    # transform test
    test = test.reshape(test.shape[0], test.shape[1])
    test_scaled = scaler.transform(test)
    return scaler, train_scaled, test_scaled

# inverse scaling for a forecasted value
def invert_scale(scaler, ori_array ,pred_array):
    # reshape the array to 2D
    pred_array=pred_array.reshape(pred_array.shape[0],1)
    ori_array=ori_array.reshape(ori_array.shape[0],1)
    # maintain the broadcast shape with scaler
    pre_inverted=concatenate((ori_array, pred_array), axis=1)
    inverted = scaler.inverse_transform(pre_inverted)
    # extraction the pred_array_inverted
    pred_array_inverted=inverted[:,-1]
    return pred_array_inverted

if __name__ == '__main__':
    # load dataset

    dirs = "./Data/Crude_Oil_Price/WTI.npz"
    # dirs = "./Data/Residential_Load/Residential_Load_hour.npz"
    temp = np.load(dirs)
    load_data= temp["arr_0"].tolist()
    # np.savez(dirs,load_data)
    ts_values_array=np.array(load_data)
    set_length=len(ts_values_array)

    k_windows = 5
    # peak_dic, trough_dic=pivot_k_window(load_data, k_windows)
    marks_dic = MDPP(load_data,5,0.15)

    # peak_range: List[int] = []
    # peak_value: List[float] = []
    # trough_range: List[int] = []
    # trough_value: List[float] = []
    marks_range: List[int] = []
    marks_value: List[float] = []
    
    # for idx in peak_dic:
    #     peak_range.append(idx)
    #     peak_value.append(peak_dic[idx])
    # for idx in trough_dic:
    #     trough_range.append(idx)
    #     trough_value.append(trough_dic[idx])
    for idx in marks_dic:
        marks_range.append(idx)
        marks_value.append(marks_dic[idx])

    # transform data to be stationary
    diff = difference(load_data, 1)

    # create differece_dataset x,y
    dataset = diff.values
    dataset = create_dataset(dataset, look_back=1)

    # split into train and test sets
    train_size = int(dataset.shape[0] * 0.8)
    train_scope=np.arange(train_size)
    # test_size = dataset.shape[0] - train_size
    test_scope= np.arange(train_size,set_length)
    #-------------------------------------------------------------------
    # divide the ts_values to train set and test set
    ts_train=ts_values_array[:train_size].copy()
    ts_target=ts_values_array[train_size:].copy()
    #--------------------------------------------------------------------
    #divide the ts_values_diff to train set and test set
    train, test = dataset[0:train_size], dataset[train_size:]
    ts_train_diff=train[:,:1]
    ts_test_diff=test[:,:1]
    ts_test_diff=np.append(ts_test_diff,dataset[-1,-1])
    #--------------------------------------------------------------------
    # transform the scale of the data
    scaler, train_scaled, test_scaled = scale(train, test)
    # divided the train_set and test_set
    ts_trian_scaled=train_scaled[:,:1]
    ts_test_scaled=test_scaled[:,:1]
    ts_test_scaled=np.append(ts_test_scaled,test_scaled[-1,-1])
    
    #=====================================================================
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # plt.figure(figsize=(10,15))
    plt.figure(figsize=(15,5))
    # locate the sublabel
    # draw the train set and test set
    # plt=plt.subplot(111)
    # plt.set_xticks(np.arange(0,set_length,10))
    plt.plot(train_scope, ts_train,'k',label='ts_train',linewidth = 1.5)
    plt.plot(test_scope, ts_target,'r',label='ts_target',linewidth = 1.5)
    # plt.plot(peak_range,peak_value,'c^',label='ts_peak')
    # plt.plot(trough_range,trough_value,'mv',label='ts_trough')
    plt.plot(marks_range,marks_value,'yo',label='ts_marks')
    for key in marks_dic:
        # show_mark='('+str(key)+',%s)' %(marks_dic[key])
        show_mark=str(key)
        plt.annotate(show_mark,xy=(key, marks_dic[key]),fontsize=9,color='y')
    # plt.minorticks_on()
    # plt.grid(which='both')
    plt.legend(loc='upper right')
    plt.title('Values for Time Sequences')
    plt.xlabel('Time Sequence' )
    plt.ylabel('Value')

    '''
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ax2=plt.subplot(312,sharex=plt)
    ax2.plot(train_scope, ts_train_diff,'g',label='ts_train_diff',linewidth = 1.5)
    ax2.plot(test_scope, ts_test_diff,'r:',label='ts_target_diff',linewidth = 1.5)
    # ax2.minorticks_on()
    ax2.grid(which='both')
    ax2.legend(loc='upper right')
    ax2.set_title('Values_difference for Time Sequences')
    plt.xlabel('Time Sequence')
    plt.ylabel('Difference')
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ax3=plt.subplot(313,sharex=plt)
    ax3.plot(train_scope, ts_trian_scaled,'b',label='ts_train_diff_scaled',linewidth = 1.5)
    ax3.plot(test_scope, ts_test_scaled,'r:',label='ts_target_diff_scaled',linewidth = 1.5)

    # ax3.minorticks_on()
    ax3.grid(which='both')
    ax3.legend(loc='upper right')
    ax3.set_title('Values_difference_scaled for Time Sequences')
    plt.xlabel('Time Sequence')
    plt.ylabel('Scaled Difference')
    '''

    # plt.subplots_adjust(hspace=0.75)
    plt.savefig('WTI_visualization.png')
    plt.show()
   
