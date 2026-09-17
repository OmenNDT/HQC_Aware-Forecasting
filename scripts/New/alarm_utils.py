"""alarm_utils.py — Hàm dùng chung cho luật báo động và cửa sổ thời gian (gom từ script 14, 15, 18, 20, 21 theo code review)."""
import os, importlib.util
import numpy as np
import pandas as pd


def alarm_days(s, tau, n):
    """Ngày báo: giá trị > tau trong ≥ n điểm liên tiếp của chuỗi theo NGÀY (s phải là chuỗi ngày, không khuyết trong đoạn)."""
    s = s.dropna()
    if len(s) == 0:
        return s.index[:0]
    # đếm "liên tiếp" theo ngày LỊCH: chuỗi vượt ngưỡng bị reset khi hai điểm cách nhau > 1 ngày
    hit = (s > tau).values; idx = s.index; run, out = 0, []
    for i in range(len(s)):
        if not hit[i]:
            run = 0
        else:
            contiguous = i > 0 and (idx[i] - idx[i - 1]).days <= 1
            run = run + 1 if contiguous else 1
        if run >= n:
            out.append(idx[i])
    return pd.DatetimeIndex(out)


def first_before(days, stop, lookback=120):
    """(ngày báo đầu tiên trong `lookback` ngày trước `stop`, lead-time theo ngày) hoặc (None, None)."""
    d = [x for x in days if stop - pd.Timedelta(days=lookback) <= x <= stop]
    return (d[0], (stop.normalize() - d[0].normalize()).days) if d else (None, None)


def load_script(name, filename, here):
    """Nạp một script đánh số (không phải module) để dùng lại hàm của nó."""
    sp = importlib.util.spec_from_file_location(name, os.path.join(here, filename))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
