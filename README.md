# E-Tawfeer Smart Plug

This repository contains the implementation of E-Tawfeer smart plug system, including **supervised learning**, **federated learning (SSFL)**, and a **real-time recommender system**.

---

## 📂 Structure

- Etawfeer_recommender_system # Real-time system (Flask + Celery + Home Assistant)
- FL_Flower_Pipeline # Federated learning pipeline (Flower)
- Supervised_training # Initial supervised model training

---

## 🔄 Workflow

1. Train initial model (Supervised_training)
2. Improve model using SSFL (FL_Flower_Pipeline)
3. Deploy model for real-time recommendations (Etawfeer_recommender_system)

---

## ⚙️ Tech Stack

- Python, TensorFlow
- Flower (Federated Learning)
- Flask + Celery + Redis
- Home Assistant

---

## 🚀 Setup

Each module has its own instructions:

- `Supervised_training/README.md`
- `FL_Flower_Pipeline/README.md`
- `Etawfeer_recommender_system/README.md`

---

## 📌 Notes

- Sensor data is expected as CSV files (`sensor_data_*.csv`)
- API tokens should be stored in a `.env` file
