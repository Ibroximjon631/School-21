"""Data access layer for the "Don't Get Kicked" project.

The module is intentionally self contained: it loads the raw competition file,
performs a *time aware* train/validation/test split (task 1 of the README),
encodes the categorical columns without leaking information from the future,
and finally materialises plain ``numpy`` design matrices that every model in
``src.tree``/``src.ensemble``/``src.gbdt`` can consume.

Only ``numpy``/``pandas``/``scikit-learn`` are used.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

__all__ = [
    "RANDOM_STATE",
    "TARGET",
    "DATE_COLUMN",
    "load_raw",
    "time_split",
    "OrdinalEncoder",
    "FrequencyEncoder",
    "split_columns",
    "build_datasets",
    "gini",
]

RANDOM_STATE = 42
TARGET = "IsBadBuy"
DATE_COLUMN = "PurchDate"

#: Columns that are stored as integers but semantically are identifiers, i.e.
#: their numeric ordering carries no meaning.  They are treated as categorical.
ID_LIKE_COLUMNS: Tuple[str, ...] = ("WheelTypeID", "BYRNO", "VNZIP1")

#: Columns that must never enter the design matrix.
DROP_COLUMNS: Tuple[str, ...] = (TARGET, DATE_COLUMN, "RefId")


# --------------------------------------------------------------------------- #
# Loading & splitting
# --------------------------------------------------------------------------- #
def load_raw(path: str = "data/training.csv") -> pd.DataFrame:
    """Read the raw competition csv and normalise the purchase date.

    ``PurchDate`` is stored as a unix timestamp (seconds) in the provided file;
    it is converted to a proper ``datetime64`` column so that the time based
    split below is easy to reason about.

    Parameters
    ----------
    path:
        Location of ``training.csv``.

    Returns
    -------
    pandas.DataFrame
        The raw frame, sorted by ``PurchDate`` (stable sort, so the original
        row order is preserved inside a single day).
    """
    frame = pd.read_csv(path)

    if DATE_COLUMN in frame.columns:
        column = frame[DATE_COLUMN]
        if pd.api.types.is_numeric_dtype(column):
            # Unix epoch expressed in seconds.
            frame[DATE_COLUMN] = pd.to_datetime(column, unit="s")
        else:
            frame[DATE_COLUMN] = pd.to_datetime(column)
        frame = frame.sort_values(DATE_COLUMN, kind="mergesort").reset_index(drop=True)

    return frame


def time_split(
    frame: pd.DataFrame,
    train_share: float = 0.33,
    valid_share: float = 0.33,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split ``frame`` chronologically into train / validation / test.

    The split is performed on the *unique* purchase dates, therefore a single
    day never ends up in two different folds and the guarantee
    ``train.PurchDate.max() < valid.PurchDate.min() < valid.PurchDate.max() <
    test.PurchDate.min()`` always holds.

    Parameters
    ----------
    frame:
        Output of :func:`load_raw`.
    train_share, valid_share:
        Fractions of the *unique dates* that go to train and validation.  The
        remainder becomes the test fold.

    Returns
    -------
    tuple of DataFrame
        ``(train, valid, test)``.
    """
    if DATE_COLUMN not in frame.columns:
        raise KeyError(f"{DATE_COLUMN!r} is required for a time based split")

    dates = np.sort(frame[DATE_COLUMN].unique())
    n_dates = dates.size
    if n_dates < 3:
        raise ValueError("not enough distinct dates to build three folds")

    first_cut = max(1, int(round(n_dates * train_share)))
    second_cut = max(first_cut + 1, int(round(n_dates * (train_share + valid_share))))
    second_cut = min(second_cut, n_dates - 1)

    train_end = dates[first_cut - 1]
    valid_end = dates[second_cut - 1]

    values = frame[DATE_COLUMN].to_numpy()
    train = frame.loc[values <= train_end].reset_index(drop=True)
    valid = frame.loc[(values > train_end) & (values <= valid_end)].reset_index(drop=True)
    test = frame.loc[values > valid_end].reset_index(drop=True)

    # Defensive check - the contract of this function.
    assert train[DATE_COLUMN].max() < valid[DATE_COLUMN].min()
    assert valid[DATE_COLUMN].max() < test[DATE_COLUMN].min()
    return train, valid, test


# --------------------------------------------------------------------------- #
# Encoders
# --------------------------------------------------------------------------- #
def _unique_sorted(series: pd.Series) -> np.ndarray:
    """Return the deterministic, sorted set of non null values of ``series``."""
    values = pd.unique(series.dropna().to_numpy())
    try:
        return np.sort(values)
    except TypeError:  # pragma: no cover - mixed types inside one column
        return np.array(sorted(values, key=repr), dtype=object)


class OrdinalEncoder:
    """Label-encoder style transformer that is safe for unseen categories.

    The mapping is built **on the training fold only**; anything that was not
    observed during :meth:`fit` (including missing values) is mapped to
    ``unknown_value`` (``-1`` by default), which keeps "unknown" a separate,
    learnable branch for a tree based model.
    """

    def __init__(self, unknown_value: float = -1.0) -> None:
        self.unknown_value = float(unknown_value)
        self.columns_: List[str] = []
        self.mapping_: Dict[str, Dict[object, int]] = {}

    def fit(self, frame: pd.DataFrame, columns: Iterable[str]) -> "OrdinalEncoder":
        """Learn ``category -> code`` mappings for ``columns`` of ``frame``."""
        self.columns_ = list(columns)
        self.mapping_ = {}
        for column in self.columns_:
            categories = _unique_sorted(frame[column])
            self.mapping_[column] = {value: code for code, value in enumerate(categories)}
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of ``frame`` with the fitted columns replaced by codes."""
        out = frame.copy()
        for column in self.columns_:
            mapping = self.mapping_[column]
            codes = pd.Series(frame[column].to_numpy(), index=frame.index).map(mapping)
            out[column] = codes.astype("float64").fillna(self.unknown_value)
        return out

    def fit_transform(self, frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """Convenience wrapper around :meth:`fit` + :meth:`transform`."""
        return self.fit(frame, columns).transform(frame)


class FrequencyEncoder:
    """Count (frequency) encoding, the equivalent of
    ``category_encoders.CountEncoder(normalize=True)``.

    Every category is replaced by the share of the *training* rows it covers.
    Unseen categories and missing values become ``0.0`` which is a natural
    extrapolation: "this value never appeared in the training period".
    """

    def __init__(self, unknown_value: float = 0.0) -> None:
        self.unknown_value = float(unknown_value)
        self.columns_: List[str] = []
        self.frequencies_: Dict[str, Dict[object, float]] = {}

    def fit(self, frame: pd.DataFrame, columns: Iterable[str]) -> "FrequencyEncoder":
        """Learn the normalised value counts of ``columns`` of ``frame``."""
        self.columns_ = list(columns)
        self.frequencies_ = {}
        n_rows = max(len(frame), 1)
        for column in self.columns_:
            counts = frame[column].value_counts(dropna=True)
            self.frequencies_[column] = {
                key: float(value) / n_rows for key, value in counts.items()
            }
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of ``frame`` with the fitted columns replaced by counts."""
        out = frame.copy()
        for column in self.columns_:
            table = self.frequencies_[column]
            values = pd.Series(frame[column].to_numpy(), index=frame.index).map(table)
            out[column] = values.astype("float64").fillna(self.unknown_value)
        return out

    def fit_transform(self, frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """Convenience wrapper around :meth:`fit` + :meth:`transform`."""
        return self.fit(frame, columns).transform(frame)


_ENCODERS = {"ordinal": OrdinalEncoder, "frequency": FrequencyEncoder}


# --------------------------------------------------------------------------- #
# Design matrices
# --------------------------------------------------------------------------- #
def split_columns(frame: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Split the feature columns of ``frame`` into categorical and numeric.

    Non numeric dtypes are categorical by definition; on top of that the
    identifier-like integer columns listed in :data:`ID_LIKE_COLUMNS` are
    treated as categorical because their numeric order is meaningless.
    """
    features = [c for c in frame.columns if c not in DROP_COLUMNS]
    categorical, numeric = [], []
    for column in features:
        if column in ID_LIKE_COLUMNS or not pd.api.types.is_numeric_dtype(frame[column]):
            categorical.append(column)
        else:
            numeric.append(column)
    return categorical, numeric


def _to_matrix(
    frame: pd.DataFrame,
    columns: Sequence[str],
    medians: "pd.Series",
    nan_columns: Sequence[str],
) -> np.ndarray:
    """Materialise a float64 matrix, median-imputing and adding NaN flags."""
    block = frame.loc[:, list(columns)].astype("float64")
    flags = [block[column].isna().to_numpy(dtype=np.float64) for column in nan_columns]
    values = block.fillna(medians).to_numpy(dtype=np.float64)
    if flags:
        values = np.column_stack([values] + flags)
    # Anything still missing (e.g. an all-NaN training column) becomes 0.
    return np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)


def build_datasets(path: str = "data/training.csv", encoding: str = "ordinal") -> Dict[str, object]:
    """Build ready-to-train numpy datasets for the three chronological folds.

    Steps
    -----
    1. load the raw csv and split it by ``PurchDate``;
    2. fit the requested categorical encoder **on the training fold only**;
    3. median-impute the numeric columns with *training* medians, keeping one
       ``<column>_nan`` indicator per numeric column that has missing values in
       the training fold;
    4. return everything as plain ``numpy`` arrays plus the raw frames.

    Parameters
    ----------
    path:
        Location of ``training.csv``.
    encoding:
        ``"ordinal"`` (label encoding, unseen -> -1) or ``"frequency"``
        (normalised count encoding, unseen -> 0.0).

    Returns
    -------
    dict
        Keys: ``Xtr``/``Xva``/``Xte`` (float64 matrices without NaNs),
        ``ytr``/``yva``/``yte`` (int arrays), ``feature_names`` (list of str),
        ``train``/``valid``/``test`` (raw frames), ``cat_cols``/``num_cols``
        and ``encoder`` (the fitted encoder instance).
    """
    if encoding not in _ENCODERS:
        raise ValueError(f"encoding must be one of {sorted(_ENCODERS)}, got {encoding!r}")

    raw = load_raw(path)
    train, valid, test = time_split(raw)

    cat_cols, num_cols = split_columns(raw)

    encoder = _ENCODERS[encoding]()
    encoder.fit(train, cat_cols)
    train_enc = encoder.transform(train)
    valid_enc = encoder.transform(valid)
    test_enc = encoder.transform(test)

    feature_columns = cat_cols + num_cols
    medians = train_enc.loc[:, feature_columns].astype("float64").median()
    # A NaN indicator is only worth keeping when the training fold really has
    # gaps there - deciding this on train alone avoids any leakage.
    nan_columns = [
        column
        for column in feature_columns
        if bool(train_enc[column].isna().any())
    ]

    feature_names = list(feature_columns) + [f"{c}_nan" for c in nan_columns]

    datasets: Dict[str, object] = {
        "Xtr": _to_matrix(train_enc, feature_columns, medians, nan_columns),
        "Xva": _to_matrix(valid_enc, feature_columns, medians, nan_columns),
        "Xte": _to_matrix(test_enc, feature_columns, medians, nan_columns),
        "ytr": train[TARGET].to_numpy(dtype=np.int64),
        "yva": valid[TARGET].to_numpy(dtype=np.int64),
        "yte": test[TARGET].to_numpy(dtype=np.int64),
        "feature_names": feature_names,
        "train": train,
        "valid": valid,
        "test": test,
        "cat_cols": cat_cols,
        "num_cols": num_cols,
        "encoder": encoder,
        "encoding": encoding,
    }
    return datasets


# --------------------------------------------------------------------------- #
# Metric
# --------------------------------------------------------------------------- #
def gini(y_true, y_score) -> float:
    """Normalised Gini coefficient, ``2 * ROC-AUC - 1``.

    ``y_score`` may be a probability vector or a ``(n, 2)`` ``predict_proba``
    output, in which case the positive-class column is used.
    """
    score = np.asarray(y_score, dtype=np.float64)
    if score.ndim == 2:
        score = score[:, -1]
    return 2.0 * roc_auc_score(np.asarray(y_true), score) - 1.0
