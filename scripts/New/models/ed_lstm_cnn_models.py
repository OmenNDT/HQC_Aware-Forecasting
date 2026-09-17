"""ed_lstm_cnn_models.py — Encoder–Decoder LSTM và Encoder–Decoder CNN trên cửa sổ 20 bước × 24 đặc trưng.

Cửa sổ NHÂN QUẢ: mẫu tại t dùng [t−19, t]; mô hình tái tạo cả cửa sổ, điểm SPE tại t lấy trên
bước cuối cửa sổ (chỉ bước t) để so được với mô hình điểm. 19 hàng đầu của mỗi đoạn không có điểm (NaN).

ED-LSTM: LSTM 16 → 10 → 16 → Linear 24, tanh; SGD 1e-3, batch 100           (paper 10,7,10)
ED-CNN : ảnh 1×24×20 → Conv16 8×8 → pool(2,2) → Conv8 3×3 → pool(2,2) → Conv8 3×3 → up(2,1)
         → Conv16 3×3 → up(2,2) → Conv1 8×8 tanh; Adam 1e-3                (paper Bảng 7)
Cả hai fit/score qua TorchRecon; dữ liệu vào là ma trận (n, 24) đã scale, cửa sổ tự dựng bên trong.
"""
import numpy as np
import torch
import torch.nn as nn
from .ae_sae_vae_models import TorchRecon, DEV

WIN = 20


def windows(X, win=WIN):
    """(n, 24) → (n−win+1, win, 24), cửa sổ kết thúc tại t = win−1 … n−1."""
    n = len(X)
    if n < win:
        return np.empty((0, win, X.shape[1]), dtype=np.float32)
    idx = np.arange(win)[None, :] + np.arange(n - win + 1)[:, None]
    return X[idx].astype(np.float32)


class WindowedRecon(TorchRecon):
    window = WIN

    def _fit_windows(self, Xtr, Xval):
        Wtr, Wva = windows(Xtr), (windows(Xval) if Xval is not None else None)
        # TorchRecon.fit làm việc trên "hàng"; ở đây mỗi hàng là một cửa sổ đã phẳng hóa
        return super().fit(Wtr.reshape(len(Wtr), -1), Wva.reshape(len(Wva), -1) if Wva is not None and len(Wva) else None)

    def fit(self, Xtr, Xval=None):
        return self._fit_windows(Xtr, Xval)

    def fit_segments(self, segments_tr, segments_val=None):
        """Dựng cửa sổ TRONG từng đoạn liên tục rồi mới nối — không cửa sổ nào vắt qua ranh giới khối."""
        Wtr = np.vstack([windows(s) for s in segments_tr if len(s) >= WIN])
        Wva = np.vstack([windows(s) for s in segments_val if len(s) >= WIN]) if segments_val else None
        return TorchRecon.fit(self, Wtr.reshape(len(Wtr), -1), Wva.reshape(len(Wva), -1) if Wva is not None and len(Wva) else None)

    def reconstruct(self, X):
        """Trả X̂ cùng cỡ (n, 24): hàng t = bước cuối của cửa sổ tái tạo kết thúc tại t; 19 hàng đầu NaN."""
        W = windows(X); out = np.full(X.shape, np.nan, dtype=np.float32)
        if len(W) == 0:
            return out
        with torch.no_grad():
            xh = self.net(torch.tensor(W.reshape(len(W), -1), dtype=torch.float32, device=DEV)).cpu().numpy()
        out[WIN - 1:] = xh.reshape(len(W), WIN, -1)[:, -1, :]
        return out


class LSTMNet(nn.Module):
    def __init__(self, n_feat=24, h=(16, 10, 16)):
        super().__init__()
        self.l1, self.l2, self.l3 = nn.LSTM(n_feat, h[0], batch_first=True), nn.LSTM(h[0], h[1], batch_first=True), nn.LSTM(h[1], h[2], batch_first=True)
        self.out = nn.Linear(h[2], n_feat)

    def forward(self, x):                     # x: (b, win*24) phẳng → (b, win, 24)
        b = x.shape[0]; s = x.view(b, WIN, -1)
        s, _ = self.l1(s); s, _ = self.l2(s); s, _ = self.l3(s)
        return torch.tanh(self.out(s)).reshape(b, -1)


class EDLSTMModel(WindowedRecon):
    batch = 100

    def __init__(self, seed=0):
        super().__init__(seed=seed, lr=1e-3, opt="sgd"); self.name = f"EDLSTM_s{seed}"

    def build(self):
        self.net = LSTMNet()


class CNNNet(nn.Module):
    """Ảnh 1 × 24 (đặc trưng) × 20 (thời gian), padding same, kích thước giữ theo paper."""

    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Conv2d(1, 16, 8, padding="same"), nn.ReLU(), nn.MaxPool2d((2, 2)),
                                 nn.Conv2d(16, 8, 3, padding="same"), nn.ReLU(), nn.MaxPool2d((2, 2)),
                                 nn.Conv2d(8, 8, 3, padding="same"), nn.ReLU())
        self.dec = nn.Sequential(nn.Upsample(scale_factor=(2, 1)), nn.Conv2d(8, 16, 3, padding="same"), nn.ReLU(),
                                 nn.Upsample(scale_factor=(2, 4)), nn.Conv2d(16, 1, 8, padding="same"), nn.Tanh())

    def forward(self, x):                     # x: (b, win*24) → ảnh (b,1,24,20)
        b = x.shape[0]; img = x.view(b, WIN, 24).transpose(1, 2).unsqueeze(1)
        y = self.dec(self.enc(img))           # 24×20 → 12×10 → 6×5 → 12×5 → 24×20 (up (2,4) khôi phục đủ trục thời gian)
        return y.squeeze(1).transpose(1, 2).reshape(b, -1)


class EDCNNModel(WindowedRecon):
    batch = 64

    def __init__(self, seed=0):
        super().__init__(seed=seed, lr=1e-3, opt="adam"); self.name = f"EDCNN_s{seed}"

    def build(self):
        self.net = CNNNet()
