"""End-to-end self check of the hand written models.

Run it from the project root::

    .venv/bin/python -m src.selfcheck

It builds the chronological datasets, fits every model implemented in
``src.tree`` / ``src.ensemble`` / ``src.gbdt``, prints the validation Gini of
each of them and then asserts

* the quality thresholds required by the README (0.10 for a single tree, 0.15
  for the random forest, 0.12 for the extra trees, and a gradient boosting
  model that beats the single tree);
* that ``random_state`` really makes a fit reproducible;
* that ``DecisionTreeRegressor`` is in the same ballpark as sklearn's;
* that ``predict_proba`` returns rows that sum to one and that ``predict``
  agrees with ``argmax(predict_proba)``.

The script exits with a non-zero status as soon as one of the checks fails.
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

import numpy as np

from .data import RANDOM_STATE, build_datasets, gini
from .ensemble import ExtraTreesClassifier, RandomForestClassifier
from .gbdt import GradientBoostingClassifier
from .tree import DecisionTreeClassifier, DecisionTreeRegressor

# --------------------------------------------------------------------------- #
# Hyper parameters that were tuned on the validation fold.
# --------------------------------------------------------------------------- #
TREE_PARAMS = dict(max_depth=7, min_samples_leaf=50, random_state=RANDOM_STATE)
EXTRA_TREE_PARAMS = dict(
    max_depth=7, min_samples_leaf=50, splitter="random", random_state=RANDOM_STATE
)
FOREST_PARAMS = dict(
    n_estimators=100,
    max_depth=10,
    min_samples_leaf=20,
    max_features="sqrt",
    random_state=RANDOM_STATE,
)
EXTRA_TREES_PARAMS = dict(
    n_estimators=100,
    max_depth=14,
    min_samples_leaf=20,
    max_features="sqrt",
    random_state=RANDOM_STATE,
)
GBDT_PARAMS = dict(
    n_estimators=300,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=50,
    random_state=RANDOM_STATE,
)

#: README requirements (task 3, 5, 9); the GBDT is additionally compared to the
#: single tree.
THRESHOLDS = {
    "DecisionTreeClassifier": 0.10,
    "RandomForestClassifier": 0.15,
    "ExtraTreesClassifier": 0.12,
    "GradientBoostingClassifier": 0.20,
}


def _timed_fit(model, X, y, **kwargs):
    """Fit ``model`` and return it together with the elapsed seconds."""
    start = time.perf_counter()
    model.fit(X, y, **kwargs)
    return model, time.perf_counter() - start


def _check_proba(name: str, model, X) -> None:
    """``predict_proba`` must be a valid distribution and match ``predict``."""
    proba = model.predict_proba(X)
    assert proba.ndim == 2 and proba.shape == (X.shape[0], 2), f"{name}: bad proba shape"
    assert np.all(proba >= -1e-12) and np.all(proba <= 1 + 1e-12), f"{name}: proba out of [0, 1]"
    assert np.allclose(proba.sum(axis=1), 1.0), f"{name}: proba rows do not sum to 1"
    expected = model.classes_[np.argmax(proba, axis=1)]
    assert np.array_equal(model.predict(X), expected), f"{name}: predict != argmax(predict_proba)"


def _check_reproducible(name: str, factory, X, y, Xva) -> None:
    """Two fits with the same ``random_state`` must be bit-identical."""
    first = factory().fit(X, y).predict_proba(Xva)
    second = factory().fit(X, y).predict_proba(Xva)
    assert np.array_equal(first, second), f"{name}: random_state is not reproducible"


def _check_regressor(data: Dict[str, object]) -> Tuple[float, float]:
    """Compare the own regressor with sklearn's on a small numeric subset."""
    from sklearn.tree import DecisionTreeRegressor as SkDecisionTreeRegressor

    names: List[str] = list(data["feature_names"])  # type: ignore[arg-type]
    target_name = "VehBCost" if "VehBCost" in names else names[-1]
    target_index = names.index(target_name)
    numeric = [
        names.index(column)
        for column in data["num_cols"]  # type: ignore[union-attr]
        if column in names and column != target_name
    ][:12]

    Xtr = np.asarray(data["Xtr"])[:4000][:, numeric]
    ytr = np.asarray(data["Xtr"])[:4000, target_index]
    Xva = np.asarray(data["Xva"])[:4000][:, numeric]
    yva = np.asarray(data["Xva"])[:4000, target_index]

    own = DecisionTreeRegressor(max_depth=5, min_samples_leaf=20, random_state=RANDOM_STATE)
    own.fit(Xtr, ytr)
    reference = SkDecisionTreeRegressor(
        max_depth=5, min_samples_leaf=20, random_state=RANDOM_STATE
    ).fit(Xtr, ytr)

    own_mse = float(np.mean((yva - own.predict(Xva)) ** 2))
    sk_mse = float(np.mean((yva - reference.predict(Xva)) ** 2))
    return own_mse, sk_mse


def main() -> int:
    """Run every check and print a small report."""
    print("=" * 78)
    print("Self check of the hand written tree models")
    print("=" * 78)

    start = time.perf_counter()
    data = build_datasets()
    Xtr, ytr = np.asarray(data["Xtr"]), np.asarray(data["ytr"])
    Xva, yva = np.asarray(data["Xva"]), np.asarray(data["yva"])
    print(
        f"data built in {time.perf_counter() - start:5.1f}s | "
        f"train {Xtr.shape}, valid {Xva.shape}, test {np.asarray(data['Xte']).shape} | "
        f"positive rate train={ytr.mean():.4f} valid={yva.mean():.4f}"
    )
    print()

    results: List[Tuple[str, float, float, float]] = []
    models = {}

    # --- 1. single CART ---------------------------------------------------- #
    tree, seconds = _timed_fit(DecisionTreeClassifier(**TREE_PARAMS), Xtr, ytr)
    models["DecisionTreeClassifier"] = tree
    results.append(
        (
            "DecisionTreeClassifier",
            gini(ytr, tree.predict_proba(Xtr)),
            gini(yva, tree.predict_proba(Xva)),
            seconds,
        )
    )

    # --- 2. single extra randomised tree ----------------------------------- #
    extra_tree, seconds = _timed_fit(DecisionTreeClassifier(**EXTRA_TREE_PARAMS), Xtr, ytr)
    models["ExtraRandomizedTree"] = extra_tree
    results.append(
        (
            "ExtraRandomizedTree",
            gini(ytr, extra_tree.predict_proba(Xtr)),
            gini(yva, extra_tree.predict_proba(Xva)),
            seconds,
        )
    )

    # --- 3. random forest --------------------------------------------------- #
    forest, seconds = _timed_fit(RandomForestClassifier(**FOREST_PARAMS), Xtr, ytr)
    models["RandomForestClassifier"] = forest
    results.append(
        (
            "RandomForestClassifier",
            gini(ytr, forest.predict_proba(Xtr)),
            gini(yva, forest.predict_proba(Xva)),
            seconds,
        )
    )

    # --- 4. extra trees ----------------------------------------------------- #
    extra, seconds = _timed_fit(ExtraTreesClassifier(**EXTRA_TREES_PARAMS), Xtr, ytr)
    models["ExtraTreesClassifier"] = extra
    results.append(
        (
            "ExtraTreesClassifier",
            gini(ytr, extra.predict_proba(Xtr)),
            gini(yva, extra.predict_proba(Xva)),
            seconds,
        )
    )

    # --- 5. gradient boosting ------------------------------------------------ #
    boosting, seconds = _timed_fit(
        GradientBoostingClassifier(**GBDT_PARAMS), Xtr, ytr, eval_set=(Xva, yva)
    )
    models["GradientBoostingClassifier"] = boosting
    results.append(
        (
            "GradientBoostingClassifier",
            gini(ytr, boosting.predict_proba(Xtr)),
            gini(yva, boosting.predict_proba(Xva)),
            seconds,
        )
    )

    # --- report -------------------------------------------------------------- #
    print(f"{'model':<28}{'train Gini':>12}{'valid Gini':>12}{'fit, s':>10}{'required':>10}")
    print("-" * 78)
    for name, train_score, valid_score, seconds in results:
        requirement = THRESHOLDS.get(name)
        needed = f"{requirement:.2f}" if requirement else "-"
        print(f"{name:<28}{train_score:>12.4f}{valid_score:>12.4f}{seconds:>10.1f}{needed:>10}")
    print()

    scores = {name: valid for name, _, valid, _ in results}

    # --- assertions ---------------------------------------------------------- #
    for name, requirement in THRESHOLDS.items():
        assert scores[name] >= requirement, (
            f"{name}: validation Gini {scores[name]:.4f} < required {requirement:.2f}"
        )
    print("[ok] every README quality threshold is met")

    assert scores["RandomForestClassifier"] > scores["DecisionTreeClassifier"], (
        "the random forest must improve on the single tree"
    )
    assert scores["ExtraTreesClassifier"] > scores["ExtraRandomizedTree"], (
        "the extra trees ensemble must improve on a single randomised tree"
    )
    assert scores["GradientBoostingClassifier"] > scores["DecisionTreeClassifier"], (
        "gradient boosting must improve on the single tree"
    )
    print("[ok] every ensemble improves on its single tree baseline")

    # --- predict / predict_proba contract ------------------------------------ #
    for name, model in models.items():
        _check_proba(name, model, Xva[:2000])
    print("[ok] predict_proba rows sum to 1 and predict == argmax(predict_proba)")

    # --- reproducibility ----------------------------------------------------- #
    small = slice(0, 8000)
    _check_reproducible(
        "DecisionTreeClassifier(splitter='random')",
        lambda: DecisionTreeClassifier(**EXTRA_TREE_PARAMS),
        Xtr[small],
        ytr[small],
        Xva[:2000],
    )
    _check_reproducible(
        "RandomForestClassifier",
        lambda: RandomForestClassifier(
            n_estimators=10, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE
        ),
        Xtr[small],
        ytr[small],
        Xva[:2000],
    )
    _check_reproducible(
        "ExtraTreesClassifier",
        lambda: ExtraTreesClassifier(
            n_estimators=10, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE
        ),
        Xtr[small],
        ytr[small],
        Xva[:2000],
    )
    _check_reproducible(
        "GradientBoostingClassifier",
        lambda: GradientBoostingClassifier(
            n_estimators=20, max_depth=3, subsample=0.8, random_state=RANDOM_STATE
        ),
        Xtr[small],
        ytr[small],
        Xva[:2000],
    )
    different = RandomForestClassifier(
        n_estimators=10, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE + 1
    ).fit(Xtr[small], ytr[small])
    same = RandomForestClassifier(
        n_estimators=10, max_depth=8, min_samples_leaf=20, random_state=RANDOM_STATE
    ).fit(Xtr[small], ytr[small])
    assert not np.array_equal(
        different.predict_proba(Xva[:2000]), same.predict_proba(Xva[:2000])
    ), "different seeds should produce different forests"
    print("[ok] random_state gives reproducible fits (and different seeds differ)")

    # --- regressor sanity check ----------------------------------------------- #
    own_mse, sk_mse = _check_regressor(data)
    ratio = own_mse / sk_mse
    assert 0.5 <= ratio <= 1.5, (
        f"DecisionTreeRegressor MSE {own_mse:.1f} is far from sklearn's {sk_mse:.1f}"
    )
    print(
        f"[ok] DecisionTreeRegressor MSE {own_mse:,.1f} vs sklearn {sk_mse:,.1f} "
        f"(ratio {ratio:.3f})"
    )

    # --- boosting bookkeeping ------------------------------------------------- #
    assert len(boosting.estimators_) == boosting.number_of_trees == GBDT_PARAMS["n_estimators"]
    assert boosting.train_loss_[-1] < boosting.train_loss_[0], "boosting did not reduce the loss"
    print(
        f"[ok] boosting reduced the train loss {boosting.train_loss_[0]:.4f} -> "
        f"{boosting.train_loss_[-1]:.4f}; best validation iteration = "
        f"{boosting.best_iteration_}"
    )

    print()
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
