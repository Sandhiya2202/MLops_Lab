from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Load data
    data = load_breast_cancer()
    X, y = data.data, data.target
    feature_names = data.feature_names
    target_names = data.target_names

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)

    # Paths
    artifacts_dir = Path("/app/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    joblib.dump(model, artifacts_dir / "cancer_model.pkl")

    # Save metrics JSON + pretty text
    (artifacts_dir / "metrics.json").write_text(json.dumps({
        "accuracy": acc,
        "classification_report": report
    }, indent=2))

    with open(artifacts_dir / "metrics.txt", "w") as f:
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write(pd.DataFrame(report).to_string())

    # Save confusion matrix as PNG
    fig = plt.figure()
    df_cm = pd.DataFrame(cm, index=target_names, columns=target_names)
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion Matrix")
    plt.colorbar()
    tick_marks = range(len(target_names))
    plt.xticks(tick_marks, target_names, rotation=45)
    plt.yticks(tick_marks, target_names)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(artifacts_dir / "confusion_matrix.png")
    plt.close(fig)

    print("✅ Trained RandomForest on Breast Cancer dataset")
    print(f"📈 Accuracy: {acc:.4f}")
    print("📝 Wrote artifacts: cancer_model.pkl, metrics.json, metrics.txt, confusion_matrix.png")
