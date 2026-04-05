import os
import glob
import pandas as pd
import numpy as np
import tensorflow as tf
from ha_rec import system_type


if system_type:
    # Path to HA config folder
    CONFIG_PATH = "/config/SSFL/Data"
    MODEL_PATH = "/config/SSFL/test_model5_final_global_model.keras"
else:
    # Path to local config folder
    CONFIG_PATH = "HA_data"
    MODEL_PATH = "../FL_Flower_Pipeline/Results/Server/test_model4/test_model4_final_global_model.keras"
    # the trained model is in Etafweer-Smart-Plug/FL_Flower_Pipeline/Results/Server/test_model4/test_model4_final_global_model.keras"


def get_latest_csv():
    """Finds the most recent CSV file in /config/SSFL/Data/"""
    files = glob.glob(os.path.join(CONFIG_PATH, "sensor_data_*.csv"))
    if not files:
        print("No CSV files found!")
        return None
    latest_file = max(files, key=os.path.getctime)
    return latest_file


def extract_last_3_rows(file_path):
    """Reads only the last 3 rows from the CSV file correctly."""
    try:
        # ✅ Ensure last 3 rows are extracted
        data = pd.read_csv(file_path).tail(3)
        # print("\nExtracted Data:\n", data)
        # print("\nExtracted Data Length:", len(data))  # Debugging
        return data
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None


def min_max_scale(value, data):
    """Manually scale value to [0,1] range, ensuring min is 0 if needed."""
    min_val = 0.0
    max_val = 16816.0  # (70.03, 16816.0)

    # Ensure scaling behaves exactly like MinMaxScaler
    if min_val == max_val:
        return 0  # Avoid division by zero

    return (value - min_val) / (max_val - min_val)


def process_last_3_rows(df):
    """Processes only the last 3 rows and returns the middle row (2nd last)."""
    if df is None or len(df) < 3:
        print("Not enough data for prediction!")
        return None

    df = df.copy()  # ✅ Avoid modifying original DataFrame

    # Rename 'power' to 'p(t)' in the WHOLE DataFrame
    df.rename(columns={'power': 'p(t)'}, inplace=True)

    # Extract 2nd last row
    middle_row = df.iloc[1].copy()

    # Replace values less than 2 with 0
    middle_row['p(t)'] = 0 if middle_row['p(t)'] < 2 else middle_row['p(t)']

    # Normalize p(t)
    # Extract all power values from dataset to determine min and max
    all_power_values = df['p(t)'].tolist()

    # Normalize the middle row's power value using dataset min/max
    middle_row['Norm_p(t)'] = min_max_scale(
        middle_row['p(t)'], all_power_values)

    # ✅ Now df has 'p(t)', so this won't throw KeyError
    middle_row['p(t) - p(t+1)'] = df.iloc[1]['p(t)'] - df.iloc[2]['p(t)']
    middle_row['p(t) - p(t-1)'] = df.iloc[1]['p(t)'] - df.iloc[0]['p(t)']

    # Select only required features
    processed_data = np.array([
        middle_row['Occupancy'],
        middle_row['p(t)'],
        middle_row['Norm_p(t)'],
        middle_row['p(t) - p(t+1)'],
        middle_row['p(t) - p(t-1)']
    ]).reshape(1, -1)  # Reshape for model input

    return processed_data


def predict():
    """Loads the model, extracts last 3 rows from latest data, and predicts."""
    latest_csv = get_latest_csv()

    print(f"Data path: {latest_csv}")

    if not latest_csv:
        return "No data available"

    df = extract_last_3_rows(latest_csv)  # Read last 3 rows
    input_data = process_last_3_rows(df)  # Process middle row

    # print(input_data)

    if input_data is None:
        return "Not enough data for prediction"

    # Load Model
    model = tf.keras.models.load_model(MODEL_PATH)

    # Get Prediction
    prediction = model.predict(input_data)
    predicted_class = int(np.argmax(prediction))

    print(f"The predincted class ins: {predicted_class}")
    return predicted_class  # Assuming a single output
