import os
import json
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import Dict, Any, List

def evaluate_model_predictions(y_true: List[int], y_pred_prob: List[float], threshold: float = 0.5) -> Dict[str, Any]:
    y_true_arr = np.array(y_true)
    y_prob_arr = np.array(y_pred_prob)
    y_pred_arr = (y_prob_arr >= threshold).astype(int)

    roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))
    cm = confusion_matrix(y_true_arr, y_pred_arr).tolist()

    return {
        "sample_count": len(y_true),
        "threshold": threshold,
        "roc_auc": round(roc_auc, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "confusion_matrix": cm,
    }

if __name__ == "__main__":
    # Benchmark synthetic run verification
    y_t = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    y_p = [0.1, 0.2, 0.35, 0.15, 0.4, 0.85, 0.9, 0.7, 0.95, 0.6]
    metrics = evaluate_model_predictions(y_t, y_p)
    print("Baseline Evaluation Metrics:")
    print(json.dumps(metrics, indent=2))
