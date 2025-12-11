
# Lab 3 – Feature Selection (MLOps)

This lab demonstrates how to apply multiple **feature selection techniques** on a classification dataset using **scikit-learn**.  
You will explore how different subsets of features affect model performance and compare evaluation metrics such as **Accuracy, ROC-AUC, Precision, Recall, and F1 Score**.

The dataset used is the **Breast Cancer Wisconsin Diagnostic dataset**, exported to CSV via `make_dataset.py`.

---

## 📂 Folder Structure

```text
lab_3/
├── data/
│   └── breast_cancer_lab3.csv        # Dataset generated using sklearn
│
├── make_dataset.py                   # Script that generates the dataset
├── lab3_feature_selection.py         # Main lab code
├── feature_selection_results.csv     # Metrics table (created after running)
└── README.md                         # This documentation


