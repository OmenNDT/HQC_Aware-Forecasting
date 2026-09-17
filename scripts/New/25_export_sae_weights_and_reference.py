#!/usr/bin/env python3
"""25_export_sae_weights_and_reference.py — Phase 04 ngày 1: xuất trọng số SAE đã khóa và SPE tham chiếu (float).

Đọc Dataclean_new/models/SAE_b0.001_s0.pkl (khóa phase 02) → Dataclean_new/embed/sae_float.npz (W[6,24,24], b[6,24], scaler a,b[8],
FEATURES) + sae_reference_spe.parquet (SPE float từng mẫu 10 phút, chấm theo đoạn liên tục như script 20).
Tự kiểm: SPE tham chiếu phải trùng tier_b45_daily.spe (phần không phải blind) tới 1e-6 tương đối; lệch là dừng.
"""
import hashlib, json, os, pickle, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import FEATURES, to_matrix                # noqa: E402
from alarm_utils import load_script                                       # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); cv13 = load_script("cv13", "13_blocked_cv_train_compare.py", HERE)
EMBED = f"{DATA_NEW}/embed"


def main():
    lock2 = json.load(open(f"{DATA_NEW}/locked_params_phase02.json")); model = lock2["model"]
    pkl = f"{MODEL_DIR}/{model}.pkl"; obj = pickle.load(open(pkl, "rb")); m, sc = obj["model"], obj["scaler"]
    sd = m.net.state_dict(); lin = sorted({int(k.split(".")[0]) for k in sd})
    W = np.stack([sd[f"{i}.weight"].cpu().numpy() for i in lin]).astype(np.float32)   # (6, out=24, in=24)
    b = np.stack([sd[f"{i}.bias"].cpu().numpy() for i in lin]).astype(np.float32)
    assert W.shape == (6, 24, 24) and sc.kind == "minmax", (W.shape, sc.kind)
    os.makedirs(EMBED, exist_ok=True)
    np.savez(f"{EMBED}/sae_float.npz", W=W, b=b, scaler_a=sc.a.astype(np.float32), scaler_b=sc.b.astype(np.float32),
             features=np.array(FEATURES), model=model, pkl_sha256=hashlib.sha256(open(pkl, "rb").read()).hexdigest())
    # SPE tham chiếu float trên toàn kho 10 phút (mọi vai trò, kể cả blind), chấm theo đoạn liên tục
    fs = pd.read_parquet(FEATURE_STORE); fs10 = fs[fs.cadence_min == 10]
    spe = cv13.score_segments(m, sc, fs10)
    # kiểm bằng numpy thuần (không torch) — cùng công thức sẽ port sang C
    X = sc.transform(to_matrix(fs10)); h = X.copy()
    for l in range(6): h = np.tanh(h @ W[l].T + b[l])
    spe_np = np.sum((X - h) ** 2, axis=1)
    rel = np.nanmax(np.abs(spe_np - spe.values) / np.maximum(spe.values, 1e-9)); assert rel < 1e-4, f"numpy ≠ torch: {rel}"
    ref = pd.read_parquet(f"{DATA_NEW}/tier_b45_daily.parquet").spe
    common = spe.index.intersection(ref.index); d = np.nanmax(np.abs(spe[common] - ref[common]) / np.maximum(ref[common], 1e-9))
    assert d < 1e-6, f"SPE tham chiếu lệch tier_b45_daily: {d}"
    out = pd.DataFrame({"spe_float": spe.values, "role": fs10.role.values, "episode": fs10.episode.values}, index=spe.index)
    out.to_parquet(f"{EMBED}/sae_reference_spe.parquet")
    print(f"{model}: W {W.shape}, b {b.shape}, scaler a={np.round(sc.a, 2)}, b={np.round(sc.b, 2)}")
    print(f"SPE tham chiếu: {len(out)} mẫu, trùng tier_b45_daily ({len(common)} mẫu chung, lệch max {d:.1e}); numpy vs torch {rel:.1e} → {EMBED}")


if __name__ == "__main__":
    main()
