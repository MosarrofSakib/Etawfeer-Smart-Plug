import os
import matplotlib.pyplot as plt

import pandas as pd
import tensorflow.keras.layers as L
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from pathlib import Path

from .models import *

Base_dir = Path(__file__).resolve().parent.parent


def process_raw_data(file_path):
    '''
    Process the raw sensors data 
    [occupancy, paower] to ["Occupancy", "P(t)", "Norm_P(t)", "P(t)-P(t+1)", "P(t)-P(t-1)"]

    Input: Raw data csv file path
    Return: Processed data as a dataframe ["Occupancy", "P(t)", "Norm_P(t)", "P(t)-P(t+1)", "P(t)-P(t-1)"]
    '''

    df = pd.read_csv(file_path)

    cols_lower = {c.strip().lower(): c for c in df.columns}
    if "occupancy" not in cols_lower or "power" not in cols_lower:
        raise ValueError(f"Required columns not found in {file_path}")

    occ_col = cols_lower["occupancy"]
    power_col = cols_lower["power"]

    df = df[[occ_col, power_col]].copy()
    df.rename(columns={occ_col: "Occupancy", power_col: "P(t)"}, inplace=True)

    # Convert to numeric
    df["P(t)"] = pd.to_numeric(df["P(t)"], errors="coerce")

    # Drop rows with NaN (both Occupancy and P(t))
    df.dropna(subset=["Occupancy", "P(t)"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ---- Normalization ----
    p_min = df["P(t)"].min()
    p_max = df["P(t)"].max()

    if pd.isna(p_min) or pd.isna(p_max):
        raise ValueError(f"'P(t)' all NaN in {file_path}")

    if p_max > p_min:
        df["Norm_P(t)"] = (df["P(t)"] - p_min) / (p_max - p_min)
    else:
        df["Norm_P(t)"] = 0.0

    # ---- Difference features ----
    df["P(t)-P(t+1)"] = df["P(t)"] - df["P(t)"].shift(-1)
    df["P(t)-P(t-1)"] = df["P(t)"] - df["P(t)"].shift(1)

    # Fill edge NaNs
    df[["P(t)-P(t+1)", "P(t)-P(t-1)"]] = df[
        ["P(t)-P(t+1)", "P(t)-P(t-1)"]
    ].fillna(0.0)

    df = df[["Occupancy", "P(t)", "Norm_P(t)", "P(t)-P(t+1)", "P(t)-P(t-1)"]]

    return df


def process_ssfl_data(dataset_root_dir, ha_data):
    '''
    Generate pseudo labels for collected processed data, then combines it with the initial labeled data.

    Input: Labeled data path, collected processed dataframe
    Return: Combined data with pseudo labels.
    '''

    model_path = os.path.join(
        Base_dir, "Results/HA_Data/Server/test_model4/test_model4_final_global_model.keras")
    labeled_data_path = os.path.join(
        dataset_root_dir, "data_com_glob_train.csv")

    labeled_d = pd.read_csv(labeled_data_path)
    labeled_d["pseudo_label"] = labeled_d["label"]

    labeled_data = labeled_d.drop(columns=["label"])

    # ====== STEP 1: extract X and y ======
    data_x = ha_data.iloc[:, :5].values    # features

    # ====== STEP 2: model predictions ======
    model = load_model(model_path)
    prediction = model.predict(data_x)

    probs = prediction.max(axis=1)              # confidence for each sample
    pseudo_labels = prediction.argmax(axis=1)   # predicted label

    # ====== STEP 3: high-confidence filtering ======
    mask = probs >= 0.90                        # threshold: 0.9

    # filter data_x, data_y, pseudo_labels
    client_data_conf = ha_data[mask]        # keep only confident samples
    pseudo_labels_conf = pseudo_labels[mask]

    # ====== STEP 4: add pseudo-labels to filtered rows ======
    data_with_pseudo = pd.concat(
        [
            client_data_conf.reset_index(drop=True),
            pd.Series(pseudo_labels_conf, name="pseudo_label")
        ],
        axis=1
    )

    # ====== STEP 5: reorder columns ======
    cols = [
        "Occupancy",
        "P(t)",
        "Norm_P(t)",
        "P(t)-P(t+1)",
        "P(t)-P(t-1)",
        "pseudo_label",
    ]

    data_with_pseudo_arr = data_with_pseudo[cols]
    dred_ssl_data = labeled_data[cols]

    # Ensure same column order
    data_with_pseudo_arr = data_with_pseudo_arr[cols]

    # Combine
    ssl_train_data = pd.concat(
        [dred_ssl_data, data_with_pseudo_arr], ignore_index=True)

    return ssl_train_data


def plot_curve(metrics, metrics_name, client_name, save_dir):
    plt.figure()
    plt.plot(metrics, label=f'{client_name}_{metrics_name}_curve')
    plt.xlabel('Round')
    plt.ylabel(f'{metrics_name}')
    plt.legend()
    plt.savefig(os.path.join(
        save_dir, f'{client_name}_{metrics_name}_curve.png'))


def build_model(input_shape, model_name):

    if model_name == "test_model1":
        model = test_model1(input_shape)
    elif model_name == "test_model2":
        model = test_model2(input_shape)
    elif model_name == "test_model3":
        model = test_model3(input_shape)
    elif model_name == "test_model4":
        model = test_model4(input_shape)
    elif model_name == "test_model5":
        model = test_model5(input_shape)
    elif model_name == "test_model6":
        model = test_model6(input_shape)
    else:
        assert ("The model is not implemented in the pipeline!")

    optimizer = Adam(learning_rate=0.0005)
    loss = SparseCategoricalCrossentropy(from_logits=True)

    model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])

    return model
