"""Offline hyper-parameter search behind Step 7 of ``decision_trees.ipynb``.

This is the script that produced the *tuned* LightGBM / XGBoost / CatBoost
configurations which Step 7 of the notebook re-fits and reports.  It is kept in
the repository so that the tuning is reproducible: the notebook only shows the
winners, this file shows how they were found.

What it does, in order:

1. builds the design matrices (time based split, ordinal encoding fitted on the
   training fold only, plus raw string frames for CatBoost's native
   ``cat_features``);
2. measures the three libraries at their **default** settings;
3. runs a random search of **110 configurations** — 40 LightGBM, 40 XGBoost,
   18 CatBoost on ordinal codes and 12 CatBoost with native categoricals —
   every one of them with early stopping (100 rounds) on the validation fold;
4. checks DART for LightGBM and XGBoost around the winning configurations;
5. scores the overall winner on train / validation / test.

Run it from the project root::

    python -m src.tune                     # ~4 minutes on 8 threads
    python -m src.tune --out results.json  # also dump every measurement

Importing the module runs nothing; the search only starts from :func:`main`.

Relationship to the notebook
----------------------------
The search was executed **before** ``src/data.py`` was finalised, and the
feature preparation below is deliberately left as it was actually run, so that
re-running this file reproduces the published configurations:

* it keeps ``RefId`` and treats ``WheelTypeID`` / ``BYRNO`` / ``VNZIP1`` as
  numeric, giving **41** columns where :func:`src.data.build_datasets` produces
  **40** (the three id-like columns are categorical there and ``RefId`` is
  dropped);
* it cuts the folds at the ``n // 3`` and ``2 * n // 3`` unique dates, which
  lands a couple of days away from the ``round(0.33 * n)`` cut used by
  :func:`src.data.time_split`.

Both differences are disclosed in the notebook, which is why Step 7 re-validates
the winning configurations against the library defaults on its own matrices
instead of assuming they are still optimal.  Nothing here writes into the
repository: CatBoost runs with ``allow_writing_files=False`` (no
``catboost_info/``) and the JSON dump is opt-in via ``--out``.
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data import RANDOM_STATE, TARGET, DATE_COLUMN, gini

__all__ = ["prepare", "random_search", "main"]

warnings.filterwarnings("ignore")

#: Default location of the raw competition file, relative to the project root.
DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "training.csv"

#: Threads handed to every library.
N_THREADS = 8

#: Early stopping patience (in boosting rounds) used by the whole search.
EARLY_STOPPING_ROUNDS = 100

#: Size of the random search, per library.  40 + 40 + 18 + 12 = 110.
N_LGB, N_XGB, N_CAT, N_CAT_NATIVE = 40, 40, 18, 12

Fitted = Tuple[float, float, int, Any]  # (valid Gini, fit seconds, best iteration, model)


def log(*args: Any) -> None:
    """Print immediately, so a long search can be followed in a terminal."""
    print(*args, flush=True)


# --------------------------------------------------------------------------- #
# 1. Data preparation
# --------------------------------------------------------------------------- #
def prepare(path: Path = DEFAULT_DATA) -> Dict[str, Any]:
    """Build the matrices the search runs on.

    The split is chronological and performed on the *unique* purchase dates, so
    a single calendar day never ends up in two folds.  Categorical columns are
    ordinal encoded with a mapping fitted on the training fold only (unseen and
    missing levels become ``-1``); numeric columns are median imputed with the
    training medians and every column that had missing values also gets a
    ``<column>_nan`` indicator.  Raw string frames are kept alongside for
    CatBoost's native ``cat_features`` mode.

    Parameters
    ----------
    path:
        Location of ``training.csv``.

    Returns
    -------
    dict
        Design matrices, targets, raw frames and the column lists.
    """
    frame = pd.read_csv(path)
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], unit="s")

    dates = np.sort(frame[DATE_COLUMN].unique())
    n_dates = len(dates)
    train_end = dates[n_dates // 3 - 1]
    valid_end = dates[2 * n_dates // 3 - 1]

    train = frame[frame[DATE_COLUMN] <= train_end].reset_index(drop=True)
    valid = frame[(frame[DATE_COLUMN] > train_end)
                  & (frame[DATE_COLUMN] <= valid_end)].reset_index(drop=True)
    test = frame[frame[DATE_COLUMN] > valid_end].reset_index(drop=True)

    features = [c for c in frame.columns if c not in (TARGET, DATE_COLUMN)]
    cat_cols = [c for c in features if not pd.api.types.is_numeric_dtype(frame[c])]
    num_cols = [c for c in features if c not in cat_cols]

    def raw_frame(fold: pd.DataFrame) -> pd.DataFrame:
        """Strings for CatBoost: missing levels become an explicit category."""
        out = fold.loc[:, features].copy()
        for column in cat_cols:
            out[column] = (out[column].astype(object)
                           .where(out[column].notna(), "__NA__").astype(str))
        return out

    # Encoders are fitted on the training fold only - no information from the
    # validation or test months can reach the model through the encoding.
    mappings = {c: {v: i for i, v in enumerate(np.sort(pd.unique(train[c].dropna().to_numpy())))}
                for c in cat_cols}
    nan_cols = [c for c in num_cols if bool(train[c].isna().any())]
    medians = train.loc[:, num_cols].astype("float64").median()

    def encode(fold: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=fold.index)
        for column in cat_cols:
            out[column] = (pd.Series(fold[column].to_numpy(), index=fold.index)
                           .map(mappings[column]).astype("float64").fillna(-1.0))
        block = fold.loc[:, num_cols].astype("float64")
        flags = {f"{c}_nan": block[c].isna().to_numpy(dtype=np.float64) for c in nan_cols}
        block = block.fillna(medians)
        for column in num_cols:
            out[column] = block[column].to_numpy(dtype=np.float64)
        for name, values in flags.items():
            out[name] = values
        return out.astype("float64")

    data = dict(
        Xtr=encode(train), Xva=encode(valid), Xte=encode(test),
        ytr=train[TARGET].to_numpy(np.int64),
        yva=valid[TARGET].to_numpy(np.int64),
        yte=test[TARGET].to_numpy(np.int64),
        raw_tr=raw_frame(train), raw_va=raw_frame(valid), raw_te=raw_frame(test),
        cat_cols=cat_cols, num_cols=num_cols,
    )

    log(f"rows  train={len(data['Xtr'])} valid={len(data['Xva'])} test={len(data['Xte'])}")
    log(f"dates train<= {train_end}  valid<= {valid_end}")
    log(f"pos rate train={data['ytr'].mean():.4f} valid={data['yva'].mean():.4f} "
        f"test={data['yte'].mean():.4f}")
    log(f"features={data['Xtr'].shape[1]} (cat={len(cat_cols)} num={len(num_cols)} "
        f"nanflags={len(nan_cols)})")
    return data


# --------------------------------------------------------------------------- #
# 2. Fitters - each returns (valid Gini, fit seconds, best iteration, model)
# --------------------------------------------------------------------------- #
def fit_lgb(data: Dict[str, Any], params: Dict[str, Any],
            early_stopping: Optional[int] = EARLY_STOPPING_ROUNDS,
            n_estimators: int = 3000) -> Fitted:
    """Fit LightGBM, optionally with early stopping on the validation fold."""
    import lightgbm as lgb

    merged = dict(params)
    merged.setdefault("objective", "binary")
    merged.setdefault("n_estimators", n_estimators)
    merged.setdefault("random_state", RANDOM_STATE)
    merged.setdefault("n_jobs", N_THREADS)
    merged.setdefault("verbose", -1)

    model = lgb.LGBMClassifier(**merged)
    callbacks = [lgb.early_stopping(early_stopping, verbose=False)] if early_stopping else []
    start = time.time()
    model.fit(data["Xtr"], data["ytr"], eval_set=[(data["Xva"], data["yva"])],
              eval_metric="auc", callbacks=callbacks)
    seconds = time.time() - start
    best_iteration = model.best_iteration_ or merged["n_estimators"]
    return gini(data["yva"], model.predict_proba(data["Xva"])[:, 1]), seconds, best_iteration, model


def fit_xgb(data: Dict[str, Any], params: Dict[str, Any],
            early_stopping: Optional[int] = EARLY_STOPPING_ROUNDS,
            n_estimators: int = 3000) -> Fitted:
    """Fit XGBoost (``tree_method="hist"``), optionally with early stopping."""
    import xgboost as xgb

    merged = dict(params)
    merged.setdefault("objective", "binary:logistic")
    merged.setdefault("eval_metric", "auc")
    merged.setdefault("tree_method", "hist")
    merged.setdefault("n_estimators", n_estimators)
    merged.setdefault("random_state", RANDOM_STATE)
    merged.setdefault("n_jobs", N_THREADS)
    if early_stopping:
        merged["early_stopping_rounds"] = early_stopping

    model = xgb.XGBClassifier(**merged)
    start = time.time()
    model.fit(data["Xtr"], data["ytr"], eval_set=[(data["Xva"], data["yva"])], verbose=False)
    seconds = time.time() - start
    best = getattr(model, "best_iteration", None)
    best_iteration = best + 1 if best is not None else merged["n_estimators"]
    return gini(data["yva"], model.predict_proba(data["Xva"])[:, 1]), seconds, best_iteration, model


def fit_cat(data: Dict[str, Any], params: Dict[str, Any],
            early_stopping: Optional[int] = EARLY_STOPPING_ROUNDS,
            iterations: int = 3000, native: bool = False) -> Fitted:
    """Fit CatBoost on the ordinal codes, or on raw strings when ``native``.

    ``allow_writing_files=False`` keeps the ``catboost_info/`` training log out
    of the repository.
    """
    from catboost import CatBoostClassifier, Pool

    merged = dict(params)
    merged.setdefault("loss_function", "Logloss")
    merged.setdefault("eval_metric", "AUC")
    merged.setdefault("iterations", iterations)
    merged.setdefault("random_seed", RANDOM_STATE)
    merged.setdefault("thread_count", N_THREADS)
    merged.setdefault("verbose", 0)
    merged.setdefault("allow_writing_files", False)
    if early_stopping:
        merged.setdefault("early_stopping_rounds", early_stopping)

    model = CatBoostClassifier(**merged)
    start = time.time()
    if native:
        cats = data["cat_cols"]
        pool_train = Pool(data["raw_tr"], data["ytr"], cat_features=cats)
        pool_valid = Pool(data["raw_va"], data["yva"], cat_features=cats)
        model.fit(pool_train, eval_set=pool_valid, use_best_model=True)
        seconds = time.time() - start
        score = gini(data["yva"], model.predict_proba(pool_valid)[:, 1])
    else:
        model.fit(data["Xtr"], data["ytr"], eval_set=(data["Xva"], data["yva"]),
                  use_best_model=True)
        seconds = time.time() - start
        score = gini(data["yva"], model.predict_proba(data["Xva"])[:, 1])
    return score, seconds, model.get_best_iteration() + 1, model


# --------------------------------------------------------------------------- #
# 3. Search space
# --------------------------------------------------------------------------- #
def _make_samplers(rng: np.random.RandomState) -> Dict[str, Callable[[], Dict[str, Any]]]:
    """Return one sampler per library, all drawing from the same ``rng``.

    The space is the one documented in Step 7 of the notebook.  ``U`` is
    uniform, ``log-U`` is uniform on the log scale, ``{...}`` is a discrete
    draw (repeated values are more likely).

    LightGBM (40 draws)
        ``learning_rate`` log-U(0.01, 0.12), ``num_leaves`` U{7..95},
        ``max_depth`` {-1, 3, 4, 5, 6, 8, 10}, ``min_child_samples`` U{10..249},
        ``subsample`` U(0.5, 1) with ``subsample_freq=1``,
        ``colsample_bytree`` U(0.4, 1), ``reg_lambda`` log-U(1e-3, 50),
        ``reg_alpha`` log-U(1e-3, 10), ``min_split_gain`` {0, 0, 0.01, 0.1}.
    XGBoost (40 draws)
        ``learning_rate`` log-U(0.01, 0.12), ``max_depth`` U{2..10},
        ``min_child_weight`` log-U(1, 60), ``subsample`` U(0.5, 1),
        ``colsample_bytree`` U(0.4, 1), ``reg_lambda`` log-U(0.1, 60),
        ``reg_alpha`` log-U(1e-3, 10), ``gamma`` {0, 0, 0.1, 0.5, 2}.
    CatBoost (18 ordinal + 12 native draws)
        ``learning_rate`` log-U(0.02, 0.2), ``depth`` U{4..8},
        ``l2_leaf_reg`` log-U(1, 30), ``random_strength`` U(0.5, 4),
        ``bagging_temperature`` U(0, 2), ``rsm`` U(0.5, 1).

    The tree count is never sampled: it is whatever early stopping selects on
    the validation fold (patience :data:`EARLY_STOPPING_ROUNDS`).
    """

    def loguniform(low: float, high: float) -> float:
        return float(np.exp(rng.uniform(np.log(low), np.log(high))))

    def lgb_sampler() -> Dict[str, Any]:
        return dict(
            learning_rate=loguniform(0.01, 0.12),
            num_leaves=int(rng.randint(7, 96)),
            max_depth=int(rng.choice([-1, 3, 4, 5, 6, 8, 10])),
            min_child_samples=int(rng.randint(10, 250)),
            colsample_bytree=float(rng.uniform(0.4, 1.0)),
            subsample=float(rng.uniform(0.5, 1.0)),
            subsample_freq=1,
            reg_lambda=loguniform(1e-3, 50.0),
            reg_alpha=loguniform(1e-3, 10.0),
            min_split_gain=float(rng.choice([0.0, 0.0, 0.01, 0.1])),
        )

    def xgb_sampler() -> Dict[str, Any]:
        return dict(
            learning_rate=loguniform(0.01, 0.12),
            max_depth=int(rng.randint(2, 11)),
            min_child_weight=loguniform(1.0, 60.0),
            subsample=float(rng.uniform(0.5, 1.0)),
            colsample_bytree=float(rng.uniform(0.4, 1.0)),
            reg_lambda=loguniform(0.1, 60.0),
            reg_alpha=loguniform(1e-3, 10.0),
            gamma=float(rng.choice([0.0, 0.0, 0.1, 0.5, 2.0])),
        )

    def cat_sampler() -> Dict[str, Any]:
        return dict(
            learning_rate=loguniform(0.02, 0.2),
            depth=int(rng.randint(4, 9)),
            l2_leaf_reg=loguniform(1.0, 30.0),
            random_strength=float(rng.uniform(0.5, 4.0)),
            bagging_temperature=float(rng.uniform(0.0, 2.0)),
            rsm=float(rng.uniform(0.5, 1.0)),
        )

    return {"lightgbm": lgb_sampler, "xgboost": xgb_sampler, "catboost": cat_sampler}


def random_search(name: str, sampler: Callable[[], Dict[str, Any]],
                  fitter: Callable[..., Fitted], n_iter: int, **fit_kwargs: Any) -> Fitted:
    """Draw ``n_iter`` configurations and keep the best validation Gini.

    A configuration that raises (an illegal parameter combination, say) is
    logged and skipped rather than aborting the whole search.

    Returns
    -------
    tuple
        ``(gini, params, seconds, best_iteration, model)`` of the winner.
    """
    log(f"\n=== RANDOM SEARCH {name}: {n_iter} configurations ===")
    best: Tuple[float, Any, Any, Any, Any] = (-1.0, None, None, None, None)
    started = time.time()
    for i in range(n_iter):
        params = sampler()
        try:
            score, seconds, iterations, model = fitter(params=params, **fit_kwargs)
        except Exception as error:  # a bad draw must not kill the search
            log(f"  [{i:02d}] FAILED {error}")
            continue
        if score > best[0]:
            best = (score, params, seconds, iterations, model)
            log(f"  [{i:02d}] gini={score:.5f} *BEST* iters={iterations} {seconds:.1f}s")
        elif i % 5 == 0:
            log(f"  [{i:02d}] gini={score:.5f}")
    log(f"{name}: best valid gini={best[0]:.5f} after {n_iter} configs "
        f"(search took {time.time() - started:.0f}s)")
    return best  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# 4. The full experiment
# --------------------------------------------------------------------------- #
def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """Baselines, random search, DART and the final train/valid/test scoring."""
    from catboost import Pool

    results: Dict[str, Any] = {}

    # ---- library defaults, no early stopping ------------------------------ #
    log("\n=== BASELINES (library defaults, no early stopping) ===")
    baselines = {}
    for key, label, call in [
        ("lightgbm", "LightGBM  default",
         lambda: fit_lgb(data, {}, early_stopping=None, n_estimators=100)),
        ("xgboost", "XGBoost   default",
         lambda: fit_xgb(data, {}, early_stopping=None, n_estimators=100)),
        ("catboost", "CatBoost  default",
         lambda: fit_cat(data, {}, early_stopping=None, iterations=1000)),
        ("catboost_native", "CatBoost  default + native cat_features",
         lambda: fit_cat(data, {}, early_stopping=None, iterations=1000, native=True)),
    ]:
        score, seconds, iterations, _ = call()
        baselines[key] = dict(gini=score, sec=seconds, iters=iterations)
        log(f"{label}  valid gini={score:.5f}  {seconds:.1f}s")
    results["baseline"] = baselines

    # ---- random search ---------------------------------------------------- #
    samplers = _make_samplers(np.random.RandomState(RANDOM_STATE))
    searches = {
        "lightgbm": random_search("LightGBM", samplers["lightgbm"],
                                  lambda **kw: fit_lgb(data, **kw), N_LGB),
        "xgboost": random_search("XGBoost", samplers["xgboost"],
                                 lambda **kw: fit_xgb(data, **kw), N_XGB),
        "catboost": random_search("CatBoost (ordinal)", samplers["catboost"],
                                  lambda **kw: fit_cat(data, **kw), N_CAT),
        "catboost_native": random_search("CatBoost (native cat_features)", samplers["catboost"],
                                         lambda **kw: fit_cat(data, native=True, **kw),
                                         N_CAT_NATIVE),
    }
    sizes = {"lightgbm": N_LGB, "xgboost": N_XGB,
             "catboost": N_CAT, "catboost_native": N_CAT_NATIVE}

    results["tuned"] = {}
    for key, (score, params, seconds, iterations, _) in searches.items():
        results["tuned"][key] = dict(gini=score, params=params, sec=seconds,
                                     best_iter=iterations, n_configs=sizes[key])
        log(f"\nFINAL {key}: valid gini={score:.5f} best_iter={iterations} fit={seconds:.1f}s")
        log(f"  params={json.dumps(params, default=str)}")

    # ---- DART around the winning configurations --------------------------- #
    # Early stopping is meaningless for DART: the ensemble prediction is not
    # monotone in the tree count, so the tree budget is fixed instead.
    log("\n=== DART MODE ===")
    dart: Dict[str, Any] = {}
    lgb_best, xgb_best = searches["lightgbm"], searches["xgboost"]

    for drop_rate, skip_drop in [(0.1, 0.5), (0.2, 0.5), (0.05, 0.9)]:
        n_estimators = max(300, min(1500, int(lgb_best[3] * 1.5)))
        params = dict(lgb_best[1], boosting_type="dart", drop_rate=drop_rate,
                      skip_drop=skip_drop, n_estimators=n_estimators)
        score, seconds, _, _ = fit_lgb(data, params, early_stopping=None)
        dart[f"lgb_dart_dr{drop_rate}_sd{skip_drop}"] = dict(
            gini=score, sec=seconds, n_estimators=n_estimators)
        log(f"LightGBM DART drop_rate={drop_rate} skip_drop={skip_drop} n={n_estimators}: "
            f"valid gini={score:.5f}  {seconds:.1f}s")

    for rate_drop, skip_drop in [(0.1, 0.5), (0.2, 0.5)]:
        n_estimators = max(300, min(1200, xgb_best[3]))
        params = dict(xgb_best[1], booster="dart", rate_drop=rate_drop,
                      skip_drop=skip_drop, n_estimators=n_estimators)
        score, seconds, _, _ = fit_xgb(data, params, early_stopping=None)
        dart[f"xgb_dart_rd{rate_drop}_sd{skip_drop}"] = dict(
            gini=score, sec=seconds, n_estimators=n_estimators)
        log(f"XGBoost  DART rate_drop={rate_drop} skip_drop={skip_drop} n={n_estimators}: "
            f"valid gini={score:.5f}  {seconds:.1f}s")
    results["dart"] = dart

    # ---- the winner on train / validation / test -------------------------- #
    log("\n=== FINAL: BEST MODEL ON TRAIN / VALID / TEST ===")

    def scores(key: str, model: Any) -> Dict[str, float]:
        """Gini on all three folds; native CatBoost needs Pools, not matrices."""
        if key == "catboost_native":
            cats = data["cat_cols"]
            frames = [Pool(data[f"raw_{fold}"], cat_features=cats)
                      for fold in ("tr", "va", "te")]
        else:
            frames = [data["Xtr"], data["Xva"], data["Xte"]]
        targets = [data["ytr"], data["yva"], data["yte"]]
        return {fold: gini(y, model.predict_proba(X)[:, 1])
                for fold, X, y in zip(("train", "valid", "test"), frames, targets)}

    winner_key, winner = max(searches.items(), key=lambda item: item[1][0])
    log(f"winner = {winner_key}  (valid gini {winner[0]:.5f})")
    winner_scores = scores(winner_key, winner[4])
    results["final"] = dict(model=winner_key, params=winner[1], best_iter=winner[3],
                            gini_train=winner_scores["train"],
                            gini_valid=winner_scores["valid"],
                            gini_test=winner_scores["test"])
    for fold in ("train", "valid", "test"):
        log(f"  {fold:5s} gini = {winner_scores[fold]:.5f}")

    # For context only, and deliberately reported *after* the choice was made.
    log("\n--- test gini of all tuned candidates (context only) ---")
    context = {key: scores(key, search[4]) for key, search in searches.items()}
    for key, folds in context.items():
        log(f"  {key:16s} train={folds['train']:.5f} valid={folds['valid']:.5f} "
            f"test={folds['test']:.5f}")
    results["all_candidates_tvt"] = context

    return results


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for ``python -m src.tune``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA,
                        help="path to training.csv (default: <project root>/data/training.csv)")
    parser.add_argument("--out", type=Path, default=None,
                        help="optional path for a JSON dump of every measurement")
    args = parser.parse_args(argv)

    results = run(prepare(args.data))

    if args.out is not None:
        with open(args.out, "w") as handle:
            json.dump(results, handle, indent=2, default=str)
        log(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
