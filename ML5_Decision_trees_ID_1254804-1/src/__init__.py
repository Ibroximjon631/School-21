"""From-scratch decision tree / ensemble implementations for the
"Supervised Learning. Decision Trees and ensembles" project.

Modules
-------
``src.data``
    Loading, chronological splitting, categorical encoding, Gini metric.
``src.tree``
    ``DecisionTreeClassifier`` / ``DecisionTreeRegressor`` (CART, histogram
    based split search, optional extra-randomised splitter).
``src.ensemble``
    ``RandomForestClassifier`` / ``ExtraTreesClassifier``.
``src.gbdt``
    ``GradientBoostingClassifier`` (binary cross-entropy gradients).
"""

from . import data, ensemble, gbdt, tree  # noqa: F401

__all__ = ["data", "tree", "ensemble", "gbdt"]
