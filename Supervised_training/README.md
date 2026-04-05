# Supervised Training

This module contains the supervised training pipeline used to initialize the Semi-Supervised Federated Learning (SSFL) framework. The supervised model is first trained on a labeled subset generated from the available benchmark datasets, and the trained model is then used to support the later SSFL stages.

---

## Dataset Preparation

All datasets are available in the `FL_Flower_Pipeline/Dataset/` directory, as shown below:

```text
Dataset/
│
├── Processed_data/
│   ├── Dred_processed.csv
│   └── QUD_processed.csv
│
└── SSFL_DATA/
    ├── Data/
    ├── DRED/
    ├── QUD/
    ├── data_com_glob_train.csv
    ├── data_dred_glob_test.csv
    ├── data_qud_glob_test.csv
└── data_com_glob_test.csv
```

### Dataset Description

- `Processed_data/`
  - Contains the original processed benchmark datasets with MM labels:
    - `QUD_processed.csv`
    - `Dred_processed.csv`

- `SSFL_DATA/`
  - Contains the data prepared for the SSFL pipeline
  - Includes the combined global training and testing splits used in the framework

---

## Training Data for Supervised Learning

For the supervised initialization stage, a **10% labeled subset from QUD** and a **10% labeled subset from DRED** are selected and combined to form the supervised training dataset.

This combined labeled subset is used to train the initial baseline classification model before pseudo-label generation and federated learning.

---

## Training Procedure

The supervised training process should be performed by following the steps provided in:

```text
Label_training.ipynb
```

This notebook contains the complete training workflow, including:

- loading the processed datasets
- preparing the labeled training subset
- model definition
- supervised training
- evaluation
- saving the trained model for later SSFL usage

---

## Notes

- Ensure the dataset paths are correctly configured before running the notebook
- The supervised model trained in this stage is later used to generate pseudo-labels for unlabeled data
- This stage serves as the initialization step for the SSFL pipeline

---

## Recommended Workflow

1. Prepare the processed datasets in the `Dataset/` folder
2. Open `Label_training.ipynb`
3. Follow the notebook step by step for supervised training
4. Save the trained model
5. Use the trained model for the SSFL and FL stages
