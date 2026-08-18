"""From-scratch CART implementation (README task 2).

The module provides

``Node``
    A single node of the tree: the samples that reached it, its impurity, the
    split it performs and the pointers to its children.
``Binning``
    Quantile pre-binning of the design matrix.  Binning is what makes the
    split search fast: instead of testing every distinct value of a feature we
    only test at most ``max_bins - 1`` quantile thresholds, and the whole scan
    over those thresholds is a couple of ``numpy`` calls.
``DecisionTreeClassifier``
    Binary classifier, Gini impurity criterion, ``splitter="best"`` (exhaustive
    scan over the binned thresholds) or ``splitter="random"`` (extra randomised
    tree: one random threshold is drawn per candidate feature and the best of
    those draws wins).
``DecisionTreeRegressor``
    Regressor with the MSE (= standard deviation reduction) criterion; used as
    the base learner of the gradient boosting model.

Implementation notes
--------------------
*   ``fit`` never copies the data: the recursion works on ``numpy`` index
    arrays only.
*   For a node the split search is vectorised over **all** candidate features
    at once: the (row, feature) bin codes are flattened into a single integer
    array, one ``np.bincount`` gives the per-(feature, bin) histogram, and a
    cumulative sum along the bin axis scores every threshold of every feature
    simultaneously.
*   After the tree is grown it is flattened into plain arrays so that
    ``predict`` is a simple iterative descent over index arrays.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple, Union

import numpy as np

__all__ = ["Node", "Binning", "DecisionTreeClassifier", "DecisionTreeRegressor"]

_EPS = 1e-12


# --------------------------------------------------------------------------- #
# Node
# --------------------------------------------------------------------------- #
class Node:
    """One node of a decision tree.

    Parameters
    ----------
    depth:
        Distance from the root (the root has ``depth == 0``).
    n_samples:
        Number of training samples that reached the node.
    impurity:
        Gini impurity (classifier) or variance/MSE (regressor) of the node.
    value:
        The prediction of the node: the class distribution for the classifier
        (``array([p0, p1])``) or the mean target for the regressor.
    indices:
        Optional array with the indices of the training samples that reached
        the node.  Kept only when the tree was fitted with
        ``store_indices=True`` (the default for a stand-alone tree; the
        ensembles switch it off to save memory).
    targets:
        Optional view on the targets of those samples.
    """

    def __init__(
        self,
        depth: int,
        n_samples: int,
        impurity: float,
        value: np.ndarray,
        indices: Optional[np.ndarray] = None,
        targets: Optional[np.ndarray] = None,
    ) -> None:
        self.depth = int(depth)
        self.n_samples = int(n_samples)
        self.impurity = float(impurity)
        self.value = value
        self.indices = indices
        self.targets = targets

        # Filled in when the node is split.
        self.feature: Optional[int] = None
        self.threshold: Optional[float] = None
        self.left: Optional["Node"] = None
        self.right: Optional["Node"] = None
        #: Position of the node inside the flattened arrays used by ``predict``.
        self.node_id: int = -1

    # -- helpers ---------------------------------------------------------- #
    @property
    def is_leaf(self) -> bool:
        """``True`` when the node has no children."""
        return self.left is None and self.right is None

    @staticmethod
    def gini_impurity(y: np.ndarray) -> float:
        """Gini impurity ``1 - sum(p_k^2)`` of a label vector."""
        y = np.asarray(y)
        if y.size == 0:
            return 0.0
        counts = np.bincount(y.astype(np.int64))
        p = counts / y.size
        return float(1.0 - np.sum(p * p))

    @staticmethod
    def mse_impurity(y: np.ndarray) -> float:
        """Variance (mean squared error around the mean) of a target vector."""
        y = np.asarray(y, dtype=np.float64)
        if y.size == 0:
            return 0.0
        return float(np.mean((y - y.mean()) ** 2))

    def split_rule(self) -> str:
        """Human readable description of the split performed by the node."""
        if self.is_leaf:
            return "leaf"
        return f"x[{self.feature}] <= {self.threshold:.6g}"

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        kind = "Leaf" if self.is_leaf else "Node"
        return (
            f"<{kind} depth={self.depth} n={self.n_samples} "
            f"impurity={self.impurity:.4f} rule={self.split_rule()}>"
        )


# --------------------------------------------------------------------------- #
# Binning
# --------------------------------------------------------------------------- #
class Binning:
    """Quantile pre-binning of a design matrix.

    Every feature is mapped to at most ``max_bins`` bins.  ``edges_[j]`` holds
    the sorted split candidates of feature ``j``; a sample with value ``v``
    receives the code ``searchsorted(edges_[j], v, side="left")``, hence

        ``code <= b``  is equivalent to  ``v <= edges_[j][b]``

    which is exactly the ``<=`` convention used by the tree at prediction time.
    """

    def __init__(self, max_bins: int = 32) -> None:
        if max_bins < 2:
            raise ValueError("max_bins must be >= 2")
        self.max_bins = int(max_bins)
        self.edges_: List[np.ndarray] = []
        self.n_bins_: np.ndarray = np.empty(0, dtype=np.int64)
        self.max_n_bins_: int = 1

    def fit(self, X: np.ndarray) -> "Binning":
        """Compute the quantile thresholds of every column of ``X``."""
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError("X must be a 2d array")

        quantiles = np.linspace(0.0, 1.0, self.max_bins + 1)[1:-1]
        edges: List[np.ndarray] = []
        for j in range(X.shape[1]):
            column = X[:, j]
            unique = np.unique(column)
            if unique.size <= 1:
                candidates = np.empty(0, dtype=np.float64)
            elif unique.size <= self.max_bins:
                # Few distinct values: every value but the largest is a split.
                candidates = unique[:-1]
            else:
                candidates = np.unique(np.quantile(column, quantiles))
                # A threshold equal to the maximum would send everything left.
                candidates = candidates[candidates < unique[-1]]
            edges.append(np.ascontiguousarray(candidates, dtype=np.float64))

        self.edges_ = edges
        self.n_bins_ = np.array([e.size + 1 for e in edges], dtype=np.int64)
        self.max_n_bins_ = int(self.n_bins_.max()) if len(edges) else 1
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Map ``X`` to its bin codes (C-ordered ``uint8``/``uint16`` matrix)."""
        X = np.asarray(X, dtype=np.float64)
        if X.shape[1] != len(self.edges_):
            raise ValueError("number of features does not match the fitted binning")

        dtype = np.uint8 if self.max_n_bins_ <= 256 else np.uint16
        codes = np.empty(X.shape, dtype=dtype)
        for j, edge in enumerate(self.edges_):
            if edge.size:
                codes[:, j] = np.searchsorted(edge, X[:, j], side="left")
            else:
                codes[:, j] = 0
        return codes

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """``fit`` followed by ``transform``."""
        return self.fit(X).transform(X)


def _resolve_max_features(
    max_features: Union[None, str, int, float], n_features: int
) -> int:
    """Translate the ``max_features`` argument into a number of columns."""
    if max_features is None:
        return n_features
    if isinstance(max_features, str):
        if max_features in ("sqrt", "auto"):
            return max(1, int(np.sqrt(n_features)))
        if max_features == "log2":
            return max(1, int(np.log2(n_features)))
        raise ValueError(f"unknown max_features={max_features!r}")
    if isinstance(max_features, (bool, np.bool_)):
        raise ValueError("max_features must not be a boolean")
    if isinstance(max_features, (int, np.integer)):
        return int(np.clip(int(max_features), 1, n_features))
    fraction = float(max_features)
    if not 0.0 < fraction <= 1.0:
        raise ValueError("a float max_features must lie in (0, 1]")
    return int(np.clip(int(round(fraction * n_features)), 1, n_features))


# --------------------------------------------------------------------------- #
# Base tree
# --------------------------------------------------------------------------- #
class _BaseTree:
    """Shared machinery of the classification and the regression tree."""

    def __init__(
        self,
        max_depth: Optional[int] = 7,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Union[None, str, int, float] = None,
        max_bins: int = 32,
        splitter: str = "best",
        random_state: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        store_indices: bool = True,
    ) -> None:
        if splitter not in ("best", "random"):
            raise ValueError("splitter must be 'best' or 'random'")
        self.max_depth = max_depth
        self.min_samples_split = int(min_samples_split)
        self.min_samples_leaf = int(min_samples_leaf)
        self.max_features = max_features
        self.max_bins = int(max_bins)
        self.splitter = splitter
        self.random_state = random_state
        self.min_impurity_decrease = float(min_impurity_decrease)
        self.store_indices = bool(store_indices)

        self.root_: Optional[Node] = None
        self.n_features_in_: int = 0
        self.n_nodes_: int = 0
        self.max_depth_: int = 0

    # -- parameters (sklearn-like, handy for the notebook) ----------------- #
    def get_params(self) -> dict:
        """Return the constructor arguments as a dictionary."""
        return {
            "max_depth": self.max_depth,
            "min_samples_split": self.min_samples_split,
            "min_samples_leaf": self.min_samples_leaf,
            "max_features": self.max_features,
            "max_bins": self.max_bins,
            "splitter": self.splitter,
            "random_state": self.random_state,
            "min_impurity_decrease": self.min_impurity_decrease,
        }

    # -- public API -------------------------------------------------------- #
    def fit(self, X, y) -> "_BaseTree":
        """Grow the tree on ``(X, y)`` and return ``self``."""
        X = np.asarray(X, dtype=np.float64)
        y = self._prepare_y(y)
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y have different numbers of rows")
        binning = Binning(self.max_bins).fit(X)
        codes = binning.transform(X)
        return self.fit_prebinned(codes, binning, y, sample_indices=None, prepared=True)

    def fit_prebinned(
        self,
        codes: np.ndarray,
        binning: Binning,
        y: np.ndarray,
        sample_indices: Optional[np.ndarray] = None,
        prepared: bool = False,
    ) -> "_BaseTree":
        """Grow the tree from an already binned design matrix.

        This entry point exists so that an ensemble can bin the data once and
        share the result between all of its trees (``sample_indices`` then
        selects the bootstrap/subsample rows of a single tree).
        """
        if not prepared:
            y = self._prepare_y(y)
        self._binning = binning
        self._codes = codes
        self._y = y
        self.n_features_in_ = codes.shape[1]
        self.feature_importances_ = np.zeros(self.n_features_in_, dtype=np.float64)

        rng = np.random.default_rng(self.random_state)
        n_candidates = _resolve_max_features(self.max_features, self.n_features_in_)
        all_features = np.arange(self.n_features_in_, dtype=np.int64)
        max_depth = np.inf if self.max_depth is None else int(self.max_depth)

        if sample_indices is None:
            indices = np.arange(codes.shape[0], dtype=np.int64)
        else:
            indices = np.asarray(sample_indices, dtype=np.int64)
        if indices.size == 0:
            raise ValueError("cannot fit a tree on an empty sample")

        self._n_total = float(indices.size)
        self.root_ = self._make_node(0, indices)
        stack: List[Tuple[Node, np.ndarray]] = [(self.root_, indices)]
        self.max_depth_ = 0

        while stack:
            node, idx = stack.pop()
            self.max_depth_ = max(self.max_depth_, node.depth)

            if (
                node.depth >= max_depth
                or idx.size < self.min_samples_split
                or idx.size < 2 * self.min_samples_leaf
                or node.impurity <= _EPS
            ):
                continue

            if n_candidates < self.n_features_in_:
                features = rng.choice(all_features, size=n_candidates, replace=False)
                features.sort()
            else:
                features = all_features

            split = self._find_split(idx, features, node, rng)
            if split is None:
                continue
            feature, threshold, gain, left_mask = split

            node.feature = int(feature)
            node.threshold = float(threshold)
            self.feature_importances_[feature] += gain * idx.size / self._n_total

            left_idx = idx[left_mask]
            right_idx = idx[~left_mask]
            node.left = self._make_node(node.depth + 1, left_idx)
            node.right = self._make_node(node.depth + 1, right_idx)
            stack.append((node.left, left_idx))
            stack.append((node.right, right_idx))

        total = self.feature_importances_.sum()
        if total > 0:
            self.feature_importances_ /= total

        self._flatten()
        # The raw data is not needed any more; dropping it keeps ensembles small.
        self._codes = None
        self._y = None
        return self

    # -- prediction -------------------------------------------------------- #
    def apply(self, X) -> np.ndarray:
        """Return the id of the leaf every row of ``X`` falls into."""
        X = np.asarray(X, dtype=np.float64)
        if self.root_ is None:
            raise RuntimeError("the tree is not fitted yet")
        if X.shape[1] != self.n_features_in_:
            raise ValueError("X has a different number of features than during fit")

        out = np.empty(X.shape[0], dtype=np.int64)
        stack = [(0, np.arange(X.shape[0], dtype=np.int64))]
        while stack:
            node_id, idx = stack.pop()
            if idx.size == 0:
                continue
            feature = self._node_feature[node_id]
            if feature < 0:
                out[idx] = node_id
                continue
            mask = X[idx, feature] <= self._node_threshold[node_id]
            stack.append((self._node_left[node_id], idx[mask]))
            stack.append((self._node_right[node_id], idx[~mask]))
        return out

    def get_depth(self) -> int:
        """Depth of the fitted tree."""
        return self.max_depth_

    def get_n_leaves(self) -> int:
        """Number of leaves of the fitted tree."""
        return int(np.sum(self._node_feature < 0))

    # -- internals to be provided by the subclasses ------------------------ #
    def _prepare_y(self, y) -> np.ndarray:
        raise NotImplementedError

    def _make_node(self, depth: int, idx: np.ndarray) -> Node:
        raise NotImplementedError

    def _find_split(self, idx, features, node, rng):
        raise NotImplementedError

    def _fill_values(self, nodes: Sequence[Node]) -> None:
        raise NotImplementedError

    # -- flattening -------------------------------------------------------- #
    def _flatten(self) -> None:
        """Copy the node tree into flat arrays so ``apply`` is a plain descent."""
        nodes: List[Node] = []
        stack = [self.root_]
        while stack:
            node = stack.pop()
            node.node_id = len(nodes)
            nodes.append(node)
            if not node.is_leaf:
                stack.append(node.left)
                stack.append(node.right)

        n = len(nodes)
        self.n_nodes_ = n
        self._node_feature = np.full(n, -1, dtype=np.int64)
        self._node_threshold = np.zeros(n, dtype=np.float64)
        self._node_left = np.full(n, -1, dtype=np.int64)
        self._node_right = np.full(n, -1, dtype=np.int64)

        for node in nodes:
            if not node.is_leaf:
                i = node.node_id
                self._node_feature[i] = node.feature
                self._node_threshold[i] = node.threshold
                self._node_left[i] = node.left.node_id
                self._node_right[i] = node.right.node_id

        self._fill_values(nodes)

    # -- shared split helpers ---------------------------------------------- #
    def _gather(self, idx: np.ndarray, features: np.ndarray) -> np.ndarray:
        """Bin codes of the rows ``idx`` restricted to ``features``."""
        block = self._codes[idx]
        if features.size != self.n_features_in_:
            block = block[:, features]
        return block

    def _flat_codes(self, block: np.ndarray, n_bins: int) -> np.ndarray:
        """Offset the per-feature codes so a single ``bincount`` scores them all."""
        offsets = np.arange(block.shape[1], dtype=np.int32) * n_bins
        return block.astype(np.int32, copy=False) + offsets

    def _candidate_mask(
        self,
        block: np.ndarray,
        valid: np.ndarray,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Restrict the thresholds that take part in the search.

        For ``splitter="best"`` every admissible threshold is a candidate.  For
        ``splitter="random"`` (extra randomised tree) exactly one threshold per
        feature is drawn uniformly from the bins observed in the node, and the
        best of those draws is kept.
        """
        if self.splitter == "best":
            return valid

        low = block.min(axis=0).astype(np.int64)
        high = block.max(axis=0).astype(np.int64)
        drawn = np.zeros_like(valid)
        movable = high > low
        if not np.any(movable):
            return drawn
        # rng.integers(low, high) draws in [low, high - 1]: the left child then
        # always keeps the smallest bin and the right child the largest one.
        picks = rng.integers(low[movable], high[movable])
        drawn[np.flatnonzero(movable), picks] = True
        return drawn & valid


# --------------------------------------------------------------------------- #
# Classifier
# --------------------------------------------------------------------------- #
class DecisionTreeClassifier(_BaseTree):
    """CART classifier with the Gini impurity criterion (README task 2).

    Parameters
    ----------
    max_depth:
        Maximum depth of the tree, ``None`` for unlimited.
    min_samples_split:
        A node is only split when it holds at least that many samples.
    min_samples_leaf:
        Minimum number of samples in each child of a split.
    max_features:
        Number of features examined at every node: ``None`` (all), ``"sqrt"``,
        ``"log2"``, an integer or a fraction of the columns.
    max_bins:
        Number of quantile bins used to pre-discretise the features.
    splitter:
        ``"best"`` scans every binned threshold, ``"random"`` builds an *extra
        randomised* tree (one random threshold per candidate feature).
    random_state:
        Seed of the feature/threshold sampling; makes the fit reproducible.
    min_impurity_decrease:
        A split is only accepted when it reduces the impurity by at least this
        (sample weighted) amount.
    store_indices:
        Keep the training sample indices/targets inside every ``Node``.

    Examples
    --------
    >>> model = DecisionTreeClassifier(max_depth=7).fit(Xtrain, ytrain)
    >>> proba = model.predict_proba(Xvalid)
    """

    def __init__(
        self,
        max_depth: Optional[int] = 7,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Union[None, str, int, float] = None,
        max_bins: int = 32,
        splitter: str = "best",
        random_state: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        store_indices: bool = True,
    ) -> None:
        super().__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            max_bins=max_bins,
            splitter=splitter,
            random_state=random_state,
            min_impurity_decrease=min_impurity_decrease,
            store_indices=store_indices,
        )
        self.classes_: np.ndarray = np.empty(0)
        self.n_classes_: int = 0

    # -- data preparation -------------------------------------------------- #
    def _prepare_y(self, y) -> np.ndarray:
        y = np.asarray(y)
        classes, encoded = np.unique(y, return_inverse=True)
        if classes.size > 2:
            raise ValueError(
                "DecisionTreeClassifier only supports binary targets, "
                f"got {classes.size} classes"
            )
        self.classes_ = classes
        self.n_classes_ = int(classes.size)
        return encoded.astype(np.int64, copy=False)

    # -- node bookkeeping -------------------------------------------------- #
    def _make_node(self, depth: int, idx: np.ndarray) -> Node:
        targets = self._y[idx]
        counts = np.bincount(targets, minlength=max(self.n_classes_, 2)).astype(np.float64)
        total = counts.sum()
        proba = counts / total if total else counts
        impurity = 1.0 - float(np.sum(proba * proba))
        node = Node(
            depth=depth,
            n_samples=idx.size,
            impurity=impurity,
            value=proba,
            indices=idx if self.store_indices else None,
            targets=targets if self.store_indices else None,
        )
        node._counts = counts  # cached for the split search
        return node

    # -- split search ------------------------------------------------------ #
    def _find_split(self, idx, features, node, rng):
        """Score every candidate threshold of every candidate feature at once."""
        block = self._gather(idx, features)
        n_bins = self._binning.max_n_bins_
        n_total = idx.size
        n_positive = float(node._counts[1]) if node._counts.size > 1 else 0.0

        flat = self._flat_codes(block, n_bins)
        n_features = block.shape[1]
        counts = np.bincount(flat.ravel(), minlength=n_features * n_bins)
        counts = counts.reshape(n_features, n_bins).astype(np.float64)

        # y is binary, so the positive histogram is a bincount over positive rows.
        positive_rows = self._y[idx] == 1
        if np.any(positive_rows):
            pos_counts = np.bincount(
                flat[positive_rows].ravel(), minlength=n_features * n_bins
            ).reshape(n_features, n_bins).astype(np.float64)
        else:
            pos_counts = np.zeros_like(counts)

        left_n = np.cumsum(counts, axis=1)[:, :-1]
        left_p = np.cumsum(pos_counts, axis=1)[:, :-1]
        right_n = n_total - left_n
        right_p = n_positive - left_p

        valid = (left_n >= self.min_samples_leaf) & (right_n >= self.min_samples_leaf)
        valid = self._candidate_mask(block, valid, rng)
        if not np.any(valid):
            return None

        with np.errstate(divide="ignore", invalid="ignore"):
            # weighted Gini = (n_L * gini_L + n_R * gini_R) / n, and
            # n_k * gini_k = 2 * pos_k * neg_k / n_k for a binary target.
            impurity_children = 2.0 * (
                np.where(left_n > 0, left_p * (left_n - left_p) / np.maximum(left_n, 1), 0.0)
                + np.where(right_n > 0, right_p * (right_n - right_p) / np.maximum(right_n, 1), 0.0)
            ) / n_total

        gains = np.where(valid, node.impurity - impurity_children, -np.inf)
        best = int(np.argmax(gains))
        gain = float(gains.ravel()[best])
        if not np.isfinite(gain) or gain <= max(self.min_impurity_decrease, _EPS):
            return None

        feature_pos, bin_pos = np.unravel_index(best, gains.shape)
        feature = int(features[feature_pos])
        threshold = float(self._binning.edges_[feature][bin_pos])
        left_mask = block[:, feature_pos] <= bin_pos
        return feature, threshold, gain, left_mask

    # -- flattening & prediction ------------------------------------------- #
    def _fill_values(self, nodes: Sequence[Node]) -> None:
        """Store the class distribution of every node."""
        width = max(self.n_classes_, 2)
        self._node_value = np.zeros((len(nodes), width), dtype=np.float64)
        for node in nodes:
            self._node_value[node.node_id, : node.value.size] = node.value

    def predict_proba(self, X) -> np.ndarray:
        """Class probabilities, shape ``(n_samples, 2)``."""
        leaves = self.apply(X)
        proba = self._node_value[leaves]
        if proba.shape[1] == 1:  # degenerate single class training set
            proba = np.column_stack([proba, np.zeros(proba.shape[0])])
        return proba

    def predict(self, X) -> np.ndarray:
        """Predicted labels, i.e. ``argmax`` of :meth:`predict_proba`."""
        indices = np.argmax(self.predict_proba(X), axis=1)
        if self.classes_.size >= 2:
            return self.classes_[indices]
        return np.full(indices.shape, self.classes_[0])


# --------------------------------------------------------------------------- #
# Regressor
# --------------------------------------------------------------------------- #
class DecisionTreeRegressor(_BaseTree):
    """CART regressor with the MSE / standard-deviation-reduction criterion.

    The constructor mirrors :class:`DecisionTreeClassifier`.  It is the base
    learner of :class:`src.gbdt.GradientBoostingClassifier`, where it is fitted
    on the negative gradient of the binary cross-entropy loss.
    """

    def __init__(
        self,
        max_depth: Optional[int] = 7,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Union[None, str, int, float] = None,
        max_bins: int = 32,
        splitter: str = "best",
        random_state: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        store_indices: bool = True,
    ) -> None:
        super().__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            max_bins=max_bins,
            splitter=splitter,
            random_state=random_state,
            min_impurity_decrease=min_impurity_decrease,
            store_indices=store_indices,
        )

    # -- data preparation -------------------------------------------------- #
    def _prepare_y(self, y) -> np.ndarray:
        return np.asarray(y, dtype=np.float64).ravel()

    # -- node bookkeeping -------------------------------------------------- #
    def _make_node(self, depth: int, idx: np.ndarray) -> Node:
        targets = self._y[idx]
        total = float(targets.sum())
        mean = total / idx.size
        # Variance computed from the raw moments (the tree only needs sums).
        impurity = float(np.dot(targets, targets) / idx.size - mean * mean)
        impurity = max(impurity, 0.0)
        node = Node(
            depth=depth,
            n_samples=idx.size,
            impurity=impurity,
            value=np.array([mean], dtype=np.float64),
            indices=idx if self.store_indices else None,
            targets=targets if self.store_indices else None,
        )
        node._sum = total
        return node

    # -- split search ------------------------------------------------------ #
    def _find_split(self, idx, features, node, rng):
        """Maximise the sum-of-squares reduction over all binned thresholds."""
        block = self._gather(idx, features)
        n_bins = self._binning.max_n_bins_
        n_total = idx.size
        total_sum = float(node._sum)

        flat = self._flat_codes(block, n_bins)
        n_features = block.shape[1]
        flat_ravel = flat.ravel()
        counts = np.bincount(flat_ravel, minlength=n_features * n_bins)
        counts = counts.reshape(n_features, n_bins).astype(np.float64)

        weights = np.repeat(self._y[idx], n_features)
        sums = np.bincount(flat_ravel, weights=weights, minlength=n_features * n_bins)
        sums = sums.reshape(n_features, n_bins)

        left_n = np.cumsum(counts, axis=1)[:, :-1]
        left_s = np.cumsum(sums, axis=1)[:, :-1]
        right_n = n_total - left_n
        right_s = total_sum - left_s

        valid = (left_n >= self.min_samples_leaf) & (right_n >= self.min_samples_leaf)
        valid = self._candidate_mask(block, valid, rng)
        if not np.any(valid):
            return None

        with np.errstate(divide="ignore", invalid="ignore"):
            # SSE(parent) - SSE(children) = sL^2/nL + sR^2/nR - s^2/n.
            reduction = (
                np.where(left_n > 0, left_s * left_s / np.maximum(left_n, 1), 0.0)
                + np.where(right_n > 0, right_s * right_s / np.maximum(right_n, 1), 0.0)
                - total_sum * total_sum / n_total
            )
        gains = np.where(valid, reduction / n_total, -np.inf)
        best = int(np.argmax(gains))
        gain = float(gains.ravel()[best])
        if not np.isfinite(gain) or gain <= max(self.min_impurity_decrease, _EPS):
            return None

        feature_pos, bin_pos = np.unravel_index(best, gains.shape)
        feature = int(features[feature_pos])
        threshold = float(self._binning.edges_[feature][bin_pos])
        left_mask = block[:, feature_pos] <= bin_pos
        return feature, threshold, gain, left_mask

    # -- flattening & prediction ------------------------------------------- #
    def _fill_values(self, nodes: Sequence[Node]) -> None:
        """Store the mean target of every node."""
        self._node_value = np.zeros(len(nodes), dtype=np.float64)
        for node in nodes:
            self._node_value[node.node_id] = float(node.value[0])

    def predict(self, X) -> np.ndarray:
        """Predicted values (the mean target of the reached leaf)."""
        return self._node_value[self.apply(X)]

    def set_leaf_values(self, values: np.ndarray) -> None:
        """Overwrite the leaf predictions (used by the Newton step of GBDT)."""
        values = np.asarray(values, dtype=np.float64)
        if values.shape[0] != self._node_value.shape[0]:
            raise ValueError("one value per node is required")
        self._node_value = values
