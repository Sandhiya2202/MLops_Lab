# Docker Cancer Trainer

This container trains a RandomForest on the **Breast Cancer Wisconsin** dataset (from scikit-learn) and saves `cancer_model.pkl` to `./artifacts`.

## Quickstart
```bash
# build
docker build -t cancer-train:1.0 .

# run (model saved to ./artifacts on your host)
mkdir -p artifacts
docker run --rm -v "$PWD/artifacts:/app/artifacts" cancer-train:1.0

- CI test: Mon Oct  6 20:30:38 EDT 2025
- CI touch: Mon Oct  6 20:47:05 EDT 2025
- CI test: Mon Oct  6 20:47:22 EDT 2025
- CI touch: Mon Oct  6 20:53:40 EDT 2025
- CI touch: Mon Oct  6 20:58:15 EDT 2025
