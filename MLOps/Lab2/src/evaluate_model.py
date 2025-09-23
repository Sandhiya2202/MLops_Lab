import os
from datetime import datetime

import joblib
from sklearn.datasets import make_classification
from sklearn.metrics import f1_score


def main() -> None:
    # Recreate synthetic test data
    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        random_state=42,
    )
    Xte, yte = X[:100], y[:100]

    # Load latest model
    model_dir = "MLOps/Lab2/models"
    if not os.path.isdir(model_dir) or not os.listdir(model_dir):
        raise FileNotFoundError("No models found. Run train_model.py first.")
    latest = sorted(os.listdir(model_dir))[-1]
    model_path = os.path.join(model_dir, latest)
    clf = joblib.load(model_path)

    # Evaluate and save metric
    f1 = f1_score(yte, clf.predict(Xte))
    metrics_dir = "MLOps/Lab2/metrics"
    os.makedirs(metrics_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    metric_path = os.path.join(metrics_dir, f"f1_{ts}.txt")
    with open(metric_path, "w", encoding="utf-8") as f:
        f.write(f"F1 Score: {f1:.4f}\n")
        f.write(f"Model: {latest}\n")
    print(f"✅ F1={f1:.4f}; wrote {metric_path}")


if __name__ == "__main__":
    main()
