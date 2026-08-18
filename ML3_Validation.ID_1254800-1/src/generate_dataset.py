"""
Synthetic dataset generator that mimics the Kaggle
"Two Sigma Connect: Rental Listing Inquiries" dataset (train.json).

The real competition data requires Kaggle authentication to download, so for a
fully self-contained and reproducible project we generate a realistic stand-in
that has the SAME schema and the SAME statistical structure the task relies on:

  * `created`        -> timestamps spread over several months (out-of-time / TimeSeriesSplit)
  * `features`       -> a list of amenity strings (Elevator, Doorman, ...)  to be one-hot encoded
  * `manager_id`     -> grouping key (Group K-Fold) -- a manager owns many listings
  * `interest_level` -> low / medium / high          (stratification target)
  * `price`          -> regression target (linear in the engineered features + noise)
  * bedrooms, bathrooms, latitude, longitude, listing_id, building_id, ...

Output: datasets/train.json  (records orientation, identical to Kaggle's file)
"""

import json
import os

import numpy as np

RNG = np.random.default_rng(42)

# ---------------------------------------------------------------- amenities
# The 20 features the task explicitly asks to engineer (plus a few extra so
# the raw `features` column is noisy and realistic).
TARGET_FEATURES = [
    "Elevator", "HardwoodFloors", "CatsAllowed", "DogsAllowed", "Doorman",
    "Dishwasher", "NoFee", "LaundryinBuilding", "FitnessCenter", "Pre-War",
    "LaundryinUnit", "RoofDeck", "OutdoorSpace", "DiningRoom",
    "HighSpeedInternet", "Balcony", "SwimmingPool", "LaundryInBuilding",
    "NewConstruction", "Terrace",
]
EXTRA_FEATURES = ["Garage", "Storage", "Garden", "Loft", "Duplex", "Furnished"]

# How strongly each engineered amenity pushes the monthly price (USD).
# These weights are the "ground truth" the Lasso / ElasticNet models try to
# recover, which makes feature-selection results interpretable.
FEATURE_PRICE_WEIGHT = {
    "Elevator": 180, "HardwoodFloors": 90, "CatsAllowed": 20, "DogsAllowed": 25,
    "Doorman": 600, "Dishwasher": 120, "NoFee": -150, "LaundryinBuilding": 80,
    "FitnessCenter": 350, "Pre-War": 60, "LaundryinUnit": 220, "RoofDeck": 300,
    "OutdoorSpace": 140, "DiningRoom": 110, "HighSpeedInternet": 40,
    "Balcony": 250, "SwimmingPool": 500, "LaundryInBuilding": 80,
    "NewConstruction": 280, "Terrace": 320,
    # extras contribute almost no signal -> good "noise" columns for selection
    "Garage": 30, "Storage": 10, "Garden": 15, "Loft": 12, "Duplex": 8,
    "Furnished": 200,
}

ALL_FEATURES = TARGET_FEATURES + EXTRA_FEATURES


def _features_to_strings(active):
    """Return raw feature strings the way Kaggle stores them (mixed casing /
    spacing), so the notebook has to clean them -- mirrors real data."""
    raw_map = {
        "HardwoodFloors": "Hardwood Floors", "CatsAllowed": "Cats Allowed",
        "DogsAllowed": "Dogs Allowed", "NoFee": "No Fee",
        "LaundryinBuilding": "Laundry in Building", "FitnessCenter": "Fitness Center",
        "Pre-War": "Pre-War", "LaundryinUnit": "Laundry in Unit",
        "RoofDeck": "Roof Deck", "OutdoorSpace": "Outdoor Space",
        "DiningRoom": "Dining Room", "HighSpeedInternet": "High Speed Internet",
        "SwimmingPool": "Swimming Pool", "LaundryInBuilding": "Laundry In Building",
        "NewConstruction": "New Construction",
    }
    return [raw_map.get(f, f) for f in active]


def generate(n=10000):
    n_managers = 380              # each manager owns ~26 listings on average
    n_buildings = 1500
    managers = [f"m{ i:04d}" for i in range(n_managers)]
    buildings = [f"b{i:05d}" for i in range(n_buildings)]
    # skew manager popularity so groups have very different sizes (realistic)
    manager_p = RNG.dirichlet(np.ones(n_managers) * 0.4)

    records = {}
    base_day = 0
    for i in range(n):
        bedrooms = int(RNG.integers(0, 5))
        bathrooms = float(RNG.choice([1, 1, 1, 1.5, 2, 2, 2.5, 3],))

        # pick amenities; more bedrooms -> slightly more amenities
        k = int(np.clip(RNG.poisson(4 + bedrooms * 0.3), 0, len(ALL_FEATURES)))
        active = list(RNG.choice(ALL_FEATURES, size=k, replace=False)) if k else []

        # ---- price = linear function of bedrooms/baths + amenities + noise ----
        price = (
            1500
            + bedrooms * 850
            + bathrooms * 400
            + sum(FEATURE_PRICE_WEIGHT[f] for f in active)
            + RNG.normal(0, 350)
        )
        price = float(max(500, round(price)))

        # interest_level: cheaper-than-expected listings attract more interest
        expected = 1500 + bedrooms * 850 + bathrooms * 400
        ratio = price / expected
        if ratio < 0.95:
            interest = RNG.choice(["high", "medium", "low"], p=[0.55, 0.30, 0.15])
        elif ratio < 1.15:
            interest = RNG.choice(["high", "medium", "low"], p=[0.20, 0.45, 0.35])
        else:
            interest = RNG.choice(["high", "medium", "low"], p=[0.07, 0.28, 0.65])

        # created timestamp: spread listings across ~6 months, in order
        base_day += RNG.exponential(0.018)           # ~ chronological drift
        ts_day = int(base_day)
        hour = int(RNG.integers(0, 24)); minute = int(RNG.integers(0, 60))
        month = 4 + ts_day // 30
        day = 1 + ts_day % 28
        created = f"2016-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"

        lat = float(40.75 + RNG.normal(0, 0.03))
        lon = float(-73.97 + RNG.normal(0, 0.03))

        mgr = str(RNG.choice(managers, p=manager_p))
        rec_id = str(i)
        records.setdefault("bathrooms", {})[rec_id] = bathrooms
        records.setdefault("bedrooms", {})[rec_id] = bedrooms
        records.setdefault("building_id", {})[rec_id] = str(RNG.choice(buildings))
        records.setdefault("created", {})[rec_id] = created
        records.setdefault("description", {})[rec_id] = ""
        records.setdefault("display_address", {})[rec_id] = f"{int(RNG.integers(1,300))} Main St"
        records.setdefault("features", {})[rec_id] = _features_to_strings(active)
        records.setdefault("latitude", {})[rec_id] = lat
        records.setdefault("listing_id", {})[rec_id] = 7000000 + i
        records.setdefault("longitude", {})[rec_id] = lon
        records.setdefault("manager_id", {})[rec_id] = mgr
        records.setdefault("photos", {})[rec_id] = []
        records.setdefault("price", {})[rec_id] = price
        records.setdefault("street_address", {})[rec_id] = f"{int(RNG.integers(1,300))} Main St"
        records.setdefault("interest_level", {})[rec_id] = interest

    return records


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(here, "datasets")
    os.makedirs(out_dir, exist_ok=True)
    data = generate(10000)
    out_path = os.path.join(out_dir, "train.json")
    with open(out_path, "w") as f:
        json.dump(data, f)
    print(f"Wrote {out_path}: {len(data['price'])} listings, "
          f"{len(data)} columns")
