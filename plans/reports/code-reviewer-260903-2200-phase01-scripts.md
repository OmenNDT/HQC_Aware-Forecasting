# Code Review — Phase 01 model-comparison pipeline (scripts/New/12–16 + models/)

**Date:** 2026-09-03 · **Scope:** read-only review vs `plans/260903-1538-early-warning-three-tier/phase-01-train-six-models-blocked-cv.md` §3–6 · **LOC:** 988 (10 files, all ≤ 200 lines)

## Scope / evidence gathered

- Verified 9b index: 4 321 contiguous rows (no gap > 1 h), 5 equal-time blocks 864/864/864/864/865, purge ±12 h removes 580 rows (13.4 %) → OOS covers 86.6 % of 9b. Fold roles (test Kᵢ, val Kᵢ₋₁ mod 5, train rest) match §5.
- `Dataclean_new/`: 27 rows in `cv_results.csv`, 27 spe parquets, `locked_params.json` (τ = 0.135, chosen `SAE_b0.001_s0`), `blind_test_ep11.json`.
- File mtimes: lock 22:39:05, blind 22:39:07, **PCA parquets + cv_results.csv rewritten 22:41:03–06** → the lock hash is already stale relative to the files on disk.

## Overall assessment

Core CV mechanics are correct: scaler fit on train only, per-block `fit_segments`, per-episode scoring, NaN warm-up rows, hash-guarded blind script. The serious problems are protocol-level: the refit model is trained without the CV-derived epoch count, the blind set is scored and summarised by script 13 before the lock, criterion 1 is disabled with `or True`, τ-tuning reads the precheck half of 9c, and the lock/blind artifacts on disk no longer correspond to the inputs that produced them. Statistical design issues (τ rule, censored lead-time, 6-h median vs 6-h sample) need a decision before any conclusion is drawn from the ranking.

---

## Critical

### C1. Blind set (ep11) is read, scored and summarised by script 13 before the lock — violates §9 "Đoạn 11 chưa từng được đọc bởi script 13, 14"
`13_blocked_cv_train_compare.py:219-220` scores every role incl. `blind`; `:246-247` writes `median_spe_blind_plateau` / `median_spe_blind_climb` into `cv_results.csv` and prints them to the console during model development. Script 14 (`:34`, `:88`) then hashes those parquets, and script 15 merely re-reads pre-computed blind SPE. Anyone iterating on architectures sees blind-set numbers while choosing.
**Fix:** in script 13 drop rows with `role == "blind"` from `fs` before scoring (`fs = fs[fs.role != "blind"]` at `:253`) and delete the two blind columns. Persist the refit model + scaler per tag (`torch.save` / `np.savez` → `Dataclean_new/models/<tag>.*`); script 15 loads the locked model, reads the feature store's `blind` rows and scores them itself. No model artifact is saved anywhere today — phase 02 cannot use the "chosen" model without retraining.

### C2. Lock is stale; blind test ran on inputs that were then overwritten
PCA models were re-run at 22:41 (after lock 22:39 and blind 22:39). `locked_params.json` / `blind_test_ep11.json` describe a superseded `cv_results.csv` and superseded PCA parquets; script 15 would now (correctly) refuse. Re-locking means re-running script 15 — a second blind run, which §7 forbids. Root cause: script 13 has no guard against overwriting inputs that are already locked, and script 15 does not enforce "run once".
**Fix:** script 13 `:225` and `:260` — if `locked_params.json` exists and `inputs_sha256` matches current files, refuse to overwrite (require `--unlock` flag which also deletes the lock). Script 15 — refuse if `blind_test_ep11.json` exists; on success write `blind_run_at` back into the lock. Document in the phase report that the current blind JSON pre-dates the PCA re-run and which of the two states is authoritative.

### C3. Refit model ignores the CV epoch count → trains 300 (DBN 600) epochs with no early stopping
`13:218` `m.fit(sc.transform(X))` with `Xval=None`; `ae_sae_vae_models.py:58-59` skips validation → loop runs to `max_epochs`. `cv_results.csv` shows `epochs = 300` for every NN and 600 for DBN — that is the refit's count, not the fold mean §5 requires ("epoch = trung bình fold"). The SPE used for sep-ratio, negative slopes, lead-time and blind come from a model trained differently (longer, possibly overfit) from the folds that set the 99 % limit.
**Fix:** in `run_cv` collect `getattr(m, "epochs_", 0)` per fold and return the mean; in `evaluate` set `m.max_epochs = max(1, round(mean_epochs))` (and for DBN divide per RBM, or store per-RBM epochs) before `m.fit`. Report both `epochs_cv_mean` and `epochs_refit`.

---

## High

### H1. `base_ok` is vacuous (`or True`) — criterion 1 disabled, EDCNN passes with `fa_fold_max = 1.0`
`14:60` `(res.loc[t,"fa_fold_mean"] <= FA_MAX*3 or True)`. Criterion 1 as written (pooled OOS FA ≤ 1.5 %) is satisfied by construction (limit = p99 of the same sample), so the pooled FA is indeed uninformative — but the script already computes the informative statistic: `fa_fold_mean/max` = limit from 4 folds applied to the 5th (`13:230-234`). EDCNN has `fa_fold_max = 1.0` in all 3 seeds (fold 1 OOS median 9.47 vs ≈2 elsewhere), AE_s1 0.64, DBN 0.30 — these models' limits do not generalise across blocks, yet all rank as `pass`.
**Fix:** replace criterion 1 with the leave-one-fold-out FA: `fa_fold_mean ≤ 0.03 and fa_fold_max ≤ 0.10` (≈21 six-hour bins per fold → 0.10 = 2 bins; state the thresholds in the plan before re-running). Also report FA at 10-min cadence as §5 requires (`13:237-239` only reports 6 h). Remove the `or True`.

### H2. τ-tuning objective reads the precheck half of 9c (decision 2 leak)
`14:45-49` `alarm_days(full9c, τ)` → `lead_days`; `14:63-66` uses `lead_days.notna()` and `median_lead` in the grid objective. Decision 2 (03/09 20:55) restricts tuning to 23/03–30/04; 01–29/05 must be untouched. Today it only "happens" not to matter because first alarms fall in April.
**Fix:** tune on `cfg` only (`alarm_days(cfg, τ)`), report `first_alarm_9c` on `full9c` after τ is fixed. Delete unused `CFG`, `PRE` (`14:21`) or use them.

### H3. τ selection rule: "maximise n_pass, then median lead" lets the worst model set τ for everyone and double-dips on 9c
Because lower τ ⇒ longer lead, the tie-break always pushes τ down until the *noisiest* model produces a negative alarm; τ = 0.135 is therefore set by that model (PCA_k3 `max_slope_neg_9a = 0.163`), not by the candidate set. Effects: (a) good models lose lead-time; (b) `n_pass` and `median_lead` are both computed on the set the models are ranked on → optimistic ranking; (c) 0.135 /day (×6.6 per 14 days) is so high that in the blind test **no model alarms on the 19/07 climb** (all `climb_first_alarm = null`, `max_slope_climb ≈ 0.045`). "One common threshold" is defensible only if the slope is first put on a common scale.
**Fix (choose one, write it in the plan first):** (i) restrict the τ search to models that already pass H1 + sep ≥ 1.3, choose τ = max negative-set 3-day slope over those models × safety margin (e.g. 1.2), no lead-time in the objective; or (ii) standardise the slope per model by its negative-set SD (z-slope) and use one common z-threshold; or (iii) keep per-model τ but publish the rule. Also report the τ–n_pass plateau (`tab`) in the report so the sensitivity is visible.

### H4. Lead-time is censored by the slope warm-up, so the ranking's top-3 is an artifact
SAE first alarm 03/04 = first day `slope14` exists (01/04) + 3 consecutive days — i.e. the earliest alarm the rule can produce. Lead 56 vs 55 vs 45 days is therefore not "SAE detects earlier" but "SAE's slope is above τ from day 1". `14:76` ranks by `lead_days` descending → SAE wins on a saturated metric.
**Fix:** treat leads within the first 3 possible alarm days as censored (report `≥ 56`), rank censored models as ties and fall through to criterion 5 (fewer parameters → AEsmall / PCA_k3 would then beat SAE). Alternatively require `slope14` warm-up be filled from 9b's last 14 days for 9c only (contiguous in time, 1-day gap) so the slope on 23/03 is defined.

### H5. `control_limit` uses the 6-h **median**, not a 6-h **sample**; 10-min FA never reported
`13:195-198`. §5: "giới hạn 99 % trên SPE ngoài mẫu lấy mẫu 6 h (≈120 điểm); báo cáo FA ở cả 6 h và 10 phút". p99 of 36-point medians is much lower than p99 of individual points → the limit is tight at 10-min cadence (10-min FA will be ≫ 1 %) and with ≈104 bins p99 is effectively the 2nd-largest value (high variance; see fa_fold_max scatter). The 6-h median is also what script 15 (`:141`) and `fa_refit_6h` compare against, so it is at least self-consistent — but not what the plan specifies.
**Fix:** decide and document: either (a) `oos.resample("6h").first()` (true subsample) or (b) keep median but rename the column `limit99_6hmedian` and add `fa_10min = (oos > limit).mean()` plus `limit99_10min = percentile(oos, 99)`. State the alarm rule (≥ 6 h continuous) uses which statistic.

### H6. Windows / DBN smoothing straddle machine-stop gaps inside an episode
`13:189-192` splits by `episode` only. ep8 has 37 internal gaps > 1 h (run-gate drops), 9c "report" (02–10/06) follows a 3.5-day stop and a further 1.7-day gap. `windows()` (`ed_lstm_cnn_models.py:262-268`) and DBN's 50-row cumsum (`dbn_rbm_model.py:241-242`) operate on row position, so a 20-step window may span days of downtime. Affects `neg` rows in ep8 (criterion 3) for LSTM/CNN/DBN.
**Fix:** in `score_by_episode` split each episode further where `index.diff() > 1 h` (`np.split` on gap positions); the `fit_segments` path already does this correctly for 9b because 9b happens to be gap-free.

### H7. `cv_results.csv` read-modify-write race between parallel runs
`13:257-260`: read → drop overlapping tags → concat → `to_csv`. Two processes (`--models ae`, `--models deep`) both do this at exit with no lock; if their end times overlap within the read/write window, one set of rows is silently lost. It did not bite (ae finished 22:04, deep 22:38) but nothing prevents it; the result is also only written at the very end (a crash after 3 h loses all rows).
**Fix:** write one row per model as it completes to `Dataclean_new/cv_rows/<tag>.json` and have script 14 (or a tiny merge step) build the CSV; or wrap the merge in `fcntl.flock` and write via temp file + `os.replace`. Either removes the race and gives crash-safety.

---

## Medium

### M1. ED-CNN decoder ends at 24×10 and is nearest-upsampled ×2 in time
`ed_lstm_cnn_models.py:334-335`: 24×20 → 12×10 → 6×5 → up(2,1) 12×5 → up(2,2) 24×10 → Conv 8×8 → tanh → `interpolate` to 24×20. Feature/time alignment is correct (H = 24 features, W = 20 steps; transpose round-trips match the `(win, feat)` flattening at `:290-296`), but the final conv works at half time-resolution, so steps 2j and 2j+1 get identical reconstructions; the "point at t" is a 20-min blur of (t−1, t). Paper Table 7 (14×20 input) cannot round-trip either, so intent is ambiguous — but upsampling after the last conv/tanh is not what any encoder–decoder does.
**Fix:** `nn.Upsample(scale_factor=(2, 4))` for the second upsample (12×5 → 24×20), drop `interpolate`; or add `nn.Upsample((1, 2))` before the last conv. Note the 8×8 "same" kernel is non-causal within the window (fine — the window itself is causal wrt t; say so in the docstring).

### M2. VAE `reconstruct` reseeds the global RNG and its score depends on batch composition
`ae_sae_vae_models.py:138` `torch.manual_seed(self.seed+1000)` inside a method mutates global state (harmless today only because every `fit` reseeds). `randn_like(mu)` on an (n, 8) tensor gives row i different noise depending on n and its position → the same row scores differently in `run_cv` (per block) vs `score_by_episode` (whole episode). 16 draws only reduce, not remove, this.
**Fix:** use a local `torch.Generator(device=DEV).manual_seed(...)` passed to `torch.randn(..., generator=g)`; or score with the posterior mean (`sample=False`) and keep the 16-draw mean as a reported variant. Also validate with `sample=False` at `:130` (stochastic val loss makes patience-20 early stopping noisy). KL uses `mean` over 8 latent dims while MSE uses `mean` over 24 → β_kl=1 is not the ELBO weighting; document or use sums.

### M3. DBN — CD-k correct; Gaussian visible ignores feature variance; warm-up rows not NaN
`dbn_rbm_model.py:172-181`: signs are right (positive phase v₀ᵀp(h|v₀), negative vₖᵀp(h|vₖ), biases likewise); using probabilities for the positive hidden phase and mean-field Gaussian visibles is standard. Issues: (a) Gaussian units assume σ = 1, but only the 8 amp columns are scaled to [−1, 1]; sin/cos have SD ≈ 0.05 and are effectively ignored by the first RBM (same for AE/LSTM/CNN inputs — see M4); (b) `score` (`:239-243`) leaves the first 49 rows as raw un-smoothed SPE instead of NaN, contradicting the base-class contract at `reconstruction_base.py:59`; (c) `epochs_` sums the three RBMs (600) — report per RBM; (d) `hs` (`:229-231`) is dead.
**Fix:** set `out[:self.smooth-1] = np.nan`; add per-feature σ to the Gaussian RBM or scale sin/cos to unit variance for the DBN only; drop `hs`.

### M4. Scaler leaves sin/cos unscaled for PCA too — §3.4 says "PCA z-score"
`reconstruction_base.py:17-37` scales only `AMP_IDX` regardless of `kind`. For z-scored amps (var 1) vs raw sin/cos (var ~10⁻³–10⁻²) PCA's k components are spent almost entirely on amplitude; phase changes (the very signal §3 cares about for the 2005/2007 bearings) barely enter SPE. The plan exempts sin/cos only for the min-max NN path.
**Fix:** for `kind == "z"` z-score all 24 columns (guard tiny SD); keep the exemption for `minmax`. Re-run PCA rows.

### M5. `slope14` window is 14 *rows* of daily medians, not 14 calendar days; day-level slope assigned to 00:00 rows is non-causal within the day
`13:203-209` `dropna()` then positional slicing; across gaps a "14-day" window can span weeks (ep8; 9c report). `len(w) >= 10` counts rows. The reindex at `:224` (`s.reindex(g.index.floor("1D"))`) is correct but gives every 10-min row of day D a slope computed from D's full-day median — fine for daily alarm evaluation (scripts 14/15/16 all take `.resample("1D").first()`), but state it.
**Fix:** `d = np.log(spe.resample("1D").median())` without dropna, then `d.rolling("14D", min_periods=10).apply(slope_fn)` (or compute on a full daily reindex and mask gaps). Guard `log(0)` (`np.log(np.clip(m, 1e-12, None))`).

### M6. `STOP2` differs between scripts and is dead in one
`13:133` `2026-05-29 10:40` (unused); `14:21` `2026-05-29 00:00` (used for `lead_days`). Also `13:128` imports unused `FEATURES`; `13:216` unpacks unused `six`; `reconstruction_base.py:87-89` `spe_series` unused; `14:21` `CFG`, `PRE` unused; `16:168` `np` unused.
**Fix:** single `constants.py` under `scripts/New/` for STOP2, windows, τ grid, role names; remove dead names.

### M7. Script 16 takes τ from CLI (default 0.06) instead of the lock; family colouring uses `startswith`
`16:258` default τ = 0.06 while the lock says 0.135 — figure and lock can disagree silently. `16:245` `chosen_model.startswith(f)`: chosen `AEsmall_s0` would colour both `AE` and `AEsmall`.
**Fix:** read `tau_common` from `locked_params.json` when present; compare `family == re.sub(r"_s\d+$", "", chosen)`.

### M8. Script 12 `ffill(limit=6)` runs after the run-gate filter, so it bridges stoppages by row count, not time
`12:47-49`: rows failing the gate are removed first, then ffill spans across the removed span. Also the gate itself treats NaN as "not running", so a row with ≥3 NaN channels is dropped rather than filled. `load_hourly_report_segment` (`:78`) relies on positional columns `r[1:17]` in the xlsx.
**Fix:** ffill on the raw frame first (with `limit=6` and a time check), then gate; map xlsx columns by header names.

---

## Low

- **L1.** Absolute `ROOT` hard-coded in 5 files (`12:23`, `13:126`, `14:17`, `15:115`, `16:172`) → `ROOT = Path(__file__).resolve().parents[2]`.
- **L2.** `model_zoo` lambda-with-default-arg factories (`13:153-170`) — works, but `functools.partial(PCAModel, k)` is clearer and pickle-able (needed if you ever parallelise with multiprocessing).
- **L3.** Heavy use of `;` to pack several statements per line (`13:176-185`, `14:55-57`, `15:141-146`) keeps files under 200 lines at the cost of readability; the ≤ 200 rule is meant to be met by splitting modules (e.g. `cv_metrics.py` for `control_limit/slope14/fa_fold`), not by line-joining.
- **L4.** `14:93`, `15:151`, `16:239` — `json.dump(..., open(path, "w"))` leaks file handles; use `with`.
- **L5.** `torch.set_num_threads(8)` at import (`ae_sae_vae_models.py:14`) — two parallel processes on an 88-thread box is fine, but make it an env-driven parameter.
- **L6.** `13:227` `spe_all[tr.index]` label-indexing a Series with a DatetimeIndex — use `.loc`.
- **L7.** `Bao_cao/` and `Dataclean_new/spe` created implicitly / by `os.makedirs` in only one place; script 16 will fail if `Bao_cao/` is absent.

---

## What is correct (keep)

- Fold construction (`13:136-143`, `:179`) matches §5 exactly, including K₀ = K₅ rotation and the 24-h total gap.
- Scaler fit on `X[trn]` only; `fit_segments` builds windows per block (`ed_lstm_cnn_models.py:282-286`) — no window straddles a block join in 9b (verified 9b is gap-free).
- `ReconstructionModel.score` returns NaN, not 0, for warm-up rows; windowed `reconstruct` scores only the last step of the causal window.
- Script 15 hash refusal works as designed (and is what exposed C2).
- RBM CD-k update and DBN greedy stacking are implemented correctly.
- Best-state restore on early stopping; leave-one-fold-out FA already computed — just not used.

## Recommended actions (in order)

1. C1 + C2: remove blind rows from script 13, persist refit models, add lock/run-once guards; decide which artifact state is authoritative and note the PCA re-run in the phase report.
2. C3: refit with CV-mean epochs; re-run all 27 configurations (results will change).
3. H1 + H2 + H3 + H4: rewrite `base_ok`, tune τ on config half only, adopt one of the τ rules, add lead-time censoring — write the chosen rules into phase-01 §6 **before** re-running.
4. H5 + H6 + M4 + M5: fix limit statistic / 10-min FA, gap-aware segmentation, PCA scaling, calendar-day slope.
5. H7 + M6 + L1–L3: per-model result rows, shared constants module, relative ROOT, split `13` into `cv_core.py` + `cv_metrics.py`.

## Metrics

- Type coverage: n/a (no annotations). Tests: none present for `models/` (plan §10 asks for synthetic-data check of the RBM). Lint: pyflakes not available in venv; manual pass found 8 unused names (M6).

## Unresolved questions

1. Which state is authoritative for phase-01 reporting: the 22:39 lock/blind (pre PCA re-run) or the current 22:41 files? A second blind run would break §7.
2. Blind result: every passing model has `state_frac_above_limit_6h = 1.0` and no rate alarm on the 19/07 climb — the 9b baseline does not transfer past stop 2 (risk "ổ 2005/2007 xoay tham chiếu" in §10). Does phase 01 accept this as the finding, or re-baseline on the 14/06–18/07 plateau for the blind test?
3. Should criterion 2 (sep ratio) have an upper sanity bound? SAE at 1 296× indicates a baseline SPE so small (0.034) that any drift saturates; the ratio currently rewards the most over-specialised model.
4. Confirm the intended 6-h statistic (sample vs median) for the 99 % limit and the ≥ 6 h alarm rule.

**Status:** DONE_WITH_CONCERNS
**Summary:** CV mechanics (blocks, purge, per-fold scaler, segment-wise windows, NaN warm-up, hash guard) are implemented as the protocol specifies, but the refit ignores CV epochs, the blind set is scored before the lock, criterion 1 is disabled, τ-tuning leaks the precheck half and is set by the noisiest model, and the on-disk lock is already stale. No conclusion should be drawn from the current ranking until C1–C3 and H1–H4 are addressed and the 27 configurations are re-run.
