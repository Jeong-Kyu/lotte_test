import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from keras.preprocessing.image import ImageDataGenerator
from numpy import expand_dims
from sklearn.model_selection import StratifiedKFold, KFold
from keras import Sequential
from keras.layers import *
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.optimizers import Adam,SGD
from sklearn.model_selection import train_test_split
from tensorflow.keras.applications import EfficientNetB4
from tensorflow.keras.applications.efficientnet import preprocess_input
from tqdm import tqdm

#데이터 지정 및 전처리
x = np.load("C:/LPD_competition/npy/P_project_x4.npy",allow_pickle=True)
x_pred = np.load('C:/LPD_competition/npy/test.npy',allow_pickle=True)
y = np.load("C:/LPD_competition/npy/P_project_y4.npy",allow_pickle=True)
x = preprocess_input(x) 
x_pred = preprocess_input(x_pred) 

idg = ImageDataGenerator(
    # rotation_range=10, acc 하락
    width_shift_range=(-1,1),   # 0.1 => acc 하락
    height_shift_range=(-1,1),  # 0.1 => acc 하락
    # rotation_range=40, acc 하락 
    shear_range=0.2)

idg2 = ImageDataGenerator()

'''
- rotation_range: 이미지 회전 범위 (degrees)
- width_shift, height_shift: 그림을 수평 또는 수직으로 랜덤하게 평행 이동시키는 범위 
                                (원본 가로, 세로 길이에 대한 비율 값)
- rescale: 원본 영상은 0-255의 RGB 계수로 구성되는데, 이 같은 입력값은 
            모델을 효과적으로 학습시키기에 너무 높습니다 (통상적인 learning rate를 사용할 경우). 
            그래서 이를 1/255로 스케일링하여 0-1 범위로 변환시켜줍니다. 
            이는 다른 전처리 과정에 앞서 가장 먼저 적용됩니다.
- shear_range: 임의 전단 변환 (shearing transformation) 범위
- zoom_range: 임의 확대/축소 범위
- horizontal_flip`: True로 설정할 경우, 50% 확률로 이미지를 수평으로 뒤집습니다. 
    원본 이미지에 수평 비대칭성이 없을 때 효과적입니다. 즉, 뒤집어도 자연스러울 때 사용하면 좋습니다.
- fill_mode 이미지를 회전, 이동하거나 축소할 때 생기는 공간을 채우는 방식
'''

y = np.argmax(y, axis=1)

from sklearn.model_selection import train_test_split
x_train, x_valid, y_train, y_valid = train_test_split(x,y, train_size = 0.8, shuffle = True, random_state=66)
kfold = KFold(n_splits=5, shuffle=True)


train_generator = idg.flow(x_train,y_train,batch_size=32)
# seed => random_state
valid_generator = idg2.flow(x_valid,y_valid)
test_generator = x_pred

mc = ModelCheckpoint('C:/LPD_competition/lotte_m2_projcet.h5',save_best_only=True, verbose=1)

from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Flatten, BatchNormalization, Dense, Activation
from tensorflow.keras.applications import VGG19, MobileNet,InceptionResNetV2, InceptionV3, EfficientNetB2
mobile_net = EfficientNetB2(weights="imagenet", include_top=False, input_shape=(128, 128, 3))

# for layer in mobile_net.layers:
# layer.trainable = False
    
top_model = mobile_net.output
top_model = GlobalAveragePooling2D()(top_model)
# top_model = Flatten()(top_model)
top_model = Dense(4048, activation="swish")(top_model)
# top_model = Dense(1024, activation="relu")(top_model)
# top_model = Dense(512, activation="relu")(top_model)
top_model = Dense(1000, activation="softmax")(top_model)
    
model = Model(inputs=mobile_net.input, outputs = top_model)

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
early_stopping = EarlyStopping(patience= 20)
lr = ReduceLROnPlateau(patience= 10, factor=0.5)

model.compile(optimizer=tf.keras.optimizers.Adam(lr=1e-5), 
                loss = 'sparse_categorical_crossentropy', metrics=['accuracy'])

learning_history = model.fit_generator(train_generator,epochs=200, 
    validation_data=valid_generator, callbacks=[early_stopping,lr,mc])

# predict
model.load_weights('C:/LPD_competition/lotte_m2_projcet.h5')
#result = model.predict(x_pred,verbose=True)

tta_steps = 20
predictions = []

for i in tqdm(range(tta_steps)):
    preds = model.predict_generator(x_pred,verbose=True)
    predictions.append(preds)

final_pred = np.mean(predictions, axis=0)

sub = pd.read_csv('C:/LPD_competition/sample.csv')
sub['prediction'] = np.argmax(final_pred,axis = 1)
sub.to_csv('C:/LPD_competition/answer0318_m2.csv',index=False)