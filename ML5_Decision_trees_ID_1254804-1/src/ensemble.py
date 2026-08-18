"""Bagging ensembles built on :mod:`src.tree` (README tasks 5 and 9).

``RandomForestClassifier``
    Bagging of CART trees: every tree sees a bootstrap sample of the rows and,
    at every node, a random subset of the columns.  The prediction is the
    average of the per-tree class probabilities.
``ExtraTreesClassifier``
    "Extremely randomised trees": *no* row subsampling by default, only column
    subsampling, and the base learners are extra randomised trees - for every
    candidate feature a single random threshold is drawn and the best of those
    candidates is used (``splitter="random"`` of :mod:`src.tree`).

Both classes bin the design matrix **once** and share the result between all
the trees, which is where most of the speed comes from.
"""

from __future__ import annotations

from typing import List, Optional, Union

import numpy as np

from .tree import Binning, DecisionTreeClassifier

__all__ = ["RandomForestClassifier", "ExtraTreesClassifier"]


class _BaseForest:
    """Shared fit/predict logic of the two bagging ensembles."""

    #: Splitter used by the base trees, overridden by ``ExtraTreesClassifier``.
    _splitter = "best"

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        max_features: Union[None, str, int, float] = "sqrt",
        min_samples_leaf: int = 1,
        max_bins: int = 32,
        bootstrap: bool = True,
        random_state: Optional[int] = None,
        n_jobs: int = 1,
        min_samples_split: int = 2,
        max_samples: Optional[float] = None,
    ) -> None:
        self.n_estimators = int(n_estimators)
        self.max_depth = max_depth
        self.max_features = max_features
        self.min_samples_leaf = int(min_samples_leaf)
        self.max_bins = int(max_bins)
        self.bootstrap = bool(bootstrap)
        self.random_state = random_state
        self.n_jobs = int(n_jobs)
        self.min_samples_split = int(min_samples_split)
        self.max_samples = max_samples

        self.estimators_: List[DecisionTreeClassifier] = []
        self.classes_: np.ndarray = np.empty(0)
        self.n_features_in_: int = 0

    # -- helpers ----------------------------------------------------------- #
    def get_params(self) -> dict:
        """Return the constructor arguments as a dictionary."""
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "max_features": self.max_features,
            "min_samples_leaf": self.min_samples_leaf,
            "max_bins": self.max_bins,
            "bootstrap": self.bootstrap,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
            "min_samples_split": self.min_samples_split,
            "max_samples": self.max_samples,
        }

    def _sample_indices(self, n_rows: int, rng: np.random.Generator) -> Optional[np.ndarray]:
        """Rows used by a single tree (bootstrap sample or the full fold)."""
        if not self.bootstrap:
            return None
        size = n_rows
        if self.max_samples is not None:
            size = max(1, int(round(float(self.max_samples) * n_rows)))
        return rng.integers(0, n_rows, size=size)

    def _make_tree(self, seed: int) -> DecisionTreeClassifier:
        return DecisionTreeClassifier(
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            max_features=self.max_features,
            max_bins=self.max_bins,
            splitter=self._splitter,
            random_state=seed,
            store_indices=False,
        )

    # -- fit --------------------------------------------------------------- #
    def fit(self, X, y) -> "_BaseForest":
        """Train ``n_estimators`` trees on bootstrap/column subsamples."""
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y have different numbers of rows")

        self.n_features_in_ = X.shape[1]
        self.classes_ = np.unique(y)
        if self.classes_.size > 2:
            raise ValueError("only binary targets are supported")

        # One binning for the whole forest - the trees only need the codes.
        self.binning_ = Binning(self.max_bins).fit(X)
        codes = self.binning_.transform(X)

        # Independent, reproducible seeds for every tree.
        seed_sequence = np.random.SeedSequence(self.random_state)
        seeds = seed_sequence.spawn(self.n_estimators)
        row_rng = np.random.default_rng(seed_sequence.spawn(1)[0])
        row_samples = [self._sample_indices(X.shape[0], row_rng) for _ in range(self.n_estimators)]

        def build(index: int) -> DecisionTreeClassifier:
            tree = self._make_tree(np.random.default_rng(seeds[index]).integers(0, 2**31 - 1))
            tree.fit_prebinned(codes, self.binning_, y, sample_indices=row_samples[index])
            return tree

        if self.n_jobs == 1:
            self.estimators_ = [build(i) for i in range(self.n_estimators)]
        else:
            from joblib import Parallel, delayed  # ships with scikit-learn

            self.estimators_ = list(
                Parallel(n_jobs=self.n_jobs, backend="threading")(
                    delayed(build)(i) for i in range(self.n_estimators)
                )
            )

        self.feature_importances_ = np.mean(
            [tree.feature_importances_ for tree in self.estimators_], axis=0
        )
        return self

    # -- predict ----------------------------------------------------------- #
    def predict_proba(self, X) -> np.ndarray:
        """Average of the class probabilities of every tree, shape ``(n, 2)``."""
        if not self.estimators_:
            raise RuntimeError("the forest is not fitted yet")
        X = np.asarray(X, dtype=np.float64)
        proba = np.zeros((X.shape[0], 2), dtype=np.float64)
        for tree in self.estimators_:
            proba += tree.predict_proba(X)
        return proba / len(self.estimators_)

    def predict(self, X) -> np.ndarray:
        """Predicted labels, i.e. ``argmax`` of :meth:`predict_proba`."""
        indices = np.argmax(self.predict_proba(X), axis=1)
        if self.classes_.size >= 2:
            return self.classes_[indices]
        return np.full(indices.shape, self.classes_[0])


class RandomForestClassifier(_BaseForest):
    """Bagged CART classifiers (README task 5).

    Parameters
    ----------
    n_estimators:
        Number of trees in the forest.
    max_depth:
        Maximum depth of every tree (``None`` = grow until the stopping
        criteria of the base tree fire).
    max_features:
        Columns examined at each node, ``"sqrt"`` by default.
    min_samples_leaf:
        Minimum number of training samples in a leaf.
    max_bins:
        Quantile bins used to discretise the features.
    bootstrap:
        Draw a bootstrap sample of the rows for each tree (the "bagging" part).
    random_state:
        Seed; two forests fitted with the same seed are identical.
    n_jobs:
        ``1`` fits the trees sequentially, any other value uses ``joblib``
        with the threading backend.

    Examples
    --------
    >>> forest = RandomForestClassifier(n_estimators=100, random_state=42)
    >>> forest.fit(Xtrain, ytrain).predict_proba(Xvalid)[:, 1]
    """

    _splitter = "best"


class ExtraTreesClassifier(_BaseForest):
    """Extremely randomised trees (README task 9, bonus).

    Differences with :class:`RandomForestClassifier`:

    * ``bootstrap`` is ``False`` by default - the whole training fold is used,
      the randomness comes from the splits only;
    * the base learners use ``splitter="random"``: at each node one threshold
      per candidate feature is drawn at random and the best of those draws is
      selected.

    That makes the individual trees weaker but much less correlated, so the
    average is typically less prone to overfitting than a random forest.
    """

    _splitter = "random"

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        max_features: Union[None, str, int, float] = "sqrt",
        min_samples_leaf: int = 1,
        max_bins: int = 32,
        bootstrap: bool = False,
        random_state: Optional[int] = None,
        n_jobs: int = 1,
        min_samples_split: int = 2,
        max_samples: Optional[float] = None,
    ) -> None:
        super().__init__(
            n_estimators=n_estimators,
            max_depth=max_depth,
            max_features=max_features,
            min_samples_leaf=min_samples_leaf,
            max_bins=max_bins,
            bootstrap=bootstrap,
            random_state=random_state,
            n_jobs=n_jobs,
            min_samples_split=min_samples_split,
            max_samples=max_samples,
        )
