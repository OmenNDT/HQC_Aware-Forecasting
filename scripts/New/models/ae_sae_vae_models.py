"""ae_sae_vae_models.py — Autoencoder, Sparse AE, Variational AE (PyTorch) theo kiến trúc quy đổi từ paper.

  AE      24-28-12-6-12-28-24, tanh, RMSProp 1e-4      (paper 14-17-8-4-8-17-14)
  AE nhỏ  24-12-6-12-24,       tanh, RMSProp 1e-4
  SAE     24-24×5-24, phạt L1 trên kích hoạt β,  RMSProp 1e-4 (paper mọi lớp = 14)
  VAE     24-28-14 → z=8 → 14-28-24, MSE + KL, mini-batch SGD 1e-3; chấm bằng trung bình 16 lần lấy mẫu
Scaler min-max [-1, 1] (đầu ra tanh). Dừng sớm theo loss tái tạo trên val, kiên nhẫn 20, tối đa 300 epoch.
"""
import numpy as np
import torch
import torch.nn as nn
from .reconstruction_base import ReconstructionModel

torch.set_num_threads(8)
DEV = "cpu"                                  # dữ liệu nhỏ (≈4k × 24): CPU nhanh hơn chi phí chuyển GPU


def mlp(sizes, act_last=True):
    layers = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2 or act_last:
            layers.append(nn.Tanh())
    return nn.Sequential(*layers)


class TorchRecon(ReconstructionModel):
    scaler_kind = "minmax"
    max_epochs, patience, batch = 300, 20, 64

    def __init__(self, seed=0, lr=1e-4, opt="rmsprop"):
        self.seed, self.lr, self.opt_name = seed, lr, opt

    def n_params(self):
        return sum(p.numel() for p in self.net.parameters())

    def build(self):
        raise NotImplementedError

    def loss(self, x):
        """Trả (loss tối ưu, MSE tái tạo) cho một batch."""
        xh = self.net(x)
        mse = ((xh - x) ** 2).mean()
        return mse, mse

    def fit(self, Xtr, Xval=None):
        torch.manual_seed(self.seed); np.random.seed(self.seed)
        self.build(); self.net.to(DEV)
        opt = (torch.optim.RMSprop if self.opt_name == "rmsprop" else torch.optim.SGD)(self.net.parameters(), lr=self.lr)
        Xt = torch.tensor(Xtr, dtype=torch.float32, device=DEV)
        Xv = torch.tensor(Xval, dtype=torch.float32, device=DEV) if Xval is not None and len(Xval) else None
        best, best_state, bad, self.epochs_ = np.inf, None, 0, 0
        for ep in range(self.max_epochs):
            self.net.train(); perm = torch.randperm(len(Xt))
            for i in range(0, len(Xt), self.batch):
                opt.zero_grad(); l, _ = self.loss(Xt[perm[i:i + self.batch]]); l.backward(); opt.step()
            self.epochs_ = ep + 1
            if Xv is None:
                continue
            self.net.eval()
            with torch.no_grad():
                _, v = self.loss(Xv)
            v = float(v)
            if v < best - 1e-6:
                best, bad, best_state = v, 0, {k: t.clone() for k, t in self.net.state_dict().items()}
            else:
                bad += 1
                if bad >= self.patience:
                    break
        if best_state is not None:
            self.net.load_state_dict(best_state)
        self.net.eval(); self.val_mse_ = best if Xv is not None else np.nan
        return self

    def reconstruct(self, X):
        with torch.no_grad():
            return self.net(torch.tensor(X, dtype=torch.float32, device=DEV)).cpu().numpy()


class AEModel(TorchRecon):
    def __init__(self, hidden=(28, 12, 6, 12, 28), seed=0):
        super().__init__(seed=seed, lr=1e-4, opt="rmsprop")
        self.hidden = tuple(hidden)
        self.name = ("AE" if len(hidden) == 5 else "AEsmall") + f"_s{seed}"

    def build(self):
        self.net = mlp([24, *self.hidden, 24], act_last=True)


class SAEModel(TorchRecon):
    """Mọi lớp ẩn = 24 nút; phạt L1 trên kích hoạt của các lớp ẩn (β)."""

    def __init__(self, beta=1e-3, seed=0):
        super().__init__(seed=seed, lr=1e-4, opt="rmsprop")
        self.beta = beta; self.name = f"SAE_b{beta:g}_s{seed}"

    def build(self):
        self.net = mlp([24] * 6 + [24], act_last=True)

    def loss(self, x):
        h, act = x, 0.0
        for layer in self.net:
            h = layer(h)
            if isinstance(layer, nn.Tanh):
                act = act + h.abs().mean()
        mse = ((h - x) ** 2).mean()
        return mse + self.beta * act, mse


class VAEModel(TorchRecon):
    """Encoder 24-28-14 → (μ, logσ²) 8 chiều → decoder 14-28-24 tanh. Chấm bằng trung bình 16 mẫu z."""
    n_draws = 16

    def __init__(self, latent=8, beta_kl=1.0, seed=0):
        super().__init__(seed=seed, lr=1e-3, opt="sgd")
        self.latent, self.beta_kl = latent, beta_kl; self.name = f"VAE_z{latent}_s{seed}"

    def build(self):
        self.enc = mlp([24, 28, 14], act_last=True)
        self.mu, self.logvar = nn.Linear(14, self.latent), nn.Linear(14, self.latent)
        self.dec = mlp([self.latent, 14, 28, 24], act_last=True)
        self.net = nn.ModuleList([self.enc, self.mu, self.logvar, self.dec])

    def forward_sample(self, x, sample=True):
        h = self.enc(x); mu, lv = self.mu(h), self.logvar(h)
        z = mu + torch.randn_like(mu) * torch.exp(0.5 * lv) if sample else mu
        return self.dec(z), mu, lv

    def loss(self, x):
        xh, mu, lv = self.forward_sample(x, sample=True)
        mse = ((xh - x) ** 2).mean()
        kl = -0.5 * torch.mean(1 + lv - mu ** 2 - lv.exp())
        return mse + self.beta_kl * kl, mse

    def reconstruct(self, X):
        """Trung bình 16 mẫu z với bộ sinh ngẫu nhiên riêng (không đụng RNG toàn cục, không phụ thuộc batch)."""
        x = torch.tensor(X, dtype=torch.float32, device=DEV)
        g = torch.Generator(device=DEV).manual_seed(self.seed + 1000)
        with torch.no_grad():
            h = self.enc(x); mu, lv = self.mu(h), self.logvar(h); std = torch.exp(0.5 * lv)
            xs = [self.dec(mu + torch.randn(mu.shape, generator=g, device=DEV) * std) for _ in range(self.n_draws)]
            return torch.stack(xs).mean(0).cpu().numpy()
