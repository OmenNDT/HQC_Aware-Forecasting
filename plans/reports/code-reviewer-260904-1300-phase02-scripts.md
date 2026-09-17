# Code Review — Phase 02 scripts (tier A / B45 / C, restart check, backtest)

Date 2026-09-04 13:00 · Scope `scripts/New/{phase01_config,17,18,19,20,21}.py` (495 LOC) + helpers in 13/14/15 · Read-only; every claim below was re-computed from the artifacts in `Dataclean_new/` (no blind statistic was recomputed beyond what `backtest_three_tiers.json` already contains).

## Overall assessment

Protocol hygiene is largely right: script 18 drops `role == "blind"` before anything (18:80), the SPE parquet has no blind rows (phase-01 C1 fixed), precheck is printed but never enters the τ₄₅ objective (18:92-95), script 20 refuses without lock / on hash mismatch / when output exists, phase-01 lock is now consistent with its inputs (lock 00:06 > pkl/spe 22:59). The mathematics of the tier rules matches the plan. But four defects change reported numbers in §6c, and one changes the tier-A blind verdict. None of them touches the ep11 conclusion for B45 (climb max 0.029 is below every τ the grid could have chosen), so the blind test does not need to be re-run for that reason — but the lead-time table must be regenerated, and doing so requires the `--force`/re-lock path, which should itself be logged.

## Critical

### C1. Script 18 computes slope45 per episode → 9b→9c continuity lost; τ₄₅ = 0.04 and "34-day lead" are artifacts
`18:84-85` `for ep, g in d.groupby("episode"): s = slope_slow(g.spe)`. 9b and 9c are different episode labels but contiguous in time; `slope_slow` (and `SEQ_GAP_DAYS` comment in config:16, and script 13's `slope_series(out.spe)` over the whole series) are designed to keep them joined. Effect measured on the locked parquet:

| | per-episode (as shipped) | whole series (as designed) |
|---|---|---|
| cfg days with slope45 | 10, first 21/04 | 39, first 23/03 |
| smallest τ with 0 neg alarms | 0.040 | **0.035** |
| first cfg alarm at that τ | 25/04 (34 d) | **11/04 (48 d)** |
| first cfg alarm at 0.040 | 25/04 | 12/04 (47 d) |

Script 20 then mixes both conventions: the non-blind slope45 comes from this per-episode parquet, while blind slope45 is computed on `db` alone (20:50), so the plateau has no slope45 until 13/07 either way. Fix: `d["slope45"] = slope_slow(d.spe).reindex(d.index.floor("1D")).values` (one call, whole series, same as 13:122), re-run 18 → new lock, re-run 20 with the re-run logged (see C3). Blind verdict for B45 unchanged (0.029 < 0.035).

### C2. Tier-C alarm timestamped at week START → "C = 5 days before stop 2" is non-causal
`18:54` `fs.resample("7D")` keys each row by bin start; `20:29-31` treats that as the alarm day. The week "24/05" has last row 29/05 10:30 (verified), i.e. the flag is computable only at the stop. Same for "18/01" (known 24/01). True lead for C at stop 2 is ≤ 0; §6c and `backtest_three_tiers.json` overstate it. Fix: add `r["week_end"] = g.index.max()` in `weekly_signature`, index the table by `week_end` for alarm purposes (keep `week` for display), and in `first_before` use that column for tier C. Also fixes the negative count window (20:68-71).

### C3. Script 20 run-once guard has a silent `--force` backdoor and the hash misses the inputs that actually matter
`20:36` `"--force" not in sys.argv` defeats "refuse to run twice" with no record. `20:39-41` hashes tier_b45/tier_c parquets + pkl + lock1, but (a) `tier_a_daily.parquet` is not hashed although tier-A flags feed the blind table and the rule was changed on 04/09 12:30; (b) `FEATURE_STORE` (the blind rows themselves) is not hashed; (c) tier C is *recomputed from source* (`s18.weekly_signature(fs10)`, 20:60) with rule constants hard-coded in 18:70-75 — editing `1.0`, `5`, `shift(8)` or the 21/28-day gaps in 18 without re-running 18 leaves the hash valid and changes blind results. Fix: remove `--force`; require the operator to delete OUT by hand and append `{"rerun_at", "reason"}` to `locked_params_phase02.json`; hash `tier_a_daily.parquet`, `FEATURE_STORE`, and the source of 17/18; read rule-C constants from `lock2["rule_c"]` (pass as arguments to `weekly_signature`); assert the recomputed non-blind rows equal the locked `tier_c_weekly.parquet` before touching blind.

## High

### H1. Tier-A window straddles stops and admits half-stop days → the 17–18/06 blind false alarm is a data-hygiene bug, not a rule outcome
`17:30-31` run-day filter uses ≥6/8 *daily medians* > 3 µm; 29/05 has 3 raw rows (37.1 / 2.4 / 2.0), median 2.4 for 2003AX, yet the day passes as a run day. `17:44` window = 14 rows regardless of gaps: at 16–18/06 the window spans 20 calendar days across stop 2 and 2b and contains that 2.4 µm point → slope t-stat 3.2 on 2003AX (verified). Also 42 skipped days (17:33-37) vs ~8 expected: `gap > 1` fires on every missing-pull day (30/09, 08/11, 06/03, 02/05 …), because the skip is applied after `dropna(how="any")`. Fix: (1) apply the run mask on raw rows *before* the daily median (`c5[(≥6/8 ch > 3 µm) per timestamp]`); (2) require the window to lie inside one contiguous run segment (`gap ≤ SEQ_GAP_DAYS`), skip if < 8 rows — same convention as tier B; (3) apply the startup skip only after gaps flagged as machine stops (reuse `19.stopped_days()`). With (1)+(2) the 17–18/06 alarms disappear; record this as a post-hoc change in the plan since blind has been seen.

### H2. Tier-C flip rule compares against the *sign* of a near-zero reference and against rows, not calendar weeks
`18:73-74` `prev = r.shift(8)` is 8 *rows* (weeks with < 100 rows are dropped at 18:55, so across ep8→9a→9b gaps this is not 8 weeks), and only `r.abs() > 1` is gated; `prev` may be 0.02 °/wk (weeks 08/03, 15/03, 22/03 in the locked table: +0.022, −0.040, +0.372). The 24/05 alarm exists only because the references 22/03 (+0.37) and 29/03 (+1.02) happen to be positive; the 10/05 flag is off because 15/03 was −0.04. So the alarm date is set by noise. `flip.shift(1)` likewise means "previous row", not "previous week". Fix (structural, not a tuned parameter): `prev` by calendar lookup `r.reindex(r.index - pd.Timedelta(weeks=8))`, hold via calendar week too; define the reference as meaningful only when `|prev| > 1` and add an explicit "onset" branch (`|prev| ≤ 1 and |r| > 1`) — the plan's 3.3 wording "dấu đổi so với 8 tuần trước" needs this to be well-defined. `|rate| > 1 °/wk` is not in plan 3.3; add it there (it is in the lock JSON).

### H3. Tier-C 18/01 alarm: genuine signature change, but a post-reassembly transient the rule will always fire on
Week 18/01: rot +14.4 °/wk, sd 2.4°, reference (8 rows back = 16/11) −1.1 °/wk. The phase moved +33° after stop 1; within-week sd stays small because the mean drifts smoothly, so the `sd < 5°` gate cannot filter transients. The rule is therefore guaranteed to alarm after any disassembly whose 8-week reference lies before the stop. Not a false alarm by the rule's own definition, but §6c should state that the rule is not a pre-event warning there; recommend suppressing C for the first N weeks after a stop detected by script 19 (or requiring the reference to be in the same run segment), decided *before* the next blind week.

### H4. Restart check "after" window straddles the next stop
`19:54` `after = fs.loc[restart+10d : restart+14d]`; for restart 02/06 this is 12–16/06 and contains stop 2b (10/06 23:50 → 14/06). The "dừng 2: 2001 −25 %" figure in §6c is a mixture of pre-2b and post-2b rows. Fix: truncate `after` at the next gap > 12 h (`fs_all.index[gaps]` is already computed) and skip when < 200 rows. Also `19:57-58` runs the turbine-reference check on phases already corrected by +148° (`phase_ref_corrected` is in the feature store, 12 500 rows); undo the correction for TURB channels when the flag is set so the January rotation is re-detectable, as §6c itself notes.

### H5. ep8 knife edge: the τ₄₅ floor is set by the 07/11 restart transient, not by a "negative" drift
ep8 slope45 by day (locked parquet): 0.042 on 06/12 falling monotonically to 0.010 on 04/01; the top values are the first windows (45 days back to 09/11, i.e. the two days after restart 07/11). At τ = 0.040 three days exceed τ (longest run 3 < 5) — the rule survives only on the consecutive-days clause; at 0.035 the run is 8. Ep7 max is −0.057, so ep7 contributes nothing to the choice. Implication for §6c: the sentence "τ tuned on a fast event does not transfer to a 3× slower one" is only half the story — the floor comes from labelling the post-restart settling of ep8 as negative. Applying the same startup skip to tier B (drop the first `TIERA_STARTUP_SKIP` running days after a stop from the slope window) would be the consistent fix and would lower the floor; whether that is allowed post-blind is a protocol decision to record.

### H6. Plan 3.5 asks for a censoring flag in the lead-time table; script 20 does not emit it
`20:29-31` returns the first alarm within 120 days; if the alarm run began earlier it is silently truncated (phase 01 had `censored: True` for PCA_k8). Add `censored = (d[0] - lookback_start).days == 0 or previous day also alarmed`.

## Medium

- M1 `17:48` 90-day reference includes day t and the whole 14-row regression window. With ≥ 30 obs one day moves the median by ≤ 1 rank — immaterial; 14 high days out of 90 can move it by ~15 % of the spread — borderline. Use `w.loc[t-90d : t-1d]` (or exclude the regression window) and keep the reference inside the current run segment (a 90-day reference across stop 1 mixes two bearing states: 2001 amplitude −49 %).
- M2 `18:81` model `"SAE_b0.001_s0"` hard-coded while `locked_params.json.chosen_model == "PCA_k8"`. lock2 records the SAE choice but not that it overrides lock1 nor why. Add `"model_override_of": lock1["chosen_model"], "reason": "..."` to lock2, or write the decision into phase-01 lock via a logged amendment.
- M3 `18:56` week `episode/role` taken from the first row: week 22/03 is labelled `train` with 864/865 rows `config_pos`. Blind week 14/06 aligns only because `fs10.index.min()` happens to be 28/09 + 37×7 d. Use the majority role and pass an explicit `origin` to `resample`.
- M4 `18:69-71` `x = np.arange(4.)` ignores dropped weeks though the guard allows a 28-day span (one missing week). Use `(w.index[i-3:i+1] - w.index[i-3]).days / 7`.
- M5 `18:40-41`, `20:25-26`, `14:24`, `15:21`, `21:25` `alarm_days` rolls over *rows* of a `dropna`'d daily series — consecutive rows ≠ consecutive days after gaps. Reindex to a daily calendar before rolling (a shared helper, see Maint).
- M6 `20:52-55` `allb.role != "report"` removes 9c report rows (29/05–13/06) between precheck and blind; slope45 on blind starts from scratch (needs 30 obs → 13/07). In operation the series is continuous; document that plateau coverage is 13/07–18/07 only.
- M7 `phase01_config.py:31-32` phase-02 constants live in a file named phase01; `TIERA_*` and `EVENTS` belong in `phase02_config.py` (re-exported) to keep the phase-01 lock reproducible.

## Low / maintainability

- L1 Duplicates: `alarm_days` ×5 (14, 15, 18, 20, 21); tier-A rolling alarm ×3 (17:71-73, 20:57-58, 21:39); blind scoring + slope block ×2 (20:45-51 = 21:33-37); `_load` ×2 (20:19-20, 21:15-16). Create `scripts/New/alarm_rules_and_windows.py` (alarm_days(s, tau, n) on a calendar index, tier_a_alarm_days(df), score_blind(model, fs10), slope_slow, weekly_signature, circ_mean_sd) and import it; numbered scripts become thin CLIs. This also removes the fragile `importlib` load of `13_…py`, which pulls the torch model zoo just for `score_segments`/`slope_series` (move those two into `models/reconstruction_base.py` or the new module).
- L2 Unused: `glob` (18:15, 20:11), `np` (20:13), `day_flag` (17:83, 17:87). `len(win) < 8` (17:45) and `len(g) < 100` (18:55), `len(a) < 10` (18:46) are magic numbers → config.
- L3 `tier_b45_daily.parquet` holds 10-min rows (30 544), not daily; rename `tier_b_spe_slopes_10min.parquet`.
- L4 All six files are ≤ 115 lines, but 17:61-65 / 20:83 / 21:36-40 pack several statements per line; fine for research code, hard to diff. No action required.
- L5 `19:35` reads the 5-year Direct parquet a second time (17 already does) — cache `stopped_days()` result to `Dataclean_new/direct_run_days.parquet`.

## Positive observations

- Blind exclusion is upstream of every computation in 18; SPE parquet is blind-free; hash + run-once guard exist and lock1 is now consistent.
- Tier-A keeps `flag_spec` / `flag_sig` / `flag` side by side, so the two rule revisions are auditable in the parquet.
- τ₄₅ objective is monotone and reads only `role ∈ {neg, config_pos}`; precheck is reported, not used.
- Restart detection filters data-pull gaps with Direct (19:33-38) — the 05–20/02 and 22/03 gaps are correctly rejected.
- Circular statistics (18:44-48) are correct (mean-resultant sd), and the unwrap resets on long gaps.

## Recommended actions (order)

1. C1 — whole-series `slope_slow` in 18; re-lock. 2. C3 — remove `--force`, extend hash, assert recomputed tier C == locked, read rule-C constants from lock. 3. C2 — week_end timestamps; regenerate lead-time table and correct §6c ("C = 5 ngày" → ≤ 0). 4. H1 — row-level run mask + segment-bounded window in 17 (log as post-blind change). 5. H4 — truncate restart "after" window; undo +148° for the turbine check. 6. H2/H3/H5 — decide and record before the 06/09 week: calendar-based reference, onset branch, post-restart suppression for C and startup skip for B45. 7. L1 — shared helper module.

## Unresolved questions

1. Was `--force` used for the 12:19 run of script 20? The lock is 12:18:06 and OUT 12:19:35, consistent with a single run, but nothing records it.
2. Is ep8 (Nov–Dec 2025, run-up to the 04/01 inspection stop) truly a negative at the 45-day scale? SPE rose 4 %/day for weeks; if the January stop found anything, ep8 is a positive mislabelled as negative and the τ₄₅ floor is wrong in the other direction.
3. After C1/C2/H1 the lead-time table changes (B45 ≈ 47–48 d, C ≤ 0 d, A blind FA = 0). Does the team accept regenerating the blind table once, with the reason logged, or should the shipped numbers stand with an erratum?

**Status:** DONE_WITH_CONCERNS
**Summary:** Protocol boundaries (blind exclusion, lock/hash, run-once) are in place, but the per-episode slope45 grouping, week-start alarm timestamps, and a half-stop day in the tier-A window mean three of the headline numbers in §6c (τ₄₅ = 0.04 / 34 d, C = 5 d, A blind FA = 2 d) are artifacts. Fixes are small and local; the ep11 verdict for B45 does not change, but the lead-time table must be regenerated under a logged re-lock.
