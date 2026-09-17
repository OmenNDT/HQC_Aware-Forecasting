"""dbn_rbm_model.py — Deep Belief Network = 3 RBM xếp chồng (24→28→22→18), tái tạo bằng lượt xuống.

Theo paper: k (CD-k) = 10, tốc độ học 0,003, batch 25; residual lọc trung bình trượt 50 mẫu (paper Hình 11).
RBM tầng đầu Gauss–Bernoulli (đầu vào thực đã scale [-1,1]); các tầng trên Bernoulli–Bernoulli.
Tái tạo: x → p(h1|x) → p(h2|h1) → p(h3|h2) → ngược xuống bằng kỳ vọng (không lấy mẫu) → x̂.
Dừng sớm theo sai số tái tạo một lượt xuống trên val cho TỪNG RBM khi xếp chồng.
"""
import numpy as np
import torch
from .reconstruction_base import ReconstructionModel

DEV = "cpu"


class RBM:
    def __init__(self, n_vis, n_hid, gaussian_visible, seed):
        g = torch.Generator().manual_seed(seed)
        self.W = torch.randn(n_vis, n_hid, generator=g) * 0.01
        self.bv, self.bh = torch.zeros(n_vis), torch.zeros(n_hid)
        self.gauss = gaussian_visible

    def n_params(self):
        return self.W.numel() + self.bv.numel() + self.bh.numel()

    def p_h(self, v):
        return torch.sigmoid(v @ self.W + self.bh)

    def mean_v(self, h):
        a = h @ self.W.T + self.bv
        return a if self.gauss else torch.sigmoid(a)

    def cd_k(self, v0, k, lr):
        """Một bước Contrastive Divergence-k trên một batch."""
        ph0 = self.p_h(v0); h = torch.bernoulli(ph0); v = v0
        for _ in range(k):
            v = self.mean_v(h)
            if not self.gauss:
                v = torch.bernoulli(v)
            ph = self.p_h(v); h = torch.bernoulli(ph)
        self.W += lr * (v0.T @ ph0 - v.T @ ph) / len(v0)
        self.bv += lr * (v0 - v).mean(0); self.bh += lr * (ph0 - ph).mean(0)

    def recon_err(self, v):
        return float(((self.mean_v(self.p_h(v)) - v) ** 2).mean())


class DBNModel(ReconstructionModel):
    scaler_kind = "minmax"
    smooth = 50                      # trung bình trượt trên SPE, theo paper
    max_epochs, patience, batch, k_cd, lr = 200, 15, 25, 10, 3e-3

    def __init__(self, hidden=(28, 22, 18), seed=0):
        self.hidden, self.seed = tuple(hidden), seed; self.name = f"DBN_s{seed}"

    def n_params(self):
        return sum(r.n_params() for r in self.rbms)

    def fit(self, Xtr, Xval=None):
        torch.manual_seed(self.seed)
        Xt = torch.tensor(Xtr, dtype=torch.float32); Xv = torch.tensor(Xval, dtype=torch.float32) if Xval is not None and len(Xval) else None
        self.rbms, sizes, self.epochs_ = [], (24, *self.hidden), 0
        vt, vv = Xt, Xv
        for li in range(len(self.hidden)):
            rbm = RBM(sizes[li], sizes[li + 1], gaussian_visible=(li == 0), seed=self.seed * 10 + li)
            best, bad, best_state = np.inf, 0, None
            for ep in range(self.max_epochs):
                perm = torch.randperm(len(vt))
                for i in range(0, len(vt), self.batch):
                    rbm.cd_k(vt[perm[i:i + self.batch]], self.k_cd, self.lr)
                self.epochs_ += 1
                if vv is None:
                    continue
                e = rbm.recon_err(vv)
                if e < best - 1e-6:
                    best, bad, best_state = e, 0, (rbm.W.clone(), rbm.bv.clone(), rbm.bh.clone())
                else:
                    bad += 1
                    if bad >= self.patience:
                        break
            if best_state is not None:
                rbm.W, rbm.bv, rbm.bh = best_state
            self.rbms.append(rbm)
            vt = rbm.p_h(vt); vv = rbm.p_h(vv) if vv is not None else None    # đầu vào cho tầng kế = kỳ vọng ẩn
        self.val_mse_ = float(np.mean((self.reconstruct(Xval) - Xval) ** 2)) if Xv is not None else np.nan
        return self

    def reconstruct(self, X):
        v = torch.tensor(X, dtype=torch.float32)
        hs = []
        for rbm in self.rbms:
            v = rbm.p_h(v); hs.append(v)
        for rbm in reversed(self.rbms):
            v = rbm.mean_v(v)
        return v.numpy()

    def score(self, X):
        """SPE rồi lọc trung bình trượt 50 mẫu (nhân quả) như paper làm với DBN."""
        spe = super().score(X)
        out = np.full_like(spe, np.nan)       # 49 hàng đầu chưa đủ cửa sổ lọc → NaN (không trả giá trị thô)
        if len(spe) < self.smooth:
            return out
        c = np.cumsum(np.insert(spe, 0, 0.0))
        out[self.smooth - 1:] = (c[self.smooth:] - c[:-self.smooth]) / self.smooth
        return out
