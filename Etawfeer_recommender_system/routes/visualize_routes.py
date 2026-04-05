import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from ha_rec import system_type
import tzlocal

visualize_bp = Blueprint('visualize_bp', __name__)

if system_type:
    POWER_DATA_FOLDER = "/config/SSFL/Data"
else:
    POWER_DATA_FOLDER = "Ha_data"


def get_csv_files():
    """Finds all CSV files in the data folder, sorted by date (newest first)."""
    files = [f for f in os.listdir(POWER_DATA_FOLDER) if f.startswith(
        "sensor_data_") and f.endswith(".csv")]
    if not files:
        return []

    files.sort(reverse=True, key=lambda x: datetime.strptime(
        x.split("_")[-1].replace(".csv", ""), "%Y-%m-%d"))
    return [os.path.join(POWER_DATA_FOLDER, f) for f in files]


@visualize_bp.route("/power-data")
def get_power_data():
    """Returns power data for the last 24 hours, week, or month."""
    filter_type = request.args.get("filter", "24h")

    csv_files = get_csv_files()
    if not csv_files:
        return jsonify([])

    df_list = []
    local_tz = tzlocal.get_localzone()
    for f in csv_files:
        file_date = f.split("_")[-1].replace(".csv", "")
        temp_df = pd.read_csv(f)

        # Drop completely empty rows
        temp_df = temp_df.dropna(how="all")

        # Drop rows where timestamp or power is missing or empty
        temp_df = temp_df[
            temp_df["timestamp"].notnull() &
            temp_df["timestamp"].astype(str).str.strip().ne("") &
            temp_df["power"].notnull()
        ]

        # Ensure power column is numeric
        temp_df["power"] = pd.to_numeric(temp_df["power"], errors="coerce")

        # Drop rows with invalid power after conversion
        temp_df = temp_df.dropna(subset=["power"])

        # Create full datetime from filename + time string
        temp_df["timestamp"] = temp_df["timestamp"].apply(
            lambda t: f"{file_date} {t}")
        # temp_df["timestamp"] = pd.to_datetime(    temp_df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

        temp_df["timestamp"] = pd.to_datetime(
            temp_df["timestamp"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce"
        ).dt.tz_localize(local_tz, ambiguous='NaT', nonexistent='NaT')

        # Drop rows with invalid timestamps
        temp_df = temp_df.dropna(subset=["timestamp"])

        df_list.append(temp_df)

    if not df_list:
        return jsonify([])

    df = pd.concat(df_list, ignore_index=True)

    now = df["timestamp"].max()
    if pd.isnull(now):
        return jsonify([])

    # Define filter window and resampling interval
    if filter_type == "24h":
        time_threshold = now - timedelta(hours=24)
        resample_interval = "10min"  # ✅ instead of deprecated "30T"
    elif filter_type == "week":
        time_threshold = now - timedelta(days=7)
        resample_interval = "6h"
    elif filter_type == "month":
        time_threshold = now - timedelta(days=30)
        resample_interval = "1D"
    else:
        return jsonify([])

    df = df[df["timestamp"] >= time_threshold]

    # ✅ Resample and fill missing values with 0
    df = (
        df.set_index("timestamp")
        .resample(resample_interval)
        .mean()
        .fillna(0)          # Replace missing values caused by empty time windows
        .reset_index()
    )

    return jsonify(df.to_dict(orient="records"))
