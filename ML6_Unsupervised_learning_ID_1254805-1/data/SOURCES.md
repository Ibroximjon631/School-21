# Dataset sources

All datasets required by `README.md` (Chapter V "Dataset" + Chapter VI bonus) were obtained
**without Kaggle credentials** — no `~/.kaggle/kaggle.json` exists on this machine and the
Kaggle API is therefore unusable. Every file below comes from a public mirror or the original
upstream host. Row/frame counts were verified against the canonical published statistics.

Python used for all conversions: `.venv/bin/python` (numpy 2.5.2, pandas 3.0.5, scikit-learn 1.9.0, opencv 5.0.0).
No extra packages had to be installed — `curl` + `unzip` + the preinstalled stack were sufficient.

| File | Size | Shape / count | Used by |
|---|---|---|---|
| `Ratings.csv` | 21.6 MB | 1,149,780 x 3 | task 2 |
| `Users.csv` | 10.2 MB | 278,858 x 3 | task 2 |
| `Books.csv` | 69.9 MB | 271,379 x 8 | task 2 (optional, not required) |
| `mnist.npz` | 11.0 MB | X (70000, 784), y (70000,) | task 3, submission |
| `Video_008.avi` | 3.0 MB | 792 frames, 320x240, 10 fps | task 5 |
| `fer2013.npz` | 74.7 MB | X (35887, 48, 48), y (35887,) | Chapter VI bonus |
| `gray_china.png`, `gray_flower.png`, `gray_hopper.png` | 0.5 MB total | 427x640, 427x640, 600x512 grayscale | task 4 (**generated**, not downloaded) |

---

## 1. Book Recommendation Dataset — `Ratings.csv`, `Users.csv` (+ `Books.csv`)

README source: <https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset>

That Kaggle dataset is a repackaging of the classic **Book-Crossing** dataset collected by
Cai-Nicolas Ziegler (2004). The original upstream host is dead:

```
http://www2.informatik.uni-freiburg.de/~cziegler/BX/BX-CSV-Dump.zip   -> HTTP 404
http://www2.informatik.uni-freiburg.de/~cziegler/BX/                  -> HTTP 404
https://www.kaggle.com/api/v1/datasets/download/arashnic/...          -> HTTP 404 (needs auth)
```

**Mirror actually used** — a GitHub repository that vendors the untouched `BX-CSV-Dump`:

```bash
BASE="https://raw.githubusercontent.com/ashwanidv100/Recommendation-System---Book-Crossing-Dataset/master/BX-CSV-Dump"
curl -L -o BX-Users.csv        "$BASE/BX-Users.csv"          # 12,005,298 bytes
curl -L -o BX-Book-Ratings.csv "$BASE/BX-Book-Ratings.csv"   # 29,532,495 bytes
curl -L -o BX-Books.csv        "$BASE/BX-Books.csv"          # 77,516,059 bytes
```

### Transformation applied (BX format -> Kaggle format)

The `BX-*.csv` files are semicolon-separated, `latin-1` encoded, quote-all, with backslash
escaping. They were converted to the plain comma-separated form Kaggle publishes:

```python
import pandas as pd, numpy as np

common = dict(sep=';', encoding='latin-1', escapechar='\\', on_bad_lines='warn', low_memory=False)

users = pd.read_csv('BX-Users.csv', **common)          # cols already: User-ID, Location, Age
users['Age'] = pd.to_numeric(users['Age'].replace('NULL', np.nan), errors='coerce').astype('Int64')
users.to_csv('Users.csv', index=False)

ratings = pd.read_csv('BX-Book-Ratings.csv', **common) # cols already: User-ID, ISBN, Book-Rating
ratings.to_csv('Ratings.csv', index=False)

books = pd.read_csv('BX-Books.csv', **common)
books.to_csv('Books.csv', index=False)
```

Column names in the BX dump are **already identical** to the Kaggle ones, so no renaming was
needed. The only content change is `Age`: the literal string `NULL` became an empty field
(read back by pandas as `NaN`).

### Verified contents

`Ratings.csv` — columns `User-ID` (int64), `ISBN` (str), `Book-Rating` (int64)

```
shape = (1149780, 3)          <- matches the canonical 1,149,780 ratings
unique users = 105,283
unique ISBNs = 340,556
Book-Rating values 0..10 (0 = implicit interaction, 716,109 of them)
```

`Users.csv` — columns `User-ID` (int64), `Location` (str), `Age` (float64 with NaN)

```
shape = (278858, 3)           <- matches the canonical 278,858 users
Age populated : 168,096 / 278,858  (60.3%)
Age min/median/max : 0 / 32 / 244   (contains implausible outliers - clip before modelling)
Age within 5..100  : 166,848
```

Population actually usable for task 2 (user has >=1 rating **and** a known age):
**62,107 users** (61,640 once age is clipped to 5..100).
Sparse interaction matrix is `(105283, 340556)`, `nnz = 1,149,780`, density `3.2e-05`.

`Books.csv` is **not required** by the task (README asks only for Ratings + Users). It is kept
because it maps `ISBN -> Book-Title/Author`, which is handy for interpreting components.
Safe to delete if repo size matters.

---

## 2. MNIST — `mnist.npz`

README source: <http://yann.lecun.com/exdb/mnist/> (the original LeCun host is unreliable /
frequently 403s). Downloaded instead from the official PyTorch S3 mirror of the *same*
original idx files:

```bash
for f in train-images-idx3-ubyte.gz train-labels-idx1-ubyte.gz \
         t10k-images-idx3-ubyte.gz  t10k-labels-idx1-ubyte.gz; do
  curl -O "https://ossci-datasets.s3.amazonaws.com/mnist/$f"
done
```

The four idx files were parsed and concatenated **train-then-test**, which reproduces exactly
the layout and ordering of `sklearn.datasets.fetch_openml("mnist_784", version=1)`, then cached
as a compressed npz so the notebook loads instantly and offline:

```python
X = np.concatenate([train_images.reshape(60000, -1), test_images.reshape(10000, -1)]).astype(np.uint8)
y = np.concatenate([train_labels, test_labels]).astype(np.int8)
np.savez_compressed('mnist.npz', X=X, y=y)
```

### Verified contents

```
X : (70000, 784) uint8, values 0..255
y : (70000,)     int8,  classes 0..9
label counts : [6903, 7877, 6990, 7141, 6824, 6313, 6876, 7293, 6825, 6958]
X[0] renders as a "5" -> matches the canonical first MNIST training label
```

Load with:

```python
d = np.load('data/mnist.npz'); X, y = d['X'], d['y']
```

---

## 3. Background models challenge — `Video_008.avi`

README source: <http://backgroundmodelschallenge.eu/> (bmc_real.zip)

`https://backgroundmodelschallenge.eu/` is alive. The landing page links the full
`data/bmc_real.zip` (**470,973,149 bytes / 449 MB**) but also **per-video archives**, so only the
single video the task needs was fetched — 10 MB instead of 449 MB:

```bash
curl -L -O "https://backgroundmodelschallenge.eu/data/real/Video_008.zip"   # 10,562,597 bytes
unzip -j Video_008.zip "Video_008/Video_008.avi" -d data/
```

The archive also contains `Video_008.xml` (ground-truth metadata) and 56 hand-labelled
`Img_*.bmp` / `Mask_*.bmp` ground-truth frame pairs. These are **not** needed for task 5
(which only reconstructs the background via low-rank SVD) and were not copied into `data/`.

This is the genuine original `Video_008.avi` — **no substitution was made**.

### Verified contents (`cv2.VideoCapture`)

```
opened            : True
resolution        : 320 x 240
fps               : 10.0
frames (decoded)  : 792     (header reports 793; the last frame does not decode)
duration          : 79.2 s
codec             : FMP4, frames come back as (240, 320, 3) uint8 BGR
```

For task 5 the grayscale video matrix is `76800 x 792` (pixels x frames) — small enough for a
dense SVD, and it is a fixed-camera street scene, so a rank-1/rank-few reconstruction recovers
the background cleanly.

---

## 4. Face expression recognition dataset — `fer2013.npz`  (Chapter VI bonus)

README source: <https://www.kaggle.com/datasets/jonathanoheix/face-expression-recognition-dataset>

That Kaggle dataset is **FER-2013** repackaged as folders of 48x48 grayscale images per emotion.
The underlying `fer2013.csv` was taken from a HuggingFace mirror:

```bash
curl -L -o fer2013.csv.zip \
  "https://huggingface.co/datasets/chitradrishti/fer2013/resolve/main/fer2013.csv.zip"
unzip fer2013.csv.zip     # -> fer2013.csv, 301,072,766 bytes
```

The CSV (`emotion, pixels, Usage`) was decoded into a compact array archive rather than ~36k
individual image files, which keeps the repo small and loads far faster for the bonus task:

```python
df = pd.read_csv('fer2013.csv')
X  = np.stack([np.array(s.split(), dtype=np.uint8).reshape(48, 48) for s in df['pixels']])
y  = df['emotion'].to_numpy().astype(np.int8)
split = np.where(df['Usage'] == 'Training', 'train', 'validation')
np.savez_compressed('fer2013.npz', X=X, y=y, split=split,
                    usage=df['Usage'].to_numpy().astype('U12'),
                    label_names=np.array(['angry','disgust','fear','happy','sad','surprise','neutral']))
```

### Verified contents

```
X           : (35887, 48, 48) uint8, values 0..255
y           : (35887,)        int8
label_names : ['angry','disgust','fear','happy','sad','surprise','neutral']   (canonical FER-2013 order)
per class   : angry 4953, disgust 547, fear 5121, happy 8989, sad 6077, surprise 4002, neutral 6198
split       : train 28709, validation 7178
usage       : Training 28709, PublicTest 3589, PrivateTest 3589
```

All counts match the canonical FER-2013 statistics exactly (35,887 images total).
`happy` = 8,989 and `sad` = 6,077 are the two classes the bonus task needs.

Load with:

```python
d = np.load('data/fer2013.npz')
X, y, names = d['X'], d['y'], d['label_names']
happy = X[y == 3]   # smiley faces
sad   = X[y == 4]   # sad faces
```

**Difference vs. the Kaggle repackaging:** `jonathanoheix` splits the same 35,887 images as
28,821 train / 7,066 validation, i.e. a slightly reshuffled split. This archive keeps the
*original* FER-2013 split (`Training` -> train, `PublicTest`+`PrivateTest` -> validation),
28,709 / 7,178. The images themselves are identical. If the exact folder layout is ever needed
it can be regenerated:

```python
import numpy as np, imageio.v3 as iio, pathlib
d = np.load('data/fer2013.npz')
names = d['label_names']
for i, (img, lab, sp) in enumerate(zip(d['X'], d['y'], d['split'])):
    p = pathlib.Path('data/images') / sp / names[lab]
    p.mkdir(parents=True, exist_ok=True)
    iio.imwrite(p / f'{i:05d}.png', img)
```

---

## 5. Task 4 images — `gray_china.png`, `gray_flower.png`, `gray_hopper.png`

**Nothing was downloaded for task 4.** It only says *"select 3 random grayscale images"* and names
no dataset, so the three images are taken from sample photos **bundled with libraries already in
this venv** — which is what keeps `04_image_compression.ipynb` fully offline and reproducible:

| file | origin | character |
|---|---|---|
| `gray_flower.png` (427x640) | `sklearn.datasets.load_sample_image("flower.jpg")` | smooth, shallow depth of field |
| `gray_hopper.png` (600x512) | `matplotlib.cbook.get_sample_data("grace_hopper.jpg")` | portrait, strong edges |
| `gray_china.png` (427x640) | `sklearn.datasets.load_sample_image("china.jpg")` | heavily textured, high-frequency |

The three PNGs are **produced by the notebook itself**, not fetched: `04_image_compression.ipynb`
loads each bundled RGB photo, converts it to a single grayscale channel with the BT.601 luma
weights and writes the result to `data/` so a reviewer can inspect the exact input matrices.

```python
# 04_image_compression.ipynb, cell 3
gray = cv2.cvtColor(np.asarray(rgb, dtype=np.uint8), cv2.COLOR_RGB2GRAY)   # Y = 0.299R + 0.587G + 0.114B
cv2.imwrite(f"data/gray_{name}.png", gray)
```

They are therefore regenerated (bit-for-bit identical) on every run of that notebook and can be
deleted at any time. Other offline options that were considered and not used: frames of
`data/Video_008.avi`, and MNIST digits from `data/mnist.npz` (only 28x28 — too small to show an
interesting singular-value spectrum; a natural image of ~512x512 or larger is much more
informative).

---

## Repository size note

`data/` totals **~190 MB**. `.gitattributes` already routes `*.csv` and `*.avi` through Git LFS,
but **`*.npz` is not tracked by LFS**, so `mnist.npz` (11 MB) and especially `fer2013.npz`
(75 MB) would be committed as raw git blobs. Consider either adding
`*.npz filter=lfs diff=lfs merge=lfs -text` to `.gitattributes`, or excluding `data/` from the
repo entirely and relying on this file to reproduce it. This was left as-is — it is a repo
policy decision.

## Note on the two files that are not in git

`Books.csv` (73.3 MB) and `fer2013.npz` (78.3 MB) exceed the school GitLab's
per-object limit — pushing them returns HTTP 413 — so they are gitignored.
Re-create them with the download commands documented in the sections above:
`Books.csv` is only used by `02_sparse_features.ipynb` to label SVD components
with book titles, and `fer2013.npz` is only used by the bonus notebook
`06_bonus_faces.ipynb`. Every other notebook runs from the files that are in
the repository.
