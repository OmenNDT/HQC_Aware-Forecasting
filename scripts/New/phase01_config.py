"""phase01_config.py — Hằng số chung cho pipeline phase 01 (một nơi duy nhất, theo góp ý code review)."""
import pandas as pd

ROOT = "/home/sontn/Projects/HQC_Aware-Forecasting"
DATA_NEW = f"{ROOT}/Dataclean_new"
FEATURE_STORE = f"{DATA_NEW}/feature_store_1x.parquet"
SPE_DIR, ROWS_DIR, MODEL_DIR = f"{DATA_NEW}/spe", f"{DATA_NEW}/cv_rows", f"{DATA_NEW}/models"
CV_RESULTS = f"{DATA_NEW}/cv_results.csv"
LOCK_FILE, BLIND_FILE = f"{DATA_NEW}/locked_params.json", f"{DATA_NEW}/blind_test_ep11.json"

# Giao thức kiểm định chéo (phase 01 mục 5)
N_BLOCKS, PURGE_H = 5, 12
LIMIT_PCT, SUBSAMPLE = 99, "6h"          # giới hạn 99% trên MẪU 6 giờ một điểm
SEGMENT_GAP = pd.Timedelta(hours=1)      # cắt đoạn liên tục khi khoảng cách hai dòng > 1 giờ (cửa sổ/lọc trượt không vắt qua)
SLOPE_DAYS, SLOPE_MIN_OBS, CONSEC = 14, 10, 3   # dốc log SPE trên 14 ngày lịch, ≥10 ngày quan sát, báo khi ≥3 ngày liên tiếp
SEQ_GAP_DAYS = 3                          # dốc tính trên chuỗi liên tục theo thời gian (9b→9c liền nhau), cắt khi trống > 3 ngày

# Mốc thời gian (phase 01 mục 2)
CFG_WINDOW = (pd.Timestamp("2026-03-23"), pd.Timestamp("2026-04-30 23:59"))
PRECHECK_WINDOW = (pd.Timestamp("2026-05-01"), pd.Timestamp("2026-05-29 23:59"))
SEP_WINDOW = (pd.Timestamp("2026-04-16"), pd.Timestamp("2026-04-30 23:59"))
STOP2 = pd.Timestamp("2026-05-29 10:40")  # máy dừng lần 2 (dòng đầu tiên mất tín hiệu trong 9c)
BLIND_PLATEAU = (pd.Timestamp("2026-06-14"), pd.Timestamp("2026-07-18 23:59"))
BLIND_CLIMB_FROM = pd.Timestamp("2026-07-19")

# Phase 02 — tầng A (Direct, peak-to-peak, cùng quy ước với ngưỡng nhà máy) và sự kiện đo lead-time
PLANT_LIMIT_UM = 65.0
TIERA_WINDOW_RUN_DAYS, TIERA_HORIZON_DAYS, TIERA_STARTUP_SKIP, TIERA_CONSEC, TIERA_Z90 = 14, 30, 2, 2, 1.645
TIERA_REF_DAYS, TIERA_REF_MIN_OBS, TIERA_RISE_MIN = 90, 30, 0.10   # "leo so với chính nó": mức > 1,10 × trung vị 90 ngày của kênh (quyết định 04/09 12:30)
DIRECT_LONG = f"{ROOT}/Dataclean_old/P29201A_clean_long.parquet"
STOP1 = pd.Timestamp("2026-01-04")            # dừng tháo kiểm tra lần 1 (đo lead-time; kỳ vọng: không báo)
EVENTS = {"dung1": STOP1, "dung2": STOP2}      # dừng 2b (11–13/06) gộp vào dừng 2

# Tiêu chí chọn (phase 01 mục 6) — mặc định theo code review: FA leave-one-fold-out
FA_FOLD_MEAN_MAX, FA_FOLD_MAX_MAX, SEP_MIN = 0.03, 0.10, 1.3
TAU_GRID = [round(0.02 + 0.005 * i, 3) for i in range(37)]   # 0.020 … 0.200
