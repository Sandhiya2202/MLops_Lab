# make_dataset.py
from sklearn.datasets import load_breast_cancer
import pandas as pd
from pathlib import Path


def main():
    data = load_breast_cancer()
    df = pd.DataFrame(data.data, columns=data.feature_names)
    # target: 0 = malignant? No: in sklearn, 0 = malignant, 1 = benign
    df["target"] = data.target

    out_path = Path("data") / "breast_cancer_lab3.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Saved dataset to {out_path} with shape {df.shape}")


if __name__ == "__main__":
    main()

