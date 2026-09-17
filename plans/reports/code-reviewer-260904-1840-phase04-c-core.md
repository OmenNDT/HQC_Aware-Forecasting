# Code Review — Phase 04 embedded port (C core + scripts 25–27)

Date 2026-09-04 · Reviewer: code-reviewer · Plan: `plans/260903-1538-early-warning-three-tier/phase-04-quantize-sae-int8-embed-esp32s3.md`

## Scope
- C (541 LOC): `firmware/core/{sae_int8,stats_util,tier_b_slopes,tier_a_direct,tier_c_phase,hqc_engine}.c/.h`, `firmware/host_sim/replay_main.c`, `Makefile`
- Python: `scripts/New/25_export_sae_weights_and_reference.py`, `26_quantize_sae_int8.py`, `27_replay_feature_store_to_uart.py`
- References checked line-by-line: `13::slope_series/contiguous_segments`, `18::slope_slow/circ_mean_sd/weekly_signature`, `17::daily_direct/project`, `alarm_utils.alarm_days`, `models/reconstruction_base.Scaler(minmax)`
- Mode: read + execution (nothing edited; scripts 13/14/15/18/20 not run)

## What was executed (confirmations)
| Check | Result |
|---|---|
| `gcc -std=c99 -Wall -Wextra -Wshadow -Wconversion -fsanitize=undefined,address` build + full replay | 0 warnings, 0 sanitizer reports, output byte-identical to `Dataclean_new/embed/host_sim_out.jsonl` |
| C `sae_forward_spe_q30` vs script-26 `forward_int` on identical `Xq` (42,064 rows) | **bit-exact: 0 mismatches in Q30** |
| Script-26 sizing from `sae_int8.npz` | max log2\|acc·mult\| = 61.0 (< 63); \|bq\|max = 0.36·2³¹; mult ≥ 4.4e7 (rounding err ≤ 1.1e-8); SH ≤ 46 |
| Q10 input: chip path (`%.6g` text → float32 → `roundf`) vs Python (`float64` parquet → `np.round`) | 4,308 / 1,009,536 entries differ by 1 LSB (4,125 rows = 9.8 %); 0 exact-.5 ties → half-even vs `roundf` is a non-issue |
| Tier-A row sets chip vs `tier_a_daily.parquet` | chip-only days **2025-10-05, 2025-10-06** (= `TIERA_STARTUP_SKIP` rows) — see H1 |
| 4-year synthetic replay (stream ×4, +366 d shifts, 36 restarts) | sanitizer-clean; `post_restart` weeks 23 emitted vs 45 expected — see H2 |
| Malformed stdin lines (short, empty ts, `inf`, `1e40`, `-nan`, `x`, 3 kB line) | no crash; garbage → 0.0, empty ts → epoch 0 — see M1 |
| `day_of`/`day_to_str` on −1, 0, 86399, 86400, −86400, −86401, 2100-01-01 | all correct |
| Feature store NaN rows (`sin_2001X`, any amp) | 0 → tier-C row-count difference (M3) cannot manifest on this replay |

## Overall assessment
The int8 path is correct and provably bit-exact vs its numpy simulation; overflow sizing is sound with ≥2 bits margin. Tiers B and C are faithful ports; tier A is faithful *given history*. The remaining findings are cold-start / device-lifetime semantics that the replay cannot expose, plus plan-compliance (hand-typed constants) and comparison-fairness gaps in script 27. No Critical findings.

## Critical
None.

## High
**H1 — Tier A cold start skips no rows; chip and Python disagree on segment start** — `firmware/core/tier_a_direct.c:38–41`. `brk` requires `last_kept_day != INT64_MIN`, so the first day after boot never triggers `skip_left = startup_skip`. Python (`17:43–47`) has Direct history since 2021, sees the true stop before 28/09/2025 and drops 28–29/09; the chip keeps them. **Confirmed**: chip emits rows on 05–06/10/2025 that Python lacks, and its 14-row windows through ~11/10 include two rows Python excluded (levels/t-stats differ; flags happen to be 0). Failure scenario: chip is powered up at a real restart → the two post-restart transient rows enter the regression → possible false tier-A flag inside the first 14 rows (same mechanism as the ep8 restart transient noted in phase 02). Fix: `ta_init` sets `skip_left = startup_skip` (treat boot as post-restart), or accept a seeded `last_stopped_day` from the host. Script 27 currently reports `rows_chip 233 vs rows_python 231` without flagging it.

**H2 — `TC_MAX_RESTARTS 16` silently drops restarts; `post_restart` wrong after 16** — `tier_c_phase.c:13`. **Confirmed** on 4-year stream: 23 vs 45 post-restart weeks. Only restarts within 21 days of a week start matter, so replace with a small ring (overwrite oldest) — 4 entries suffice.

**H3 — Q10 input clamp saturates at amp = a + 32·b; Python has no clamp** — `sae_int8.c:11`. Saturation amplitudes per channel: 2001X 53.7 µm, 2001Y 46.6, 2003X 205, 2003Y 147, 2005X 28.5, 2005Y 22.5, 2007X 28.0, 2007Y 64.5. Observed max in the store: 42.4 / 39.4 / 63.7 / 43.9 / 12.0 / 11.4 / 8.9 / 27.2 — 2001X/Y are within 1.3× of clamp and the plant limit is 65 µm. On a real degradation past ~54 µm the chip's SPE stops growing while Python's keeps growing → slope14/45 understated exactly when it matters. Script 26 asserts `max|x|·2^10 < 32767` only on historical data. Fix: raise `X_Q` headroom is not free (Q10 chosen for precision); instead emit a `saturated` flag in the B JSON and treat any clamp as alarm-worthy, or move input to int32 Q10 (acc sizing already int64; `acc_max` for L0 would need 2^17 factor → SH shrinks by 2 bits, still fine).

## Medium
**M1 — `replay_main.c` parsing maps garbage to real values** — `replay_main.c:15,22`. `strtof("x")` → 0.0 (a "0 µm" amplitude, not NaN); `strtoll("")` → 0 → day 1970-01-01, which closes the current day early and, when the real day resumes, appends the same calendar day twice to the tier-B ring (duplicate `x` in `linfit`). **Confirmed** no crash, values silently accepted. For the ESP32 `main.c` (same core): validate with `endptr`, reject `ts < last_ts` or `ts` outside a plausible range, and count rejected frames. Core-level guard: `tb_push`/`ta_push_hour`/`tc_push` should ignore `day < cur_day`.

**M2 — Thresholds and tier constants hand-typed, violating plan §5 item 4** — `hqc_engine.c:9–12` (τ14 0.135, τ45 0.035, 3, 5), `tier_a_direct.c:7–8` (65, 30, 1.645, 0.10, 14, 90, 30, 2, 2), `tier_c_phase.c:9` (1.0, 5.0, 56, 3, 2, 21, 100). Values match `locked_params_phase02.json` and `phase01_config.py` today, but nothing ties them to the lock hash. Generate a `hqc_params.h` from lock2 + phase01_config in script 26 (same pattern as `sae_weights.h`, include `inputs_sha256`).

**M3 — Tier-C week admission and `week_end` differ from Python under NaN** — `tier_c_phase.c:19,46` vs `18:44–46`. Python counts *all* rows in the 7-day bin (`len(g) >= 100`) and `week_end = g.index.max()`; C counts only rows with valid 2001X sin/cos and `wend = last valid ts`. With NaN 2001X rows a week could be kept by Python and dropped by C (or vice-versa), and `week_end` keys would mismatch so script 27's intersection-based compare would silently skip them. Not reachable on the current store (0 NaN rows). Also Python's unwrap propagates NaN forever after a `<10 valid` week until a >21 d gap (`18:52–54`), whereas C resets to `ph` — Python-side quirk, note for a future fix in 18.

**M4 — Script 27 fairness: Python references are not computed on exactly what the chip receives**
- B: reference SPE is the float64-parquet path; chip gets `%.6g` text → 9.8 % of rows differ by 1 Q10 LSB (confirmed). Emit `%.9g` (float32 round-trip) so the numpy int sim and the chip see identical `Xq`; then the compare can assert bit-exact daily medians instead of a 5 % tolerance.
- A: reference is `tier_a_daily.parquet` (full 2021→ history) while the chip stream starts 28/09/2025 — the H1 discrepancy is hidden because only flag/alarm sets are compared and rows before 2026 carry no flags. Compare should assert `rows_chip == rows_python` (or list the diff) and compare `level`/`t_stat` per common row.
- C: fine (same `fs10`, same restarts).
- Row-count mismatch B ok (307 = 307).

**M5 — No state persistence; tier-C bin origin = first sample after boot** — `tier_c_phase.c:42`. Python anchors weeks at 28/09/2025 00:00. After any reboot the chip re-anchors at the next sample's midnight → week boundaries shift, `prev8` lookback pairs different weeks, and all rings (45 d, 100 rows, 12 weeks) restart empty (≥30 days blind for B45, ≥8 rows for A). Acceptable for the replay milestone; must be stated in §3.9 and solved (NVS snapshot or host-fed origin) before any plant deployment.

## Low
- **L1** `hqc_engine.c:39` computes SPE twice (`sae_forward_spe_q30` result discarded, `sae_spe` recomputes in double). Return the Q30 int and divide once; keeps one code path.
- **L2** `emit_a` reads `flag_ch[]`/`days_left_low[]` that are stale on incomplete days (`close_day` returns before `project_last_row`); JSON still says `row:0`. Not manifest in replay (0 cases). Zero them in `close_day`.
- **L3** Day/week close only fires on the *next* sample (`tb_push`, `ta_push_hour`, `tc_push`). During a machine stop the last partial day/week stays open until restart; alarms for that day are delayed. On device add a wall-clock close (call `*_flush`-like close when `now/86400 > cur_day`).
- **L4** `tier_b_slopes.c:24` treats `median ≤ 0` as "no day"; Python takes `log(0) = -inf` and would poison the window. SPE min observed 1.6e-3, unreachable; C behaviour is the saner one — document the divergence.
- **L5** `26_quantize_sae_int8.py:36,43`: no guard for an all-zero weight row (`s_w = 0` → NaN) or `sh ≥ 63` (`1 << (sh-1)` overflow in both numpy and C). Add `assert s_w.min() > 0` and `assert sh.max() < 62`.
- **L6** `27:24–31` duplicates `17::daily_direct` grid code; drift risk if 17 changes. Import it via `load_script`.
- **L7** `stats_util.c:7` `median_f` caps at 256 silently; `TB_MAX_PER_DAY 200` drops samples beyond 200/day (144 today). Fine for 10-min cadence; a 5-min cadence (288/day) would bias the median. Document or raise.
- **L8** Right-shift of negative `int64_t` (`sae_int8.c:19,34`) is implementation-defined in C99; gcc/xtensa are arithmetic, matching numpy. Add a `static_assert((-1 >> 1) == -1)`-style build check for portability.
- **L9** `SAE_W` as `const void*` with per-layer casts is fine, but `SAE_WBITS` is only 8/16; a future int32 layer would silently read wrong widths — assert in script 26 that `wbits ⊂ {8,16}`.

## Semantic parity verified (no finding)
- B: day = local-as-UTC midnight (`day_of` ↔ `resample("1D")`); segment break `> 3` calendar days; windows 13/44 calendar days within segment; `x = day − first`; min obs 10/30; run counter on NaN-dropped series with `≤ 1 day` contiguity; no alarm on NaN-slope day; ring 45 exactly covers the 45-day window.
- A: hour gate `known ≥ 6 && running ≥ 6`; stopped-day capture incl. incomplete days; break on stop in `(prev_kept, d]`; skip counts *rows*; 14-*row* window same segment ≥ 8; ref 90 calendar days `[t−90, t−1]` ≥ 30 rows; se/t/dl_low/rising identical; alarm run over rows with results.
- C: origin = first-sample midnight; bin label = start; unwrap gap ≤ 21 d; 4-week rate span ≤ 28 d ×7; prev8 = latest rated week with `wstart ∈ [ws−59, ws−53]`; sign/|rate|>1 both sides/sd<5; alarm = flag & previous *row* flag; `post_restart` 0..21 d.
- SAE: scaler minmax on 8 amp cols only; layer order (out,in) matches `a @ W.T`; tanh on all 6 layers incl. output; LUT index/interp/saturation identical; SPE in Q30 int64 exact.
- RAM: `hqc_t` ≈ 7 KB static; within plan's 16 KB.

## Recommended actions (priority)
1. H1: `ta_init` → `skip_left = startup_skip`; script 27 assert row sets equal and compare `level`/`t_stat`.
2. H2: restart ring (4 entries) in tier C.
3. H3: saturation flag in B JSON + document; decide int32 input vs flag.
4. M2: generate `hqc_params.h` from lock2/phase01_config with hash.
5. M1: ts/value validation in core push functions before ESP32 `main.c`.
6. M4: `%.9g` in stream; bit-exact daily-median assert.
7. M5: state persistence/origin — record as open risk in §3.9.

## Metrics
- Build warnings (`-Wall -Wextra -Wshadow -Wconversion`): 0 · UBSan/ASan: 0
- C bit-exactness vs numpy int sim: 42,064/42,064
- Replay parity: B14/B45/A/C alarm days identical (as reported); tier-A row sets differ by 2 (H1)

## Unresolved questions
1. Should the chip treat boot as "post-restart" (skip 2 rows) or be seeded with `last_stopped_day` from the host? Affects H1 fix choice.
2. Is int32 Q10 input acceptable for H3, or is a saturation flag enough for the thesis scope?
3. Will thresholds ever be updated OTA? If yes, M2 needs a runtime param block, not a header.

**Status:** DONE_WITH_CONCERNS
**Summary:** SAE int8 path is bit-exact and overflow-safe; tiers B/C match Python; tier A diverges at cold start (2 extra rows, confirmed) and the restart cap breaks `post_restart` after 16 restarts (confirmed). Script 27's compare hides the tier-A row difference and compares against float64 inputs the chip never sees.
**Concerns:** H1 (cold-start skip), H2 (restart cap), H3 (input clamp at 54 µm on 2001X vs 65 µm limit); plan §5.4 (hand-typed constants) not yet met.
