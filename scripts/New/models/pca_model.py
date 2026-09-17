"""pca_model.py — PCA tái tạo (đường cơ sở tuyến tính), k thành phần.

Phần dư = khoảng cách vuông góc tới không gian con k chiều. Không có epoch; val dùng cho
đường cong học theo k (script 13 ghi val MSE).
"""
import numpy as np
from .reconstruction_base import ReconstructionModel


class PCAModel(ReconstructionModel):
    scaler_kind = "z"

    def __init__(self, k=6):
        self.k = k
        self.name = f"PCA_k{k}"

    def n_params(self):
        return 24 * self.k + 24 + 48          # W (k×24) + tâm 24 + mu/sd 48

    def fit(self, Xtr, Xval=None):
        self.mean_ = Xtr.mean(0)
        _, _, Vt = np.linalg.svd(Xtr - self.mean_, full_matrices=False)
        self.W_ = Vt[: self.k]                 # (k, 24)
        return self

    def reconstruct(self, X):
        Z = X - self.mean_
        return (Z @ self.W_.T) @ self.W_ + self.mean_
