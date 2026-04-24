from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import re

def count_locations(locations):
    return len(locations)


def add_basic_location_stats(df):
    df = df.copy()
    df["n_locations"] = df["locations"].apply(count_locations)
    return df

def clean_locations_list(locations):
    bad_words = {
        "a", "à", "et", "f", "etat", "état",
        "francais", "français", "française", "françaises",
        "republique", "république", "gouvernement",
        "place", "part", "mesures", "aide"
    }

    articles = ["le", "la", "les", "l'", "de", "du", "des"]

    clean_locs = []

    for loc in locations:
        loc_clean = str(loc).strip()

        loc_clean = loc_clean.replace("\n", " ")

        loc_clean = re.sub(
            r"^(le|la|les|l'|de|du|des)\s+",
            "",
            loc_clean,
            flags=re.IGNORECASE
        )

        loc_lower = loc_clean.lower()

        if len(loc_clean) <= 2:
            continue

        if loc_lower in bad_words:
            continue

        if loc_clean.isdigit():
            continue

        clean_locs.append(loc_clean)

    return clean_locs


def add_clean_locations(df):
    df = df.copy()
    df["locations_clean"] = df["locations"].apply(clean_locations_list)
    df["n_locations_clean"] = df["locations_clean"].apply(len)
    return df


# init géocodeur
geolocator = Nominatim(user_agent="archelec_project")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def geocode_location(loc):
    try:
        location = geocode(loc)
        if location and "country_code" in location.raw["address"]:
            return location.raw["address"]["country_code"]
    except:
        pass
    return None


def build_location_cache(df):
    unique_locations = set()

    for locs in df["locations_clean"]:
        unique_locations.update(locs)

    data = []
    for loc in unique_locations:
        country = geocode_location(loc)
        data.append({"location": loc, "country_code": country})

    df_cache = pd.DataFrame(data)
    df_cache.to_csv("../data/processed/location_cache.csv", index=False)

    return df_cache


def load_location_cache():
    return pd.read_csv("../data/processed/location_cache.csv")


def classify_location(loc, dept, cache_df):
    row = cache_df[cache_df["location"] == loc]

    if row.empty:
        return "other"

    country = row["country_code"].values[0]

    if pd.isna(country):
        return "other"

    if country == "fr":
        if dept.lower() in loc.lower():
            return "local"
        return "national"

    return "international"

def add_location_categories(df, cache_df):
    df = df.copy()

    local_counts = []
    national_counts = []
    international_counts = []
    other_counts = []

    for _, row in df.iterrows():
        categories = [
            classify_location(loc, row["departement-nom"], cache_df)
            for loc in row["locations_clean"]
        ]

        local_counts.append(categories.count("local"))
        national_counts.append(categories.count("national"))
        international_counts.append(categories.count("international"))
        other_counts.append(categories.count("other"))

    df["local_count"] = local_counts
    df["national_count"] = national_counts
    df["international_count"] = international_counts
    df["other_count"] = other_counts

    df["total"] = (
        df["local_count"] + df["national_count"] + df["international_count"]
    )

    df["local_ratio"] = df["local_count"] / df["total"]
    df["national_ratio"] = df["national_count"] / df["total"]
    df["international_ratio"] = df["international_count"] / df["total"]

    df[["local_ratio", "national_ratio", "international_ratio"]] = (
        df[["local_ratio", "national_ratio", "international_ratio"]].fillna(0)
    )

    return df