import os

import tensorflow.keras.layers as L
from tensorflow.keras.models import Sequential


def test_model1(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(64, activation='relu'),
        L.Dense(32, activation='relu'),
        L.Dense(5)
    ])

    return model


def test_model2(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(128, activation='relu'),
        L.Dense(64, activation='relu'),
        L.Dense(32, activation='relu'),
        L.Dense(5)
    ])

    return model


def test_model3(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(256, activation='relu'),
        L.Dense(128, activation='relu'),
        L.Dense(64, activation='relu'),
        L.Dense(32, activation='relu'),
        L.Dense(5)
    ])

    return model


def test_model4(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(64, activation='relu'),
        L.Dropout(0.3),
        L.Dense(32, activation='relu'),
        L.Dropout(0.3),
        L.Dense(5)
    ])

    return model


def test_model5(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(128, activation='relu'),
        L.Dropout(0.3),
        L.Dense(64, activation='relu'),
        L.Dropout(0.3),
        L.Dense(32, activation='relu'),
        L.Dropout(0.3),
        L.Dense(5)
    ])

    return model


def test_model6(input_shape):
    model = Sequential([
        L.Input(shape=input_shape),
        L.Dense(256, activation='relu'),
        L.Dropout(0.3),
        L.Dense(128, activation='relu'),
        L.Dropout(0.3),
        L.Dense(64, activation='relu'),
        L.Dropout(0.3),
        L.Dense(32, activation='relu'),
        L.Dropout(0.3),
        L.Dense(5)
    ])

    return model
