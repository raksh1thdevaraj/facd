from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.svm import SVC

from ml.scripts.extract_dataset_features import generate_synthetic_feature_dataset
from ml.scripts.preprocess_features import FEATURE_NAMES, TabularDataPreprocessor


def train_baseline_models(
    train_df: pd.DataFrame | None = None,
    output_model_dir: Path | None = None,
    cv_splits: int = 5,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train and cross-validate 4 candidate ML baseline models, selecting and serializing the best model.

    Args:
        train_df: Training DataFrame containing 22 features and 'is_manipulated'.
        output_model_dir: Directory to save serialized model artifacts.
        cv_splits: Number of stratified cross-validation folds.
        random_state: Seed for reproducibility.

    Returns:
        Dictionary of candidate model performance summaries and path to best model artifact.
    """
    model_dir = output_model_dir or Path("ml/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    if train_df is None:
        train_df, _, _ = generate_synthetic_feature_dataset(
            n_samples=600, random_state=random_state
        )

    X_train = train_df[FEATURE_NAMES].values.astype(np.float32)
    y_train = train_df["is_manipulated"].values.astype(int)

    # 1. Fit feature scaler strictly on training split
    preprocessor = TabularDataPreprocessor()
    X_train_scaled = preprocessor.fit_transform(X_train)
    scaler_path = model_dir / "feature_scaler.joblib"
    preprocessor.save(scaler_path)

    # 2. Define candidate models
    candidate_models: dict[str, Any] = {
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=4,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.08,
            random_state=random_state,
        ),
        "LogisticRegression": LogisticRegression(
            C=1.0,
            max_iter=500,
            class_weight="balanced",
            random_state=random_state,
        ),
        "SVC": SVC(
            C=1.0,
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=random_state,
        ),
    }

    # 3. Stratified 5-Fold Cross Validation
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
    results: dict[str, dict[str, float]] = {}

    best_model_name = "RandomForestClassifier"
    best_f1 = 0.0

    for name, model in candidate_models.items():
        # Tree models can use unscaled or scaled; linear/SVM need scaled
        features_to_use = (
            X_train_scaled if name in ("LogisticRegression", "SVC") else X_train
        )
        scores = cross_validate(
            model,
            features_to_use,
            y_train,
            cv=cv,
            scoring=["accuracy", "f1", "precision", "recall", "roc_auc"],
            n_jobs=-1,
        )

        mean_acc = float(np.mean(scores["test_accuracy"]))
        mean_f1 = float(np.mean(scores["test_f1"]))
        mean_roc = float(np.mean(scores["test_roc_auc"]))

        results[name] = {
            "cv_accuracy": round(mean_acc, 4),
            "cv_f1": round(mean_f1, 4),
            "cv_roc_auc": round(mean_roc, 4),
        }

        # Primary baseline selection
        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_model_name = name

    # 4. Train best model on full training set
    selected_estimator = candidate_models[best_model_name]
    if best_model_name in ("LogisticRegression", "SVC"):
        selected_estimator.fit(X_train_scaled, y_train)
    else:
        # Wrap in pipeline or fit directly on unscaled
        selected_estimator.fit(X_train, y_train)

    # 5. Serialize best model bundle
    best_model_path = model_dir / "baseline_model_v1.joblib"
    joblib.dump(selected_estimator, str(best_model_path))

    return {
        "best_model": best_model_name,
        "best_f1_score": round(best_f1, 4),
        "model_artifact_path": str(best_model_path),
        "scaler_artifact_path": str(scaler_path),
        "candidate_results": results,
    }


if __name__ == "__main__":
    out = train_baseline_models()
    print("Training finished successfully:")
    print(out)
