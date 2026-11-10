# Thematic Portfolio Risk Engine

Measures the downside risk of an equity portfolio **by theme** — neoclouds,
hyperscalers, critical minerals, gold miners, etc. — using a factor model,
Monte Carlo simulation and backtesting.

The question it answers: *"How much could this portfolio lose over the next
N days, and which themes would that loss come from?"*

---

## 1. Objectives

| # | Objective | Output | Status |
|---|-----------|--------|--------|
| 1 | **Pull data** — daily prices for holdings, theme baskets, market index and macro factors (gold, AUDUSD) in AUD | `data/prices.parquet` | ☐ |
| 2 | **Build theme factors** — equal-weight basket returns, orthogonalised against the market | `outputs/factors.parquet` | ☐ |
| 3 | **Regress** — each holding on Market + theme factors (ridge) to get exposures and idiosyncratic vol | `outputs/exposures.csv` | ☐ |
| 4 | **Monte Carlo** — simulate factor + idiosyncratic returns over the horizon (Student-t and block bootstrap) | `outputs/sims.parquet` | ☐ |
| 5 | **Measure risk** — VaR and Expected Shortfall at 95% / 99%, and ES attribution by theme | `outputs/risk_report.csv` | ☐ |
| 6 | **Stress test** — shock a theme (e.g. neoclouds −40%) and propagate through correlations | `outputs/stress.csv` | ☐ |
| 7 | **Backtest** — roll the model through history, count VaR breaches, run Kupiec / Christoffersen tests | `outputs/backtest.csv` | ☐ |

**Success criteria**
- 99% VaR breach rate within the Kupiec 95% acceptance band over the backtest.
- ES attribution by theme sums to total ES (within 1%).
- Every result is reproducible from config + seed with a single command.

**Out of scope (for now):** options/derivatives, intraday risk, liquidity-adjusted VaR, live trading.

---

## 2. Methodology

```
prices ─► log returns ─► theme factors ─► regression ─► exposures (B), idio vol
                                                              │
                     factor covariance (EWMA) / history ──────┤
                                                              ▼
                                         Monte Carlo (t / bootstrap) ─► P&L distribution
                                                                              │
                                     VaR · ES · theme attribution · stress ◄──┘
                                                      │
                                                 backtest (rolling)
```

1. **Theme factors.** For each theme, take the equal-weighted daily return of
   its basket and remove the part explained by the market:
   `theme_pure = basket − β · market`. Without this, every theme factor is
   mostly "the market".
2. **Exposures.** Regress each holding's returns on `[Market, themes, extras]`
   with ridge regression (themes are correlated — neoclouds vs hyperscalers).
   Portfolio exposure to factor *k* = Σ market value × β<sub>k</sub>.
3. **Simulation.**
   - `t`: multivariate Student-t on an EWMA covariance (λ = 0.97, df = 5) — fat tails.
   - `bootstrap`: resample contiguous blocks of historical factor returns —
     keeps real crash co-movement.
   - Idiosyncratic shocks added independently per stock.
4. **Risk.** VaR = loss at the (1 − α) quantile; ES = mean loss beyond VaR.
   Theme attribution = average factor P&L in the tail scenarios (Euler allocation).
5. **Stress.** Condition the factor distribution on a theme shock:
   `E[f | f_k = s] = Σ_·k Σ_kk⁻¹ s`.
6. **Backtest.** Re-fit on a rolling window, forecast next-period VaR, compare
   with realised P&L. Kupiec tests breach *frequency*; Christoffersen tests
   whether breaches *cluster*.

**Known limitations**
- Short histories (e.g. CoreWeave listed Mar-2025) → noisy betas; can override
  with judgemental exposures in `config/themes.yaml`.
- Correlations rise in crises; the bootstrap captures this better than `t`.
- Gold price and the gold-miners factor overlap — use one, or strip gold out
  of the miners basket.

---

## 3. Repository structure

```
.
├── README.md               ← this file (for humans)
├── CLAUDE.md               ← rules and commands for AI agents
├── .claude/agents/         ← agent role definitions
├── config/
│   ├── portfolio.yaml      ← holdings + market values (AUD)
│   ├── themes.yaml         ← theme baskets, market index, extra factors
│   └── model.yaml          ← horizon, confidence, n_sims, λ, df, ridge, seed
├── src/risk/
│   ├── data.py             ← pull_prices(), to_base_currency()
│   ├── factors.py          ← build_factors()
│   ├── regress.py          ← fit_exposures()
│   ├── montecarlo.py       ← simulate_factors(), run_mc()
│   ├── metrics.py          ← var_es(), attribute_es()
│   ├── stress.py           ← conditional_stress()
│   ├── backtest.py         ← rolling_backtest(), kupiec(), christoffersen()
│   └── cli.py              ← command-line entry point (below)
├── tests/                  ← one test file per module
├── data/                   ← raw downloads (git-ignored)
└── outputs/                ← results, one folder per run (git-ignored)
```

Each module does **one job**, reads its inputs from files/config, and writes
its outputs to files. This lets each step be run, tested and replaced on its own.

---

## 4. Usage

```bash
pip install -r requirements.txt

python -m risk.cli pull        # 1. download prices → data/
python -m risk.cli regress     # 2–3. factors + exposures
python -m risk.cli montecarlo  # 4–5. simulate, VaR/ES, attribution
python -m risk.cli stress      # 6. stress scenarios
python -m risk.cli backtest    # 7. rolling VaR backtest
python -m risk.cli all         # everything, in order
```

Every command accepts `--config config/` and `--seed 42`, and writes to
`outputs/<YYYY-MM-DD_HHMM>/` along with a copy of the config used.

---

## 5. Configuration example

```yaml
# config/themes.yaml
market: ACWI
extra_factors: [GC=F, AUDUSD=X]
themes:
  Neoclouds:         [CRWV, NBIS, IREN]
  Hyperscalers:      [MSFT, AMZN, GOOGL, META, ORCL]
  Critical minerals: [LYC.AX, PLS.AX, MP, ALB]
  Gold miners:       [NST.AX, EVN.AX, NEM, AEM]
```

---

## 6. Roadmap

- [ ] Port `thematic_var.py` prototype into `src/risk/` modules
- [ ] Unit tests for each module
- [ ] Rolling backtest + Kupiec / Christoffersen
- [ ] FactSet / Capital IQ CSV loader as alternative to Yahoo
- [ ] HTML risk report
- [ ] Crisis-period covariance option
