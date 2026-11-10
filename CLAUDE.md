# Instructions for AI agents

Read README.md first for objectives and methodology. This file is the rulebook.

## Commands
- Install: `pip install -r requirements.txt`
- Run a step: `python -m risk.cli <pull|regress|montecarlo|stress|backtest|all> --seed 42`
- Test: `pytest -q`. Run the tests for the module you changed before finishing.

## Module contracts (do not change signatures without updating README + tests)
| Module | Function | Input | Output |
|--------|----------|-------|--------|
| data.py | `pull_prices(tickers, start) -> DataFrame` | ticker list | prices in AUD, Date index |
| factors.py | `build_factors(returns, themes, market) -> DataFrame` | log returns | factor returns |
| regress.py | `fit_exposures(returns, factors, ridge) -> (B, idio)` | returns, factors | betas, idio vol |
| montecarlo.py | `run_mc(factors, B, idio, values, cfg) -> (pnl, contrib)` | above | P&L per sim, factor P&L per sim |
| metrics.py | `var_es(pnl, conf)`, `attribute_es(pnl, contrib, conf)` | sims | numbers / Series |
| backtest.py | `rolling_backtest(...)`, `kupiec(...)`, `christoffersen(...)` | history | breaches, p-values |

## Rules
1. **No look-ahead.** In backtests, only use data available at each forecast date.
2. **Reproducible.** All randomness goes through `np.random.default_rng(seed)`.
3. **Config, not constants.** Tickers, horizons, confidence levels live in `config/`.
4. **Files in, files out.** Modules communicate via `data/` and `outputs/`, not shared state.
5. **Stay in your lane.** Only edit the modules your task names. If another module
   needs changing, say so in your summary rather than editing it.
6. **Never commit** `data/`, `outputs/`, API keys or credentials.
7. Losses are reported as **positive numbers** (VaR = 250,000 means a loss of 250k).

## Definition of done
- Tests pass, new code has a test, the README status table is updated, and the
  final message says what changed and any numbers that looked suspicious.
