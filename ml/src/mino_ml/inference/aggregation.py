from typing import List
import numpy as np

def aggregate_frame_scores(scores: List[float], method: str = "top_k_mean", k: int = 3) -> float:
    """
    Evaluates video-level manipulation score from sampled valid face frames.
    Methods:
    - top_k_mean: Average of top K highest risk frames (captures localized face swap moments).
    - mean: Average across all valid frames.
    - median: Median risk across all valid frames.
    """
    if not scores:
        return 0.5  # Inconclusive neutral default

    arr = np.array(scores, dtype=float)

    if method == "mean":
        return float(np.mean(arr))
    elif method == "median":
        return float(np.median(arr))
    elif method == "top_k_mean":
        top_k = sorted(scores, reverse=True)[:min(k, len(scores))]
        return float(np.mean(top_k))
    else:
        return float(np.mean(arr))
