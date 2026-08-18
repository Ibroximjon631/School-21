"""Gradient boosted decision trees, from scratch (README task 6).

The model is the classic additive one

    ``F_0(x) = log(p / (1 - p))``          (log-odds of the training mean)
    ``F_m(x) = F_{m-1}(x) + lr * h_m(x)``

where ``h_m`` is a :class:`src.tree.DecisionTreeRegressor` fitted on the
**negative gradient of the binary cross-entropy loss**

    ``L(y, F) = -[y log(sigma(F)) + (1 - y) log(1 - sigma(F))]``
    ``-dL/dF  = y - sigma(F)``            (the "pseudo residual")

so every new tree literally learns the mistakes the current ensemble still
makes - this is the incremental learning required by the task.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple, Union

import numpy as np

from .tree import Binning, DecisionTreeRegressor

__all__ = ["GradientBoostingClassifier", "sigmoid"]

_EPS = 1e-12


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable logistic function."""
    x = np.asarray(x, dtype=np.float64)
    out = np.empty_like(x)
    positive = x >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    out[~positive] = exp_x / (1.0 + exp_x)
    return out


def _log_loss(y: np.ndarray, scores: np.ndarray) -> float:
    """Mean binary cross-entropy of raw scores (log-odds)."""
    p = np.clip(sigmoid(scores), 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


class GradientBoostingClassifier:
    """Binary GBDT built on the project's own regression trees.

    Parameters
    ----------
    n_estimators:
        Number of boosting iterations, also available as ``number_of_trees``.
    max_depth:
        Depth of every regression tree (boosting wants *weak* learners).
    learning_rate:
        Shrinkage applied to the contribution of each tree.
    max_features:
        Columns examined at each node of the trees (``None``, ``"sqrt"``,
        ``"log2"``, an integer or a fraction).
    subsample:
        Fraction of the training rows drawn (without replacement) for each
        iteration - "stochastic gradient boosting".
    max_bins:
        Quantile bins used to discretise the features.  The binning is
        computed once and reused by every tree.
    random_state:
        Seed of the row/column sampling.
    min_samples_leaf:
        Minimum number of samples per leaf of the regression trees.
    leaf_estimation:
        ``"newton"`` (default) rescales the leaf values with one Newton step
        of the cross-entropy loss, ``sum(y - p) / sum(p (1 - p))``, which is
        what sklearn's ``GradientBoostingClassifier`` does; ``"mean"`` keeps
        the plain mean of the pseudo residuals produced by the MSE tree.

    Attributes
    ----------
    estimators_ : list of DecisionTreeRegressor
    init_score_ : float
        ``log(p / (1 - p))`` of the training fold.
    train_loss_, eval_loss_ : list of float
        Cross-entropy after each iteration (``eval_loss_`` only when an
        ``eval_set`` was passed to :meth:`fit`).
    best_iteration_ : int
        1-based iteration with the lowest ``eval_loss_``.

    Examples
    --------
    >>> gb = GradientBoostingClassifier(n_estimators=300, max_depth=4,
    ...                                 learning_rate=0.05, random_state=42)
    >>> gb.fit(Xtrain, ytrain, eval_set=(Xvalid, yvalid))
    >>> proba = gb.predict_proba(Xvalid)[:, 1]
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1,
        max_features: Union[None, str, int, float] = None,
        subsample: float = 1.0,
        max_bins: int = 32,
        random_state: Optional[int] = None,
        min_samples_leaf: int = 1,
        leaf_estimation: str = "newton",
    ) -> None:
        if not 0.0 < subsample <= 1.0:
            raise ValueError("subsample must lie in (0, 1]")
        if leaf_estimation not in ("newton", "mean"):
            raise ValueError("leaf_estimation must be 'newton' or 'mean'")
        self.n_estimators = int(n_estimators)
        self.max_depth = int(max_depth)
        self.learning_rate = float(learning_rate)
        self.max_features = max_features
        self.subsample = float(subsample)
        self.max_bins = int(max_bins)
        self.random_state = random_state
        self.min_samples_leaf = int(min_samples_leaf)
        self.leaf_estimation = leaf_estimation

        self.estimators_: List[DecisionTreeRegressor] = []
        self.init_score_: float = 0.0
        self.classes_: np.ndarray = np.array([0, 1])
        self.n_features_in_: int = 0
        self.train_loss_: List[float] = []
        self.eval_loss_: List[float] = []
        self.best_iteration_: int = 0

    # -- README task 6 asks for a ``number_of_trees`` attribute ------------- #
    @property
    def number_of_trees(self) -> int:
        """Alias of ``n_estimators`` (the name used in the assignment)."""
        return self.n_estimators

    @number_of_trees.setter
    def number_of_trees(self, value: int) -> None:
        self.n_estimators = int(value)

    def get_params(self) -> dict:
        """Return the constructor arguments as a dictionary."""
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "max_features": self.max_features,
            "subsample": self.subsample,
            "max_bins": self.max_bins,
            "random_state": self.random_state,
            "min_samples_leaf": self.min_samples_leaf,
            "leaf_estimation": self.leaf_estimation,
        }

    # -- fit --------------------------------------------------------------- #
    def fit(self, X, y, eval_set=None) -> "GradientBoostingClassifier":
        """Fit ``n_estimators`` trees on the successive pseudo residuals.

        Parameters
        ----------
        X, y:
            Training design matrix and binary target.
        eval_set:
            Optional ``(X, y)`` tuple (or a list with a single one) used to
            monitor the validation loss; it never influences the fit.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        if self.classes_.size > 2:
            raise ValueError("only binary targets are supported")
        y = (y == self.classes_[-1]).astype(np.float64)
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y have different numbers of rows")

        n_rows = X.shape[0]
        self.n_features_in_ = X.shape[1]

        # Bin once, reuse for every tree of the ensemble.
        self.binning_ = Binning(self.max_bins).fit(X)
        codes = self.binning_.transform(X)

        prior = float(np.clip(y.mean(), 1e-6, 1 - 1e-6))
        self.init_score_ = float(np.log(prior / (1.0 - prior)))

        scores = np.full(n_rows, self.init_score_, dtype=np.float64)
        eval_sets = self._check_eval_set(eval_set)
        eval_scores = [np.full(ye.shape[0], self.init_score_) for _, ye in eval_sets]

        rng = np.random.default_rng(self.random_state)
        seeds = rng.integers(0, 2**31 - 1, size=self.n_estimators)
        n_subsample = max(1, int(round(self.subsample * n_rows)))

        self.estimators_ = []
        self.train_loss_ = []
        self.eval_loss_ = []

        for iteration in range(self.n_estimators):
            probabilities = sigmoid(scores)
            residuals = y - probabilities  # negative gradient of the BCE loss

            if self.subsample < 1.0:
                sample = rng.choice(n_rows, size=n_subsample, replace=False)
            else:
                sample = None

            tree = DecisionTreeRegressor(
                max_depth=self.max_depth,
                min_samples_split=2,
                min_samples_leaf=self.min_samples_leaf,
                max_features=self.max_features,
                max_bins=self.max_bins,
                splitter="best",
                random_state=int(seeds[iteration]),
                store_indices=False,
            )
            tree.fit_prebinned(codes, self.binning_, residuals, sample_indices=sample)

            if self.leaf_estimation == "newton":
                self._newton_update(tree, X, residuals, probabilities, sample)

            update = tree.predict(X)
            scores += self.learning_rate * update
            self.estimators_.append(tree)

            self.train_loss_.append(_log_loss(y, scores))
            for position, (Xe, ye) in enumerate(eval_sets):
                eval_scores[position] += self.learning_rate * tree.predict(Xe)
            if eval_sets:
                self.eval_loss_.append(_log_loss(eval_sets[0][1], eval_scores[0]))

        if self.eval_loss_:
            self.best_iteration_ = int(np.argmin(self.eval_loss_)) + 1
        else:
            self.best_iteration_ = len(self.estimators_)
        return self

    # -- helpers ----------------------------------------------------------- #
    @staticmethod
    def _check_eval_set(eval_set) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Normalise ``eval_set`` into a list of ``(X, y)`` numpy pairs."""
        if eval_set is None:
            return []
        if isinstance(eval_set, tuple) and len(eval_set) == 2:
            eval_set = [eval_set]
        out = []
        for Xe, ye in eval_set:
            ye = np.asarray(ye)
            classes = np.unique(ye)
            ye = (ye == classes[-1]).astype(np.float64) if classes.size > 1 else ye.astype(np.float64)
            out.append((np.asarray(Xe, dtype=np.float64), ye))
        return out

    def _newton_update(
        self,
        tree: DecisionTreeRegressor,
        X: np.ndarray,
        residuals: np.ndarray,
        probabilities: np.ndarray,
        sample: Optional[np.ndarray],
    ) -> None:
        """Replace each leaf mean by one Newton step of the logistic loss."""
        rows = np.arange(X.shape[0]) if sample is None else sample
        leaves = tree.apply(X[rows])
        hessians = probabilities[rows] * (1.0 - probabilities[rows])
        n_nodes = tree.n_nodes_
        numerator = np.bincount(leaves, weights=residuals[rows], minlength=n_nodes)
        denominator = np.bincount(leaves, weights=hessians, minlength=n_nodes)
        values = np.where(denominator > 1e-9, numerator / np.maximum(denominator, 1e-9), 0.0)
        # Guard against the huge steps that appear in almost pure leaves.
        tree.set_leaf_values(np.clip(values, -10.0, 10.0))

    # -- prediction -------------------------------------------------------- #
    def decision_function(self, X, n_trees: Optional[int] = None) -> np.ndarray:
        """Raw additive score (log-odds) of the first ``n_trees`` trees."""
        X = np.asarray(X, dtype=np.float64)
        limit = len(self.estimators_) if n_trees is None else int(n_trees)
        scores = np.full(X.shape[0], self.init_score_, dtype=np.float64)
        for tree in self.estimators_[:limit]:
            scores += self.learning_rate * tree.predict(X)
        return scores

    def predict_proba(self, X, n_trees: Optional[int] = None) -> np.ndarray:
        """Class probabilities, shape ``(n_samples, 2)``."""
        positive = sigmoid(self.decision_function(X, n_trees=n_trees))
        return np.column_stack([1.0 - positive, positive])

    def predict(self, X, n_trees: Optional[int] = None) -> np.ndarray:
        """Predicted labels, i.e. ``argmax`` of :meth:`predict_proba`."""
        indices = np.argmax(self.predict_proba(X, n_trees=n_trees), axis=1)
        if self.classes_.size >= 2:
            return self.classes_[indices]
        return np.full(indices.shape, self.classes_[0])

    def staged_predict_proba(self, X) -> Iterable[np.ndarray]:
        """Yield the probabilities after each boosting iteration."""
        X = np.asarray(X, dtype=np.float64)
        scores = np.full(X.shape[0], self.init_score_, dtype=np.float64)
        for tree in self.estimators_:
            scores += self.learning_rate * tree.predict(X)
            positive = sigmoid(scores)
            yield np.column_stack([1.0 - positive, positive])

    @property
    def feature_importances_(self) -> np.ndarray:
        """Mean impurity-reduction importance over all the trees."""
        if not self.estimators_:
            raise RuntimeError("the model is not fitted yet")
        importances = np.mean(
            [tree.feature_importances_ for tree in self.estimators_], axis=0
        )
        total = importances.sum()
        return importances / total if total > 0 else importances
