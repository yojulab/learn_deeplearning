# -*- coding: utf-8 -*-
# refer : https://www.tensorflow.org/tutorials/images/classification
"""classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/tensorflow/docs-l10n/blob/master/site/ko/tutorials/images/classification.ipynb
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import PIL
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

import pathlib
# download : http://www.vision.caltech.edu/Image_Datasets/Caltech101/
data_dir = '/Users/sanghunoh/Downloads/101_ObjectCategories/'
data_dir = pathlib.Path(data_dir)

image_count = len(list(data_dir.glob('*/*.jpg')))
print(data_dir, image_count)

batch_size = 64
img_height = 180
img_width = 180

train_ds = tf.keras.preprocessing.image_dataset_from_directory(
  data_dir,
  validation_split=0.2,
  subset="training",
  seed=123,
  image_size=(img_height, img_width),
  batch_size=batch_size)

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
  data_dir,
  validation_split=0.2,
  subset="validation",
  seed=123,
  image_size=(img_height, img_width),
  batch_size=batch_size)

class_names = train_ds.class_names
print(class_names)

count = 0
for images, labels in train_ds.take(1):
  count += 1
  print(count, ', ', labels)

import matplotlib.pyplot as plt

plt.figure(figsize=(100, 100))
cols = 10
remains = batch_size % cols
rows = batch_size - remains

for images, labels in train_ds.take(1):
  for i in range(rows):
    ax = plt.subplot(rows, cols, i + 1)
    plt.imshow(images[i].numpy().astype("uint8"))
    plt.title(class_names[labels[i]])
    plt.axis("off")

for image_batch, labels_batch in train_ds:
  print(image_batch.shape)
  print(labels_batch.shape)
  break

"""# 모델 만들기

모델은 각각에 최대 풀 레이어가 있는 3개의 컨볼루션 블록으로 구성됩니다. 그 위에 `relu` 활성화 함수에 의해 활성화되는 128개의 단위가 있는 완전히 연결된 레이어가 있습니다. 이 모델은 높은 정확성을 고려해 조정되지 않았습니다. 이 튜토리얼의 목표는 표준적인 접근법을 보여주는 것입니다. 
"""

num_classes = len(train_ds.class_names)

"""## 과대적합

## 데이터 증강
"""

with tf.device('/cpu:0'):   # for mac with cpu
  data_augmentation = keras.Sequential(
    [
      layers.experimental.preprocessing.RandomFlip("horizontal", 
                                                  input_shape=(img_height, 
                                                                img_width,
                                                                3)),
      layers.experimental.preprocessing.RandomRotation(0.1),
      layers.experimental.preprocessing.RandomZoom(0.1),
    ]
  )

plt.figure(figsize=(100, 100))

for images, _ in train_ds.take(1):
  for i in range(rows):
    augmented_images = data_augmentation(images)
    ax = plt.subplot(rows, cols, i + 1)
    plt.imshow(augmented_images[0].numpy().astype("uint8"))
    plt.axis("off")

"""## 드롭아웃"""

model = Sequential([
  data_augmentation,
  layers.experimental.preprocessing.Rescaling(1./255),
  layers.Conv2D(16, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(32, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(64, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Dropout(0.2),
  layers.Flatten(),
  layers.Dense(128, activation='relu'),
  layers.Dense(num_classes)
])

"""## 모델 컴파일 및 훈련하기"""

model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

model.summary()

epochs = 150
history = model.fit(
  train_ds,
  validation_data=val_ds,
  epochs=epochs,
)

model.save('./datas/tf_model.h5')

"""## 훈련 결과 시각화하기

데이터 증강 및 드롭아웃을 적용한 후, 이전보다 과대적합이 줄어들고 훈련 및 검증 정확성이 더 가깝게 조정됩니다. 
"""

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

loss = history.history['loss']
val_loss = history.history['val_loss']

epochs_range = range(epochs)

plt.figure(figsize=(8, 8))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.title('Training and Validation Accuracy')

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.title('Training and Validation Loss')
plt.show()

"""## 새로운 데이터로 예측하기

참고: 데이터 증강 및 드롭아웃 레이어는 추론 시 비활성화됩니다.
"""

load_model = tf.keras.models.load_model('./datas/tf_model.h5')

test_datasets_dir = "/Users/sanghunoh/Downloads/test_datasets"

test_datasets_dir = pathlib.Path(test_datasets_dir)

possitive = 0
negative = 0
for filepath in list(test_datasets_dir.glob('*.*')):
  img = keras.preprocessing.image.load_img(
      str(filepath), target_size=(img_height, img_width)
  )
  img_array = keras.preprocessing.image.img_to_array(img)
  img_array = tf.expand_dims(img_array, 0) # Create a batch

  predictions = load_model.predict(img_array)
  score = tf.nn.softmax(predictions[0])

  print(
      "belongs to {} with a {:.2f} percent confidence. - {}"
      .format(class_names[np.argmax(score)], 100 * np.max(score), filepath.stem)
  )
  if class_names[np.argmax(score)] in filepath.stem:
    possitive += 1
  else :
    negative += 1

print('possitive : {}, negative : {}'.format(possitive, negative))
# batch_size = 32, epochs = 50 --> possitive : 7, negative : 14
# batch_size = 128, epochs = 50 --> possitive : 10, negative : 11
# batch_size = 64, epochs = 150 --> possitive : 12, negative : 9