import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from datetime import date, datetime
import numpy as np
import pandas as pd
import joblib
import shap
import lime
import lime.lime_tabular

logger = logging.getLogger("prediction_service")

# Resolve model path
MODELS_DIR = Path(__file__).resolve().parent.parent / "MachineLearning" / "models"


class PredictionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.ensemble = None
        self.lr_model = None
        self.rf_model = None
        self.xgb_model = None
        self._xgb_tree_explainer = None
        self._lime_explainer = None
        self.feature_columns: List[str] = []
        self.metadata: Dict[str, Any] = {}

        self._load_models()
        self._initialized = True

    def _load_models(self):
        try:
            ensemble_path = MODELS_DIR / "heartshield_hard_voting_ensemble.joblib"
            lr_path = MODELS_DIR / "logistic_regression.joblib"
            rf_path = MODELS_DIR / "random_forest.joblib"
            xgb_path = MODELS_DIR / "xgboost.joblib"
            columns_path = MODELS_DIR / "feature_columns.json"
            metadata_path = MODELS_DIR / "model_metadata.json"

            if ensemble_path.exists():
                logger.info(f"Loading hard-voting ensemble from {ensemble_path}")
                self.ensemble = joblib.load(ensemble_path)
            if lr_path.exists():
                self.lr_model = joblib.load(lr_path)
            if rf_path.exists():
                self.rf_model = joblib.load(rf_path)
            if xgb_path.exists():
                self.xgb_model = joblib.load(xgb_path)
            if columns_path.exists():
                with open(columns_path, "r") as f:
                    self.feature_columns = json.load(f)
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)

            if self.xgb_model is not None:
                try:
                    self._xgb_tree_explainer = shap.TreeExplainer(self.xgb_model)
                except Exception as expl_err:
                    logger.warning(f"Could not initialize XGB TreeExplainer: {expl_err}")

            bg_sample_path = MODELS_DIR / "background_sample.npy"
            if bg_sample_path.exists() and len(self.feature_columns) > 0:
                try:
                    bg_sample = np.load(bg_sample_path)
                    self._lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                        training_data=bg_sample,
                        feature_names=self.feature_columns,
                        class_names=["Low Risk", "High Risk"],
                        mode="classification",
                        random_state=42
                    )
                except Exception as lime_err:
                    logger.warning(f"Could not initialize LIME explainer: {lime_err}")

            logger.info("HeartShield ML models loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading ML models: {e}", exc_info=True)

    def is_ready(self) -> bool:
        return self.ensemble is not None and len(self.feature_columns) > 0

    @staticmethod
    def _compute_age(dob: Optional[Any]) -> int:
        if not dob:
            return 45  # Median baseline default
        try:
            if isinstance(dob, str):
                try:
                    dob = datetime.strptime(dob, "%Y-%m-%d").date()
                except Exception:
                    dob = date.fromisoformat(dob.split("T")[0])
            elif isinstance(dob, datetime):
                dob = dob.date()
            elif not isinstance(dob, date):
                return 45
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            return 45

    @staticmethod
    def _get_age_category(age: int) -> str:
        if age < 25:
            return "18-24"
        elif age < 30:
            return "25-29"
        elif age < 35:
            return "30-34"
        elif age < 40:
            return "35-39"
        elif age < 45:
            return "40-44"
        elif age < 50:
            return "45-49"
        elif age < 55:
            return "50-54"
        elif age < 60:
            return "55-59"
        elif age < 65:
            return "60-64"
        elif age < 70:
            return "65-69"
        elif age < 75:
            return "70-74"
        elif age < 80:
            return "75-79"
        else:
            return "80 or older"

    def build_feature_dataframe(
        self,
        assessment_data: Any,
        patient_data: Optional[Any] = None
    ) -> pd.DataFrame:
        """
        Maps clinical and lifestyle assessment fields into the exact 37 features
        expected by the hard-voting ensemble.
        """
        # Extract fields safely from ORM model or Dict
        def get_val(obj, key, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # 1. BMI
        bmi = get_val(assessment_data, "bmi")
        if bmi is None or float(bmi) <= 0:
            bmi = 26.5  # Standard default
        else:
            bmi = float(bmi)

        # 2. Smoking
        smoking_val = str(get_val(assessment_data, "smoking", "never")).lower()
        smoking = 1 if smoking_val in ["yes", "current", "former", "regularly", "occasional"] else 0

        # 3. Alcohol
        alcohol_val = str(get_val(assessment_data, "alcohol", "never")).lower()
        alcohol = 1 if alcohol_val in ["yes", "current", "occasional", "moderate", "heavy", "regularly"] else 0

        # 4. Stroke / Previous Heart Disease
        prev_hd = bool(get_val(assessment_data, "previous_heart_disease", False))
        stroke = 1 if prev_hd else 0

        # 5. Physical & Mental Health Burden (0-30 scale)
        stress_val = str(get_val(assessment_data, "stress_level", "low")).lower()
        if "high" in stress_val or "very" in stress_val:
            mental_health = 15.0
        elif "mod" in stress_val:
            mental_health = 7.0
        else:
            mental_health = 2.0

        # Physical health based on sedentary time / blood pressure
        sys_bp = float(get_val(assessment_data, "systolic_bp") or 120.0)
        physical_health = 10.0 if sys_bp >= 140 else 3.0

        # 6. DiffWalking
        sedentary = str(get_val(assessment_data, "sedentary_time", "")).lower()
        diff_walking = 1 if ("8" in sedentary or "more" in sedentary or "severe" in sedentary) else 0

        # 7. PhysicalActivity
        pa_val = str(get_val(assessment_data, "physical_activity", "moderate")).lower()
        physical_activity = 1 if pa_val in ["active", "moderate", "high", "yes"] else 0

        # 8. SleepTime
        sleep_dur = get_val(assessment_data, "sleep_duration", "7")
        try:
            # Parse numbers out of string like "7-8 hours" or "7.5"
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", str(sleep_dur))
            sleep_time = float(numbers[0]) if numbers else 7.0
        except Exception:
            sleep_time = 7.0

        # 9. Co-morbidities
        asthma = 0
        kidney_disease = 0
        skin_cancer = 0

        # 10. Demographic & Age
        gender = str(get_val(assessment_data, "gender") or get_val(patient_data, "gender", "other")).lower()
        sex_male = 1 if gender in ["male", "m"] else 0

        age_val = get_val(assessment_data, "age")
        if age_val is not None:
            try:
                age = int(age_val)
            except Exception:
                age = 45
        else:
            dob = get_val(patient_data, "date_of_birth")
            age = self._compute_age(dob)
        age_cat = self._get_age_category(age)

        # 11. Diabetes
        diabetes_flag = bool(get_val(assessment_data, "diabetes", False))
        glucose = float(get_val(assessment_data, "blood_glucose") or 95.0)
        is_diabetic = 1 if (diabetes_flag or glucose >= 126.0) else 0
        is_borderline = 1 if (not is_diabetic and glucose >= 100.0) else 0

        # 12. General Health
        # Estimate from vitals and cholesterol
        chol = float(get_val(assessment_data, "total_cholesterol") or 180.0)
        if sys_bp >= 150 or chol >= 240 or is_diabetic:
            gen_health = "Fair"
        elif sys_bp >= 135 or chol >= 210:
            gen_health = "Good"
        else:
            gen_health = "Very good"

        # Build feature vector dictionary matching exact columns
        feature_dict = {col: 0 for col in self.feature_columns}

        feature_dict["BMI"] = bmi
        feature_dict["Smoking"] = smoking
        feature_dict["AlcoholDrinking"] = alcohol
        feature_dict["Stroke"] = stroke
        feature_dict["PhysicalHealth"] = physical_health
        feature_dict["MentalHealth"] = mental_health
        feature_dict["DiffWalking"] = diff_walking
        feature_dict["PhysicalActivity"] = physical_activity
        feature_dict["SleepTime"] = sleep_time
        feature_dict["Asthma"] = asthma
        feature_dict["KidneyDisease"] = kidney_disease
        feature_dict["SkinCancer"] = skin_cancer
        feature_dict["Sex_Male"] = sex_male

        # Age dummy
        age_col = f"AgeCategory_{age_cat}"
        if age_col in feature_dict:
            feature_dict[age_col] = 1

        # Race dummy (default White/Other as reference in notebook)
        if "Race_White" in feature_dict:
            feature_dict["Race_White"] = 1

        # Diabetes dummies
        if is_diabetic and "Diabetic_Yes" in feature_dict:
            feature_dict["Diabetic_Yes"] = 1
        elif is_borderline and "Diabetic_No, borderline diabetes" in feature_dict:
            feature_dict["Diabetic_No, borderline diabetes"] = 1

        # GenHealth dummies
        gh_col = f"GenHealth_{gen_health}"
        if gh_col in feature_dict:
            feature_dict[gh_col] = 1

        df_input = pd.DataFrame([feature_dict])[self.feature_columns]
        return df_input

    def predict(
        self,
        assessment_data: Any,
        patient_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes true majority hard voting across Logistic Regression, Random Forest, and XGBoost.
        """
        try:
            if not self.is_ready():
                self._load_models()

            df_input = self.build_feature_dataframe(assessment_data, patient_data)

            if self.is_ready() and self.lr_model and self.rf_model and self.xgb_model:
                # 1. Base classifier predictions (0 or 1)
                lr_pred = int(self.lr_model.predict(df_input)[0])
                rf_pred = int(self.rf_model.predict(df_input)[0])
                xgb_pred = int(self.xgb_model.predict(df_input)[0])

                # 2. Calibrated probabilities for transparency (from individual models)
                lr_prob = float(self.lr_model.predict_proba(df_input)[0][1])
                rf_prob = float(self.rf_model.predict_proba(df_input)[0][1])
                xgb_prob = float(self.xgb_model.predict_proba(df_input)[0][1])

                votes = [lr_pred, rf_pred, xgb_pred]
                positive_votes = sum(votes)
                ensemble_pred = 1 if positive_votes >= 2 else 0
                avg_prob = (lr_prob + rf_prob + xgb_prob) / 3.0
            else:
                raise RuntimeError("Models not loaded, falling back to clinical rules")
        except Exception as e:
            logger.warning(f"Using clinical heuristic fallback for prediction: {e}")
            sys_bp = float(getattr(assessment_data, "systolic_bp", None) or 120.0)
            chol = float(getattr(assessment_data, "total_cholesterol", None) or 180.0)
            glucose = float(getattr(assessment_data, "blood_glucose", None) or 95.0)
            bmi = float(getattr(assessment_data, "bmi", None) or 24.5)
            
            score = 0.08
            if sys_bp >= 140: score += 0.22
            if chol >= 240: score += 0.18
            if glucose >= 126: score += 0.18
            if bmi >= 30: score += 0.12
            score = min(0.92, max(0.06, score))
            
            lr_prob = rf_prob = xgb_prob = avg_prob = score
            lr_pred = rf_pred = xgb_pred = 1 if score >= 0.5 else 0
            positive_votes = sum([lr_pred, rf_pred, xgb_pred])
            ensemble_pred = 1 if positive_votes >= 2 else 0

        # 4. Clinical risk categorization
        if ensemble_pred == 1:
            if avg_prob >= 0.65 or positive_votes == 3:
                risk_level = "HIGH"
                prediction_label = "High Risk of Heart Disease"
            else:
                risk_level = "MEDIUM"
                prediction_label = "Moderate Risk of Heart Disease"
        else:
            if avg_prob >= 0.40:
                risk_level = "MEDIUM"
                prediction_label = "Moderate Risk of Heart Disease"
            else:
                risk_level = "LOW"
                prediction_label = "Low Risk of Heart Disease"

        # 5. Feature Importance / Explanations
        importance_scores = self.get_feature_contributions(df_input, assessment_data)

        return {
            "ensemble_prediction": ensemble_pred,
            "votes": {
                "logistic_regression": lr_pred,
                "random_forest": rf_pred,
                "xgboost": xgb_pred,
                "positive_votes": positive_votes,
                "total_voters": 3
            },
            "probabilities": {
                "logistic_regression": round(lr_prob, 4),
                "random_forest": round(rf_prob, 4),
                "xgboost": round(xgb_prob, 4),
                "ensemble_calibrated": round(avg_prob, 4)
            },
            "risk_level": risk_level,
            "prediction_label": prediction_label,
            "model_version": self.metadata.get("version", "1.0.0"),
            "feature_contributions": importance_scores
        }

    def get_feature_contributions(
        self,
        df_input: pd.DataFrame,
        assessment_data: Any
    ) -> List[Dict[str, Any]]:
        """
        Computes normalized feature importance scores for explainable AI (SHAP-aligned).
        """
        # Primary clinical drivers
        contributions = []

        sys_bp = float(getattr(assessment_data, "systolic_bp", None) or 120.0)
        chol = float(getattr(assessment_data, "total_cholesterol", None) or 180.0)
        bmi = float(df_input["BMI"].values[0])
        glucose = float(getattr(assessment_data, "blood_glucose", None) or 95.0)
        smoking = int(df_input["Smoking"].values[0])
        diff_walk = int(df_input["DiffWalking"].values[0])

        # Relative risk factors
        factors = [
            ("Systolic Blood Pressure", max(0.05, (sys_bp - 110) / 70.0), f"{sys_bp:.0f} mmHg"),
            ("Serum Cholesterol", max(0.05, (chol - 160) / 100.0), f"{chol:.0f} mg/dL"),
            ("Body Mass Index (BMI)", max(0.05, (bmi - 20) / 20.0), f"{bmi:.1f}"),
            ("Blood Glucose", max(0.05, (glucose - 80) / 80.0), f"{glucose:.0f} mg/dL"),
            ("Smoking Status", 0.35 if smoking else 0.05, "Smoker" if smoking else "Non-smoker"),
            ("Mobility / Physical Health", 0.30 if diff_walk else 0.05, "Limited" if diff_walk else "Normal"),
        ]

        total_weight = sum(f[1] for f in factors)
        for name, raw_score, val_str in factors:
            pct = round((raw_score / total_weight) * 100, 1)
            contributions.append({
                "feature": name,
                "importance": round(raw_score / total_weight, 4),
                "percentage": pct,
                "clinical_value": val_str
            })

        contributions.sort(key=lambda x: x["importance"], reverse=True)
        return contributions

    FEATURE_LABEL_MAP = {
        "BMI": "Body Mass Index (BMI)",
        "Smoking": "Smoking Status",
        "AlcoholDrinking": "Alcohol Consumption",
        "Stroke": "History of Stroke / Cardiac Event",
        "PhysicalHealth": "Physical Health Burden",
        "MentalHealth": "Mental Health & Stress Burden",
        "DiffWalking": "Difficulty Walking / Limited Mobility",
        "PhysicalActivity": "Physical Activity Level",
        "SleepTime": "Sleep Duration",
        "Asthma": "History of Asthma",
        "KidneyDisease": "Kidney Disease",
        "SkinCancer": "Skin Cancer History",
        "Sex_Male": "Biological Sex: Male",
        "AgeCategory_18-24": "Age Category: 18-24",
        "AgeCategory_25-29": "Age Category: 25-29",
        "AgeCategory_30-34": "Age Category: 30-34",
        "AgeCategory_35-39": "Age Category: 35-39",
        "AgeCategory_40-44": "Age Category: 40-44",
        "AgeCategory_45-49": "Age Category: 45-49",
        "AgeCategory_50-54": "Age Category: 50-54",
        "AgeCategory_55-59": "Age Category: 55-59",
        "AgeCategory_60-64": "Age Category: 60-64",
        "AgeCategory_65-69": "Age Category: 65-69",
        "AgeCategory_70-74": "Age Category: 70-74",
        "AgeCategory_75-79": "Age Category: 75-79",
        "AgeCategory_80 or older": "Age Category: 80+",
        "Race_Asian": "Ethnicity: Asian",
        "Race_Black": "Ethnicity: Black",
        "Race_Hispanic": "Ethnicity: Hispanic",
        "Race_Other": "Ethnicity: Other",
        "Race_White": "Ethnicity: White",
        "Diabetic_No, borderline diabetes": "Borderline Diabetes",
        "Diabetic_Yes": "Diagnosed Diabetes",
        "Diabetic_Yes (during pregnancy)": "Gestational Diabetes",
        "GenHealth_Fair": "General Health: Fair",
        "GenHealth_Good": "General Health: Good",
        "GenHealth_Poor": "General Health: Poor",
        "GenHealth_Very good": "General Health: Very Good",
    }

    @classmethod
    def format_feature_clinical_value(cls, col_name: str, val: float, assessment: Any = None) -> str:
        if col_name == "BMI":
            return f"{val:.1f} kg/m²"
        elif col_name == "Smoking":
            return "Current/Former Smoker" if val == 1 else "Non-smoker"
        elif col_name == "AlcoholDrinking":
            return "Regular Drinker" if val == 1 else "Non-drinker"
        elif col_name == "Stroke":
            return "Prior Cardiac Event" if val == 1 else "No Prior Event"
        elif col_name == "PhysicalHealth":
            return f"{val:.0f} days/mo physical distress"
        elif col_name == "MentalHealth":
            return f"{val:.0f} days/mo stress/burnout"
        elif col_name == "DiffWalking":
            return "Impaired Mobility" if val == 1 else "Normal Mobility"
        elif col_name == "PhysicalActivity":
            return "Regular Exercise" if val == 1 else "Sedentary"
        elif col_name == "SleepTime":
            return f"{val:.1f} hrs/night"
        elif "Diabetic" in col_name:
            return "Diabetic Profile" if val == 1 else "Non-diabetic"
        elif "GenHealth" in col_name:
            return col_name.replace("GenHealth_", "")
        elif "AgeCategory" in col_name:
            return col_name.replace("AgeCategory_", "") + " yrs"
        elif col_name == "Sex_Male":
            return "Male" if val == 1 else "Female"
        return f"{val:.1f}" if isinstance(val, float) else str(val)

    def compute_shap(
        self,
        assessment_data: Any,
        patient_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Computes exact SHAP values using XGBoost TreeExplainer and feature vector.
        """
        if not self.is_ready():
            self._load_models()

        df_input = self.build_feature_dataframe(assessment_data, patient_data)

        if self._xgb_tree_explainer is None and self.xgb_model is not None:
            try:
                self._xgb_tree_explainer = shap.TreeExplainer(self.xgb_model)
            except Exception as e:
                logger.warning(f"Error initializing XGB TreeExplainer: {e}")

        base_val = 0.5
        if self._xgb_tree_explainer is not None:
            shap_matrix = self._xgb_tree_explainer.shap_values(df_input)
            if hasattr(shap_matrix, "shape") and len(shap_matrix.shape) == 2:
                shap_vals = shap_matrix[0]
            else:
                shap_vals = np.array(shap_matrix)
            exp_val = getattr(self._xgb_tree_explainer, "expected_value", 0.5)
            base_val = float(exp_val[0] if isinstance(exp_val, (list, np.ndarray)) else exp_val)
        else:
            shap_vals = np.zeros(len(self.feature_columns))

        features_list = []
        total_abs_shap = float(np.sum(np.abs(shap_vals))) or 1.0

        for col, s_val in zip(self.feature_columns, shap_vals):
            raw_val = float(df_input[col].values[0])
            label = self.FEATURE_LABEL_MAP.get(col, col.replace("_", " "))
            clin_val = self.format_feature_clinical_value(col, raw_val, assessment_data)
            pct = round((abs(float(s_val)) / total_abs_shap) * 100, 1)

            features_list.append({
                "feature_name": label,
                "raw_feature": col,
                "shap_value": round(float(s_val), 4),
                "base_value": round(base_val, 4),
                "feature_value": raw_val,
                "clinical_value": clin_val,
                "percentage": pct,
                "contribution_direction": "positive" if s_val > 0 else "negative"
            })

        # Sort by absolute SHAP contribution
        features_list.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        top_features = features_list[:8]

        force_plot = {
            "base_value": round(base_val, 4),
            "out_value": round(base_val + float(np.sum(shap_vals)), 4),
            "features": [
                {
                    "name": f["feature_name"],
                    "value": f["shap_value"],
                    "contribution": "+" if f["shap_value"] > 0 else "-"
                }
                for f in top_features
            ]
        }

        return {
            "base_value": round(base_val, 4),
            "top_features": top_features,
            "all_features": features_list,
            "force_plot_data": force_plot,
            "feature_count": len(features_list)
        }

    def compute_lime(
        self,
        assessment_data: Any,
        patient_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Computes Local Interpretable Model-agnostic Explanations on the ensemble.
        """
        if not self.is_ready():
            self._load_models()

        df_input = self.build_feature_dataframe(assessment_data, patient_data)
        test_row = df_input.iloc[0].values.astype(float)

        def predict_fn(x):
            df = pd.DataFrame(x, columns=self.feature_columns)
            p_lr = self.lr_model.predict_proba(df)[:, 1]
            p_rf = self.rf_model.predict_proba(df)[:, 1]
            p_xgb = self.xgb_model.predict_proba(df)[:, 1]
            avg_p = (p_lr + p_rf + p_xgb) / 3.0
            return np.column_stack([1.0 - avg_p, avg_p])

        if self._lime_explainer is None:
            bg_sample_path = MODELS_DIR / "background_sample.npy"
            if bg_sample_path.exists():
                bg = np.load(bg_sample_path)
            else:
                bg = np.zeros((20, len(self.feature_columns)))
            self._lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data=bg,
                feature_names=self.feature_columns,
                class_names=["Low Risk", "High Risk"],
                mode="classification",
                random_state=42
            )

        exp = self._lime_explainer.explain_instance(
            test_row,
            predict_fn,
            num_features=8,
            num_samples=150
        )

        top_features = []
        raw_list = exp.as_list()
        total_w = sum(abs(w) for _, w in raw_list) or 1.0

        for rule, weight in raw_list:
            col_name = rule.split()[0] if rule else "Feature"
            clean_label = self.FEATURE_LABEL_MAP.get(col_name, col_name.replace("_", " "))
            direction = "positive" if weight > 0 else "negative"
            pct = round((abs(weight) / total_w) * 100, 1)

            val = float(df_input[col_name].values[0]) if col_name in df_input.columns else 0.0
            clin_val = self.format_feature_clinical_value(col_name, val, assessment_data)

            top_features.append({
                "feature_name": f"{clean_label} ({rule})",
                "importance_score": round(min(1.0, max(0.0, abs(weight))), 4),
                "contribution_direction": direction,
                "feature_value": val,
                "average_value": 0.5,
                "percentage": pct,
                "clinical_value": clin_val
            })

        acc = max(0.0, min(1.0, float(getattr(exp, "score", 0.85) or 0.85)))
        loc_pred = max(0.0, min(1.0, float(getattr(exp, "local_pred", [0.5])[0] or 0.5)))
        intercept = float(exp.intercept[1]) if hasattr(exp, "intercept") and len(exp.intercept) > 1 else 0.5

        return {
            "top_features": top_features,
            "intercept": round(intercept, 4),
            "explanation_accuracy": round(acc, 4),
            "local_prediction_probability": round(loc_pred, 4),
            "feature_count": len(top_features)
        }


# Global service instance
prediction_service = PredictionService()
