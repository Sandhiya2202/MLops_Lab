"""
Lab 3 – Feature Selection

Dataset:
    data/breast_cancer_lab3.csv
    - 30 numeric features
    - target column: "target" (0/1)

This script:
    * loads the dataset
    * trains a RandomForestClassifier
    * applies multiple feature selection methods
    * compares performance (Accuracy, ROC, Precision, Recall, F1)
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import (
    RFE,
    SelectKBest,
    SelectFromModel,
    f_classif,
)
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)

# ==========================
# CONFIG
# ==========================

DATASET_PATH = Path("data") / "breast_cancer_lab3.csv"
TARGET_COL = "target"

TEST_SIZE = 0.2
RANDOM_STATE = 123
K_UNIVARIATE = 20
N_RFE_FEATURES = 20
CORR_TARGET_THRESHOLD = 0.2
CORR_FEATURE_THRESHOLD = 0.9
FEATURE_IMPORTANCE_THRESHOLD = 0.013


# ==========================
# HELPERS
# ==========================

def load_data():
    """Load the CSV and split into X, y."""
    print(f"Loading dataset from {DATASET_PATH} ...")
    df = pd.read_csv(DATASET_PATH)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())

    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in CSV.")

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].values
    return df, X, y


def fit_model(X_train, y_train):
    model = RandomForestClassifier(
        criterion="entropy", random_state=47, n_estimators=200
    )
    model.fit(X_train, y_train)
    return model


def calculate_metrics(model, X_test, y_test):
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    return acc, roc, prec, rec, f1


def train_and_get_metrics(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = fit_model(X_train_scaled, y_train)
    return calculate_metrics(model, X_test_scaled, y_test)


def evaluate_model_on_features(X, y, label):
    acc, roc, prec, rec, f1 = train_and_get_metrics(X, y)
    return pd.DataFrame(
        [[acc, roc, prec, rec, f1, X.shape[1]]],
        columns=["Accuracy", "ROC", "Precision", "Recall", "F1 Score", "Feature Count"],
        index=[label],
    )


# ==========================
# FEATURE SELECTION METHODS
# ==========================

def strong_corr_features(df):
    """Filter features strongly correlated with the target."""
    print("\n[1] Filter: correlation with target")
    cor = df.corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(cor, cmap="PuBu", annot=False)
    plt.title("Correlation matrix")
    plt.tight_layout()
    plt.show()

    cor_target = cor[TARGET_COL].abs()
    relevant = cor_target[cor_target > CORR_TARGET_THRESHOLD]
    names = [c for c in relevant.index if c != TARGET_COL]

    print(f"Selected {len(names)} strongly correlated features.")
    return names


def drop_redundant_features(X):
    """Drop highly correlated (redundant) features."""
    print("\n[2] Filter: drop redundant highly correlated features")
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    to_drop = [col for col in upper.columns if any(upper[col] > CORR_FEATURE_THRESHOLD)]
    kept = [c for c in X.columns if c not in to_drop]

    print("Features dropped:", to_drop)
    print("Remaining features:", len(kept))
    return kept


def univariate_kbest(X, y):
    """SelectKBest with ANOVA F-test."""
    print("\n[3] Filter: Univariate F-test (SelectKBest)")
    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)

    k = min(K_UNIVARIATE, X.shape[1])
    selector = SelectKBest(f_classif, k=k)
    selector.fit(X_train_scaled, y_train)
    names = X.columns[selector.get_support()]
    print(f"Selected {len(names)} features by F-test.")
    return list(names)


def rfe_selection(X, y):
    """Recursive Feature Elimination with RandomForest."""
    print("\n[4] Wrapper: RFE with RandomForest")
    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)

    n_features = min(N_RFE_FEATURES, X.shape[1])
    model = RandomForestClassifier(
        criterion="entropy", random_state=47, n_estimators=200
    )
    rfe = RFE(model, n_features_to_select=n_features)
    rfe.fit(X_train_scaled, y_train)
    names = X.columns[rfe.get_support()]
    print(f"Selected {len(names)} features via RFE.")
    return list(names)


def feature_importance_selection(X, y):
    """Embedded: RandomForest feature importance + SelectFromModel."""
    print("\n[5] Embedded: Feature importance (RandomForest)")
    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)

    model = RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=200)
    model.fit(X_train_scaled, y_train)
    importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(
        ascending=True
    )

    plt.figure(figsize=(8, 12))
    importances.plot(kind="barh")
    plt.title("Feature importances (RandomForest)")
    plt.tight_layout()
    plt.show()

    selector = SelectFromModel(model, prefit=True, threshold=FEATURE_IMPORTANCE_THRESHOLD)
    names = X.columns[selector.get_support()]
    print(f"Selected {len(names)} features via feature importance.")
    return list(names)


def l1_selection(X, y):
    """Embedded: L1-regularized LinearSVC."""
    print("\n[6] Embedded: L1-regularized LinearSVC")
    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train)

    lsvc = LinearSVC(C=1.0, penalty="l1", dual=False, random_state=RANDOM_STATE)
    selector = SelectFromModel(lsvc)
    selector.fit(X_train_scaled, y_train)

    names = X.columns[selector.get_support()]
    print(f"Selected {len(names)} features via L1 regularization.")
    return list(names)


# ==========================
# MAIN
# ==========================

def main():
    df, X, y = load_data()

    # start with an empty DataFrame
    results = pd.DataFrame()

    # 0) Baseline – all features
    print("\n=== Baseline: all features ===")
    results = pd.concat([results, evaluate_model_on_features(X, y, "All features")])

    # 1) Strongly correlated features
    strong_names = strong_corr_features(df)
    X_strong = X[strong_names]
    results = pd.concat([results, evaluate_model_on_features(X_strong, y, "Strong corr")])

    # 2) Subset after dropping redundant features
    subset_names = drop_redundant_features(X_strong)
    X_subset = X[subset_names]
    results = pd.concat([results, evaluate_model_on_features(X_subset, y, "Subset corr")])

    # 3) Univariate F-test
    uni_names = univariate_kbest(X, y)
    X_uni = X[uni_names]
    results = pd.concat([results, evaluate_model_on_features(X_uni, y, "F-test")])

    # 4) RFE
    rfe_names = rfe_selection(X, y)
    X_rfe = X[rfe_names]
    results = pd.concat([results, evaluate_model_on_features(X_rfe, y, "RFE")])

    # 5) Feature importance
    fi_names = feature_importance_selection(X, y)
    X_fi = X[fi_names]
    results = pd.concat([results, evaluate_model_on_features(X_fi, y, "Feat importance")])

    # 6) L1 regularization
    l1_names = l1_selection(X, y)
    if len(l1_names) > 0:
        X_l1 = X[l1_names]
        results = pd.concat([results, evaluate_model_on_features(X_l1, y, "L1 Reg")])
    else:
        print("No features selected by L1; skipping metrics for L1.")

    # Final summary
    print("\n==============================")
    print("FINAL RESULTS")
    print("==============================")
    print(results)

    results.to_csv("feature_selection_results.csv")
    print("\nSaved metrics to feature_selection_results.csv")



if __name__ == "__main__":
    main()

