import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.utils import resample
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_train")


def train_and_export_models():
    # Resolve paths
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    csv_path = base_dir / "ML" / "heart_2020_cleaned (1).csv"
    output_dir = Path(__file__).resolve().parent / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    logger.info(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Raw dataset shape: {df.shape}")

    # 1. Resample and balance classes (exact logic from notebook cell 49)
    df_majority = df[df['HeartDisease'] == 'No']
    df_minority = df[df['HeartDisease'] == 'Yes']

    df_majority_downsampled = resample(
        df_majority,
        replace=False,
        n_samples=len(df_minority),
        random_state=42
    )

    df_balanced = pd.concat([df_majority_downsampled, df_minority])
    df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
    df_balanced = df_balanced.drop_duplicates().copy()
    logger.info(f"Balanced dataset shape after dedup: {df_balanced.shape}")

    # 2. Binary column mapping
    binary_columns = [
        'Smoking',
        'AlcoholDrinking',
        'Stroke',
        'DiffWalking',
        'PhysicalActivity',
        'Asthma',
        'KidneyDisease',
        'SkinCancer'
    ]
    for col in binary_columns:
        df_balanced[col] = df_balanced[col].map({'No': 0, 'Yes': 1})

    df_balanced['HeartDisease'] = df_balanced['HeartDisease'].map({'No': 0, 'Yes': 1})

    # 3. Dummy encoding for multi-category columns
    df_encoded = pd.get_dummies(
        df_balanced,
        columns=['Sex', 'AgeCategory', 'Race', 'Diabetic', 'GenHealth'],
        drop_first=True
    )

    bool_columns = df_encoded.select_dtypes(include='bool').columns
    df_encoded[bool_columns] = df_encoded[bool_columns].astype(int)

    X = df_encoded.drop('HeartDisease', axis=1)
    y = df_encoded['HeartDisease']
    feature_names = X.columns.tolist()
    logger.info(f"Feature count: {len(feature_names)}")

    # 4. Stratified Train-Test Split (80/20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    logger.info(f"X_train: {X_train.shape}, X_test: {X_test.shape}")

    # 5. Initialize exact base models from notebook
    logger.info("Initializing base estimators...")
    lr_model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=42
    )

    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )

    xgb_model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
        n_jobs=-1
    )

    # 6. Fit base estimators
    logger.info("Fitting Logistic Regression...")
    lr_model.fit(X_train, y_train)

    logger.info("Fitting Random Forest...")
    rf_model.fit(X_train, y_train)

    logger.info("Fitting XGBoost...")
    xgb_model.fit(X_train, y_train)

    # 7. Construct and fit Hard Voting Ensemble
    logger.info("Building Hard-Voting Ensemble...")
    heartshield_ensemble = VotingClassifier(
        estimators=[
            ('lr', lr_model),
            ('rf', rf_model),
            ('xgb', xgb_model)
        ],
        voting='hard'
    )
    heartshield_ensemble.fit(X_train, y_train)

    # 8. Evaluate
    y_pred_ensemble = heartshield_ensemble.predict(X_test)
    train_acc = heartshield_ensemble.score(X_train, y_train)
    test_acc = accuracy_score(y_test, y_pred_ensemble)
    report = classification_report(y_test, y_pred_ensemble, output_dict=True)
    conf_matrix = confusion_matrix(y_test, y_pred_ensemble).tolist()

    logger.info(f"Ensemble Train Accuracy: {train_acc:.4f}")
    logger.info(f"Ensemble Test Accuracy: {test_acc:.4f}")

    # Individual model test accuracies
    lr_test_acc = accuracy_score(y_test, lr_model.predict(X_test))
    rf_test_acc = accuracy_score(y_test, rf_model.predict(X_test))
    xgb_test_acc = accuracy_score(y_test, xgb_model.predict(X_test))

    logger.info(f"Base Accuracies - LR: {lr_test_acc:.4f}, RF: {rf_test_acc:.4f}, XGB: {xgb_test_acc:.4f}")

    # 9. Export artifacts
    joblib.dump(heartshield_ensemble, output_dir / "heartshield_hard_voting_ensemble.joblib")
    joblib.dump(lr_model, output_dir / "logistic_regression.joblib")
    joblib.dump(rf_model, output_dir / "random_forest.joblib")
    joblib.dump(xgb_model, output_dir / "xgboost.joblib")

    with open(output_dir / "feature_columns.json", "w") as f:
        json.dump(feature_names, f, indent=2)

    metadata = {
        "model_name": "HeartShield Hybrid Hard-Voting Ensemble",
        "version": "1.0.0",
        "estimators": ["LogisticRegression", "RandomForestClassifier", "XGBClassifier"],
        "voting_strategy": "hard",
        "num_features": len(feature_names),
        "train_accuracy": round(float(train_acc), 4),
        "test_accuracy": round(float(test_acc), 4),
        "base_model_accuracies": {
            "logistic_regression": round(float(lr_test_acc), 4),
            "random_forest": round(float(rf_test_acc), 4),
            "xgboost": round(float(xgb_test_acc), 4)
        },
        "classification_report": report,
        "confusion_matrix": conf_matrix
    }

    with open(output_dir / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"All model artifacts successfully exported to {output_dir}")
    return metadata


if __name__ == "__main__":
    train_and_export_models()
