import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier


def main() -> None:
    # Generate synthetic data
    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        random_state=42,
    )
    df = pd.DataFrame(
        X,
        columns=[f"feature_{i}" for i in range(10)],
    )
    df["target"] = y

    # Train split
    train = df.sample(frac=0.8, random_state=42)
    Xtr = train.drop(columns=["target"])
    ytr = train["target"]

    # Train model
    clf = RandomForestClassifier(random_state=42)
    clf.fit(Xtr, ytr)

    # Save model with timestamp
    os.makedirs("MLOps/Lab2/models", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    path = f"MLOps/Lab2/models/model_{ts}.joblib"
    joblib.dump(clf, path)
    print(f"✅ Saved: {path}")


if __name__ == "__main__":
    main()
