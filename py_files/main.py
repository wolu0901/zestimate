# -*- coding: utf-8 -*-
'''
Created on Thu Sep 21 19:11:28 2017

@authors: codeWoker & Zibski
'''


import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
import pickle
import os

import data_loader

data_files = data_loader.load_all_data_files()
properties = data_loader.load_data(data_files[0])
train = data_loader.load_data(data_files[1])
for c in properties.columns:
    properties[c]=properties[c].fillna(-1)
    if properties[c].dtype == 'object':
        lbl = LabelEncoder()
        lbl.fit(list(properties[c].values))
        properties[c] = lbl.transform(list(properties[c].values))

train_df = train.merge(properties, how='left', on='parcelid')
x_train = train_df.drop(['parcelid', 'logerror','transactiondate'], axis=1)
x_test = properties.drop(['parcelid'], axis=1)
# shape        
print('Shape train: {}\nShape test: {}'.format(x_train.shape, x_test.shape))

# drop out ouliers
train_df=train_df[ train_df.logerror > -0.4 ]
train_df=train_df[ train_df.logerror < 0.4 ]
x_train=train_df.drop(['parcelid', 'logerror','transactiondate'], axis=1)
y_train = train_df["logerror"].values.astype(np.float32)
y_mean = np.mean(y_train)

print('After removing outliers:')     
print('Shape train: {}\nShape test: {}'.format(x_train.shape, x_test.shape))


# xgboost params
xgb_params = {
    'eta': 0.06,
    'max_depth': 5,
    'subsample': 0.77,
    'objective': 'reg:linear',
    'eval_metric': 'mae',
    'base_score': y_mean,
    'silent': 1
}

dtrain = xgb.DMatrix(x_train, y_train)
dtest = xgb.DMatrix(x_test)

# cross-validation
cv_result = xgb.cv(xgb_params, 
                   dtrain, 
                   nfold=5,
                   num_boost_round=200,
                   early_stopping_rounds=50,
                   verbose_eval=10, 
                   show_stdv=False
                  )
num_boost_rounds = len(cv_result)
print(num_boost_rounds)
# train model
model = xgb.train(dict(xgb_params, silent=1), dtrain, num_boost_round=num_boost_rounds)
pred = model.predict(dtest)
y_pred=[]

for i,predict in enumerate(pred):
    y_pred.append(str(round(predict,4)))
y_pred=np.array(y_pred)

output = pd.DataFrame({'ParcelId': properties['parcelid'].astype(np.int32),
        '201610': y_pred, '201611': y_pred, '201612': y_pred,
        '201710': y_pred, '201711': y_pred, '201712': y_pred})
# set col 'ParceID' to first col
cols = output.columns.tolist()
cols = cols[-1:] + cols[:-1]
output = output[cols]
from datetime import datetime
data_loader.save_data(output, 'sub{}.csv'.format(datetime.now().strftime('%Y%m%d_%H%M%S')))
# Save model to sav file
pickle.dump(model, open(os.path.abspath(os.getcwd()+'\\..')+'\\models\\' + 'model_{}.sav'.format(datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb'))
# Save model parameters to file
f = open(os.path.abspath(os.getcwd()+'\\..')+'\\models\\' + 'model_{}_parameters.txt'.format(datetime.now().strftime('%Y%m%d_%H%M%S')),'w')
f.write(str(xgb_params))
f.close()