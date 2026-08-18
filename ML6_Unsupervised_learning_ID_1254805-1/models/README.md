# Saved model — MNIST PCA (784 -> 2)

Artifact for the **Submission** part of the project (README, Chapter V).
Produced by `03_visualizations.ipynb`; see that notebook for why PCA was chosen over
t-SNE / UMAP / LLE (short version: the task demands that *the compressed vector has the
same values*, so the model must be a deterministic parametric map. `TSNE` has no
`transform` at all, `UMAP.transform` runs a stochastic optimisation, and `LLE.transform`
is fragile and drags the whole training set along).

| | |
|---|---|
| file | `mnist_pca.joblib` (16.2 KB) |
| estimator | `sklearn.decomposition.PCA(n_components=2, svd_solver='full', random_state=42)` |
| fitted on | 10000 MNIST images (exactly 1000 per digit) drawn from the 70000 in `data/mnist.npz` |
| preprocessing at fit time | `X.astype(np.float64) / 255.0` |
| explained variance ratio | 0.095646, 0.071647  (sum 0.1673) |
| scikit-learn | 1.9.0 |
| numpy | 2.5.2 |
| joblib | 1.5.3 |
| python | 3.12.3 |

Machine-readable copy of the same facts: `mnist_pca_meta.json`.

## Preprocessing contract

`PCA.transform` computes `z = (x - mean_) @ components_.T`, and `mean_` was learnt on
pixels scaled to `[0, 1]`. Feed it anything else and the numbers will not match:

- **dtype** `np.float64` — cast *before* dividing;
- **scaling** divide by `255.0` and nothing else — no `StandardScaler`, no per-image
  normalisation, no manual mean subtraction (the model carries `mean_` itself);
- **shape** `(n_samples, 784)`, so a single digit needs `.reshape(1, -1)`;
- **output** `(n_samples, 2)` `float64`.

## How to load and apply

```python
import joblib, numpy as np

pca = joblib.load("models/mnist_pca.joblib")          # sklearn PCA, n_components=2

X = np.load("data/mnist.npz")["X"]                    # (70000, 784) uint8
digit = X[0].astype(np.float64) / 255.0               # the contract: float64, /255
z = pca.transform(digit.reshape(1, -1))               # -> (1, 2)

print(z)
```

## Expected result

Demo image: **`X[0]`**, the first MNIST training image, a handwritten **5**.

```
[[0.48286096 1.28573242]]
```

Full double precision (what `np.array_equal` is checked against):

```python
[[0.48286095691474973, 1.2857324188640864]]
```

Reproduced bit-for-bit in the notebook with
`np.array_equal(pca_in_memory.transform(x), joblib.load(path).transform(x))`.

If your numbers differ, check the scaling first — these are the two classic mistakes:

```
correct   (/255.0)        : [0.482861 1.285732]
forgot to divide by 255   : [853.886405 266.274210]
per-image standardised    : [2.576605 3.688152]
```

## Decompressing back to an image

```python
recon = pca.inverse_transform(z).reshape(28, 28)      # 2 numbers -> 28 x 28
```

Two components keep only 16.7 % of the total pixel variance, so the reconstruction is a
blurry average-digit-like blob, not a readable 5. That is expected: 2-D is a
visualisation budget, not a compression budget.
