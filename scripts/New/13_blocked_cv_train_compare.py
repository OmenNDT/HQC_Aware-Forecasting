#!/usr/bin/env python3
"""13_blocked_cv_train_compare.py — Kiểm định chéo 5 khối ba vai trên nền 9b, cho mọi mô hình.

Bản sửa theo code review 03/09 22:50:
  - KHÔNG chấm đoạn 11 (blind) ở đây; mô hình fit lại được lưu (pickle) để script 15 tự chấm sau khi khóa.
  - Fit lại trên toàn 9b với số epoch = trung bình các fold (không train "mù" 300 epoch).
  - Đoạn liên tục cắt theo khoảng trống > 1 giờ (không chỉ theo khối/episode) cho cửa sổ và lọc trượt.
  - Giới hạn 99% trên MẪU 6 giờ một điểm; báo FA cả 6 giờ và 10 phút.
  - Dốc log SPE tính trên chuỗi liên tục theo thời gian (9b→9c liền nhau) theo ngày lịch, cửa sổ 14 ngày.
  - Mỗi mô hình ghi một file JSON riêng (không đua ghi CSV); script 14 gộp.
  - Từ chối chạy khi đã có locked_params.json, trừ khi --force (tránh làm lệch hash sau khi khóa).

Chạy: python scripts/New/13_blocked_cv_train_compare.py --models pca|ae|deep [--force]
"""
import argparse, json, os, pickle, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase01_config import *                                              # noqa: F401,F403,E402
from models.reconstruction_base import Scaler, to_matrix                   # noqa: E402
from models.pca_model import PCAModel                                      # noqa: E402

SEEDS = (0, 1, 2)


def model_zoo(names):
    zoo = []
    if "pca" in names:
        zoo += [(f"PCA_k{k}", (lambda k=k: PCAModel(k))) for k in (2, 3, 4, 5, 6, 8)]
    if "ae" in names:
        from models.ae_sae_vae_models import AEModel, SAEModel, VAEModel
        for s in SEEDS:
            zoo += [(f"AE_s{s}", (lambda s=s: AEModel(seed=s))), (f"AEsmall_s{s}", (lambda s=s: AEModel(hidden=(12, 6, 12), seed=s))),
                    (f"SAE_b0.001_s{s}", (lambda s=s: SAEModel(beta=1e-3, seed=s))), (f"VAE_z8_s{s}", (lambda s=s: VAEModel(seed=s)))]
    if "deep" in names:
        from models.dbn_rbm_model import DBNModel
        from models.ed_lstm_cnn_models import EDLSTMModel, EDCNNModel
        for s in SEEDS:
            zoo += [(f"DBN_s{s}", (lambda s=s: DBNModel(seed=s))), (f"EDLSTM_s{s}", (lambda s=s: EDLSTMModel(seed=s))),
                    (f"EDCNN_s{s}", (lambda s=s: EDCNNModel(seed=s)))]
    return zoo


def contiguous_segments(idx, gap=SEGMENT_GAP):
    """Chia index thời gian thành các đoạn liên tục (khoảng cách > gap thì cắt). Trả list mặt nạ bool."""
    brk = np.r_[True, np.diff(idx.values) > gap.to_timedelta64()]
    seg_id = np.cumsum(brk)
    return [seg_id == s for s in np.unique(seg_id)]


def make_blocks(idx):
    edges = pd.date_range(idx.min(), idx.max(), periods=N_BLOCKS + 1)
    blk = np.searchsorted(edges[1:-1], idx.values, side="right")
    keep = np.ones(len(idx), bool)
    for e in edges[1:-1]:
        keep &= ~((idx >= e - pd.Timedelta(hours=PURGE_H)) & (idx <= e + pd.Timedelta(hours=PURGE_H)))
    return blk, keep


def segments_of(X, idx, mask):
    """Các đoạn liên tục (theo thời gian) của những dòng nằm trong mask, dưới dạng ma trận con của X."""
    pos = np.flatnonzero(mask)
    return [X[pos[seg]] for seg in contiguous_segments(idx[pos]) if seg.sum() > 0]


def score_segments(m, sc, df):
    parts = []
    for mask in contiguous_segments(df.index):
        g = df[mask]
        parts.append(pd.Series(m.score(sc.transform(to_matrix(g))), index=g.index))
    return pd.concat(parts).sort_index()


def run_cv(factory, tr):
    X = to_matrix(tr); idx = tr.index; blk, keep = make_blocks(idx)
    oos = pd.Series(np.nan, index=idx); fold_id = pd.Series(-1, index=idx); vals, epochs = [], []
    for i in range(N_BLOCKS):
        te = (blk == i) & keep; va = (blk == (i - 1) % N_BLOCKS) & keep; trn = keep & ~te & ~va
        m = factory(); sc = Scaler(m.scaler_kind).fit(X[trn])
        m.fit_segments([sc.transform(s) for s in segments_of(X, idx, trn)], [sc.transform(s) for s in segments_of(X, idx, va)])
        oos[te] = score_segments(m, sc, tr[te]); fold_id[te] = i
        vals.append(float(np.nanmean(m.residual(sc.transform(X[va])) ** 2))); epochs.append(getattr(m, "epochs_", 0))
    return oos.dropna(), fold_id, float(np.mean(vals)), int(round(np.mean(epochs)))


def six_hour_sample(s):
    return s.resample(SUBSAMPLE).first().dropna()


def control_limit(oos):
    return float(np.percentile(six_hour_sample(oos), LIMIT_PCT))


def slope_series(spe):
    """Dốc log SPE (/ngày) trên cửa sổ 14 ngày LỊCH, tính trên chuỗi liên tục theo thời gian (cắt khi trống > 3 ngày)."""
    d = np.log(spe.resample("1D").median().dropna())
    out = pd.Series(np.nan, index=d.index)
    seg = np.cumsum(np.r_[True, np.diff(d.index.values) > np.timedelta64(SEQ_GAP_DAYS, "D")])
    for s in np.unique(seg):
        ds = d[seg == s]
        for t in ds.index:
            w = ds.loc[t - pd.Timedelta(days=SLOPE_DAYS - 1): t]
            if len(w) >= SLOPE_MIN_OBS:
                x = (w.index - w.index[0]).days.values.astype(float)
                out[t] = np.polyfit(x, w.values, 1)[0]
    return out


def evaluate(factory, fs, tag):
    tr = fs[fs.role == "train"]
    oos, fold_id, val_mse, mean_epochs = run_cv(factory, tr)
    limit = control_limit(oos)
    X = to_matrix(tr); m = factory(); sc = Scaler(m.scaler_kind).fit(X)
    if hasattr(m, "max_epochs"):
        m.max_epochs = max(mean_epochs, 1)                  # fit lại với số epoch trung bình các fold
    m.fit_segments([sc.transform(s) for s in segments_of(X, tr.index, np.ones(len(tr), bool))], None)
    dev = fs[fs.role != "blind"]                            # KHÔNG chấm blind ở đây
    spe = score_segments(m, sc, dev)
    out = pd.DataFrame({"spe": spe, "role": dev.role, "episode": dev.episode})
    out["oos_spe"] = oos.reindex(out.index); out["fold"] = fold_id.reindex(out.index).fillna(-1).astype(int)
    sl = slope_series(out.spe); out["slope14"] = sl.reindex(out.index.floor("1D")).values
    os.makedirs(SPE_DIR, exist_ok=True); os.makedirs(MODEL_DIR, exist_ok=True); os.makedirs(ROWS_DIR, exist_ok=True)
    out.to_parquet(f"{SPE_DIR}/{tag}.parquet"); pickle.dump({"model": m, "scaler": sc}, open(f"{MODEL_DIR}/{tag}.pkl", "wb"))
    fa_fold = []
    for i in range(N_BLOCKS):
        lim_i = control_limit(oos[fold_id.reindex(oos.index) != i])
        fa_fold.append(float((six_hour_sample(oos[fold_id.reindex(oos.index) == i]) > lim_i).mean()))
    refit_tr = out.loc[tr.index, "spe"]
    neg = out[out.role == "neg"].groupby("episode")["slope14"].max()
    row = {"model": tag, "n_params": m.n_params(), "epochs_refit": mean_epochs, "val_mse": round(val_mse, 4),
           "limit99_6h": round(limit, 4), "spe_oos_median": round(float(oos.median()), 4),
           "fa_oos_10min": round(float((oos > limit).mean()), 4), "fa_refit_6h": round(float((six_hour_sample(refit_tr) > limit).mean()), 4),
           "fa_fold_mean": round(float(np.mean(fa_fold)), 4), "fa_fold_max": round(float(np.max(fa_fold)), 4),
           "sep_ratio_16-30apr": round(float(out.loc[SEP_WINDOW[0]:SEP_WINDOW[1]].query("role=='config_pos'").spe.median() / oos.median()), 2),
           "max_slope_neg_ep7": round(float(neg.get("ep7", np.nan)), 4), "max_slope_neg_ep8": round(float(neg.get("ep8", np.nan)), 4),
           "max_slope_neg_9a": round(float(neg.get("9a", np.nan)), 4),
           "max_slope_cfg_pos": round(float(out[out.role == "config_pos"].slope14.max()), 4),
           "max_slope_precheck": round(float(out[out.role == "precheck_pos"].slope14.max()), 4)}
    json.dump(row, open(f"{ROWS_DIR}/{tag}.json", "w"), ensure_ascii=False)
    return row


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--models", default="pca"); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
    if os.path.exists(LOCK_FILE) and not a.force:
        sys.exit("TỪ CHỐI: đã có locked_params.json — chạy lại CV sẽ làm lệch hash khóa. Xóa khóa có chủ ý hoặc dùng --force.")
    fs = pd.read_parquet(FEATURE_STORE); fs = fs[fs.cadence_min == 10]
    for tag, factory in model_zoo(a.models.split(",")):
        print(json.dumps(evaluate(factory, fs, tag), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
