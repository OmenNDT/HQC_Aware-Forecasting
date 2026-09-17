"""reconstruction_base.py — Lớp cơ sở cho mọi mô hình tái tạo của phase 01.

Hợp đồng chung (mục 3 phase 01):
  - Scaler fit trên train của từng fold; 'z' cho PCA, 'minmax' về [-1, 1] theo p1–p99 cho mạng nơ-ron.
    Cột sin/cos đã trong [-1, 1] → giữ nguyên (không scale).
  - SPE = Σ (x − x̂)² trên 24 chiều đã scale; MAE giữ để đối chiếu paper.
  - Đóng góp kênh j = (r²amp + r²sin + r²cos)_j / SPE, đủ 8 kênh.
"""
import numpy as np
import pandas as pd

CH = ["2001X", "2001Y", "2003X", "2003Y", "2005X", "2005Y", "2007X", "2007Y"]
FEATURES = [f"amp_{c}" for c in CH] + [f"sin_{c}" for c in CH] + [f"cos_{c}" for c in CH]
AMP_IDX = np.arange(0, 8)          # vị trí 8 cột amp trong vector 24 chiều


class Scaler:
    """'z': z-score; 'minmax': co về [-1, 1] theo p1–p99. Chỉ áp lên 8 cột amp."""

    def __init__(self, kind="z"):
        self.kind = kind

    def fit(self, X):
        A = X[:, AMP_IDX]
        if self.kind == "z":
            self.a, self.b = A.mean(0), A.std(0)
            self.b[self.b < 1e-9] = 1.0
        else:
            lo, hi = np.percentile(A, 1, axis=0), np.percentile(A, 99, axis=0)
            self.a, self.b = (lo + hi) / 2, (hi - lo) / 2
            self.b[self.b < 1e-9] = 1.0
        return self

    def transform(self, X):
        Z = X.astype(float).copy()
        Z[:, AMP_IDX] = (Z[:, AMP_IDX] - self.a) / self.b
        return Z


class ReconstructionModel:
    """Giao diện: fit(Xtr, Xval) → self; reconstruct(X) → X̂; score(X) → SPE; contribution(X) → (n, 8)."""
    name = "base"
    scaler_kind = "z"
    window = 1                       # >1 cho mô hình cửa sổ (LSTM, CNN); điểm tại t dùng [t-window+1, t]

    def n_params(self):
        raise NotImplementedError

    def fit(self, Xtr, Xval=None):
        raise NotImplementedError

    def reconstruct(self, X):
        raise NotImplementedError

    def residual(self, X):
        return X - self.reconstruct(X)

    def score(self, X):
        """SPE theo hàng; hàng không tái tạo được (đầu cửa sổ) trả NaN, không phải 0."""
        r = self.residual(X)
        spe = np.nansum(r ** 2, axis=1)
        spe[np.isnan(r).all(axis=1)] = np.nan
        return spe

    def fit_segments(self, segments_tr, segments_val=None):
        """Fit trên danh sách đoạn liên tục (không cho cửa sổ vắt qua chỗ nối). Mặc định: nối lại rồi fit."""
        Xtr = np.vstack(segments_tr)
        Xval = np.vstack(segments_val) if segments_val else None
        return self.fit(Xtr, Xval)

    def mae(self, X):
        return np.nanmean(np.abs(self.residual(X)), axis=1)

    def contribution(self, X):
        r2 = self.residual(X) ** 2
        per = r2[:, 0:8] + r2[:, 8:16] + r2[:, 16:24]
        tot = per.sum(1, keepdims=True)
        tot[tot == 0] = 1.0
        return per / tot


def to_matrix(df):
    """DataFrame kho đặc trưng → ma trận (n, 24) đúng thứ tự FEATURES."""
    return df[FEATURES].to_numpy(dtype=float)


def spe_series(model, scaler, df):
    """Chấm SPE cho một DataFrame kho đặc trưng, trả Series theo ts (mô hình cửa sổ tự xử lý NaN đầu)."""
    return pd.Series(model.score(scaler.transform(to_matrix(df))), index=df.index, name="spe")
