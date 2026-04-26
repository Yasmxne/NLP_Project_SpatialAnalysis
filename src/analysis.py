from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import re
import ast
import unicodedata


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


def to_list(x):
    if isinstance(x, list):
        return x

    if pd.isna(x):
        return []

    try:
        return ast.literal_eval(x)
    except Exception:
        return []


def normalize_text(x):
    if pd.isna(x):
        return ""

    x = str(x).lower().strip()
    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    x = re.sub(r"[^a-z0-9\s-]", " ", x)
    x = re.sub(r"\s+", " ", x)

    return x.strip()


def extract_address_field(geo, keys):
    address = geo.raw.get("address", {})

    for key in keys:
        if key in address:
            return address[key]

    return None


def classify_contextual_marker(location):
    """
    Classification des mots qui ne sont pas des lieux géographiques,
    mais indiquent quand même une échelle territoriale.
    """

    loc = normalize_text(location)

    local_markers = {
        "circonscription",
        "canton",
        "commune",
        "municipalite",
        "municipal",
        "maire",
        "mairie",
        "conseiller general",
        "conseil general",
        "departement",
        "departemental",
        "departementale",
        "arrondissement"
    }

    national_international_markers = {
    "regional",
    "region",
    "national",
    "nationale",
    "republique",
    "republique francaise",
    "france",
    "europe",
    "europeen",
    "europeenne",
    "union europeenne",
    "etats-unis",
    "etats unis",
    "usa",
    "amerique",
    "amerique du nord",
    "international",
    "internationale",
    "mondial",
    "mondiale",
    "etranger",
    "etrangere"
    }

    if loc in local_markers:
        return "local"

    if loc in national_international_markers:
        return "national_international"

    return "unknown"


def build_locations_reference(df, location_col="locations_clean"):
    """
    Crée une table de référence avec les lieux uniques.
    Chaque lieu est géocodé une seule fois.
    """

    unique_locations = (
        df[location_col]
        .apply(to_list)
        .explode()
        .dropna()
        .astype(str)
        .str.strip()
    )

    unique_locations = unique_locations[unique_locations != ""]
    unique_locations = unique_locations.drop_duplicates().reset_index(drop=True)

    locations_ref = pd.DataFrame({"location": unique_locations})

    geolocator = Nominatim(user_agent="spatial_analysis_project")

    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1,
        max_retries=2,
        error_wait_seconds=2
    )

    def safe_geocode(location):
        """
        France d'abord pour éviter :
        Lorraine -> Kansas.
        Puis monde entier si rien n'est trouvé.
        """

        try:
            result_fr = geocode(
                location,
                language="fr",
                addressdetails=True,
                exactly_one=True,
                timeout=10,
                country_codes="fr"
            )

            if result_fr is not None:
                return result_fr

            result_world = geocode(
                location,
                language="fr",
                addressdetails=True,
                exactly_one=True,
                timeout=10
            )

            return result_world

        except Exception:
            return None

    locations_ref["geo"] = locations_ref["location"].apply(safe_geocode)

    locations_ref["country"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("address", {}).get("country") if g is not None else None
    )

    locations_ref["country_code"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("address", {}).get("country_code") if g is not None else None
    )

    locations_ref["display_name"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("display_name") if g is not None else None
    )

    locations_ref["geo_type"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("type") if g is not None else None
    )

    locations_ref["geo_class"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("class") if g is not None else None
    )

    locations_ref["importance"] = locations_ref["geo"].apply(
        lambda g: g.raw.get("importance") if g is not None else None
    )

    locations_ref["city"] = locations_ref["geo"].apply(
        lambda g: extract_address_field(
            g,
            ["city", "town", "village", "hamlet", "municipality"]
        ) if g is not None else None
    )

    locations_ref["county"] = locations_ref["geo"].apply(
        lambda g: extract_address_field(g, ["county"]) if g is not None else None
    )

    locations_ref["state"] = locations_ref["geo"].apply(
        lambda g: extract_address_field(g, ["state", "region"]) if g is not None else None
    )

    locations_ref["postcode"] = locations_ref["geo"].apply(
        lambda g: extract_address_field(g, ["postcode"]) if g is not None else None
    )

    locations_ref["lat"] = locations_ref["geo"].apply(
        lambda g: g.latitude if g is not None else None
    )

    locations_ref["lon"] = locations_ref["geo"].apply(
        lambda g: g.longitude if g is not None else None
    )

    locations_ref["context_scale"] = locations_ref["location"].apply(classify_contextual_marker)

    return locations_ref.drop(columns=["geo"])


def is_valid_geographic_result(row):
    """
    Validation stricte :
    on garde seulement les lieux correspondant à des champs géographiques structurés.
    """

    if pd.isna(row["country_code"]):
        return False

    location = normalize_text(row["location"])

    if len(location) < 3:
        return False

    geo_class = str(row["geo_class"])
    geo_type = str(row["geo_type"])

    if geo_class not in {"place", "boundary"}:
        return False

    valid_geo_types = {
    "city",
    "town",
    "village",
    "hamlet",
    "municipality",
    "administrative",
    "county",
    "state",
    "region",
    "country",
    "continent"
}

    if geo_type not in valid_geo_types:
        return False

    structured_names = [
        row.get("city"),
        row.get("county"),
        row.get("state"),
        row.get("country")
    ]

    structured_names = [
        normalize_text(x)
        for x in structured_names
        if not pd.isna(x)
    ]

    if location not in structured_names:
        return False

    return True


def classify_location_with_department(location_row, document_department_name, document_department_insee):
    """
    Classification finale :
    - local : lieu lié au département du document ou marqueur local
    - national_international : lieu reconnu hors département ou marqueur supra-local
    - unknown : bruit ou lieu non fiable
    """

    context_scale = location_row.get("context_scale", "unknown")

    if context_scale in {"local", "national_international"}:
        return context_scale

    if not is_valid_geographic_result(location_row):
        return "unknown"

    country_code = location_row["country_code"]

    if country_code != "fr":
        return "national_international"

    doc_dep_name = normalize_text(document_department_name)
    doc_dep_insee = str(document_department_insee).strip() if not pd.isna(document_department_insee) else ""

    loc_name = normalize_text(location_row["location"])
    city = normalize_text(location_row["city"])
    county = normalize_text(location_row["county"])
    state = normalize_text(location_row["state"])
    display_name = normalize_text(location_row["display_name"])
    postcode = str(location_row["postcode"]).strip() if not pd.isna(location_row["postcode"]) else ""

    if doc_dep_name and loc_name == doc_dep_name:
        return "local"

    if doc_dep_name and county == doc_dep_name:
        return "local"

    if doc_dep_name and doc_dep_name in display_name:
        return "local"

    if doc_dep_insee and postcode.startswith(doc_dep_insee):
        return "local"

    if city and city == loc_name:
        return "national_international"

    if state:
        return "national_international"

    return "national_international"


def classify_locations_for_document(row, locations_ref, location_col="locations_clean"):
    locations = to_list(row[location_col])

    if len(locations) == 0:
        return []

    tmp = pd.DataFrame({"location": locations})
    tmp["location"] = tmp["location"].astype(str).str.strip()

    tmp = tmp.merge(
        locations_ref,
        on="location",
        how="left"
    )

    tmp["scale"] = tmp.apply(
        lambda x: classify_location_with_department(
            x,
            document_department_name=row.get("departement-nom"),
            document_department_insee=row.get("departement-insee")
        ),
        axis=1
    )

    return tmp[["location", "scale"]].to_dict("records")


def compute_spatial_ratios(classified_locations):
    if len(classified_locations) == 0:
        return pd.Series({
            "local_ratio": 0,
            "national_international_ratio": 0,
            "unknown_ratio": 1,
            "dominant_scale": "unknown"
        })

    scales = pd.Series([x["scale"] for x in classified_locations])
    counts = scales.value_counts(normalize=True)

    local_ratio = counts.get("local", 0)
    national_international_ratio = counts.get("national_international", 0)
    unknown_ratio = counts.get("unknown", 0)

    valid_scales = scales[scales != "unknown"]

    if len(valid_scales) == 0:
        dominant_scale = "unknown"
    else:
        dominant_scale = valid_scales.value_counts().idxmax()

    return pd.Series({
        "local_ratio": local_ratio,
        "national_international_ratio": national_international_ratio,
        "unknown_ratio": unknown_ratio,
        "dominant_scale": dominant_scale
    })


def add_spatial_ratios(df, location_col="locations_clean"):
    locations_ref = build_locations_reference(df, location_col=location_col)

    df["classified_locations"] = df.apply(
        lambda row: classify_locations_for_document(
            row,
            locations_ref=locations_ref,
            location_col=location_col
        ),
        axis=1
    )

    ratio_cols = df["classified_locations"].apply(compute_spatial_ratios)
    df_final = pd.concat([df, ratio_cols], axis=1)

    return df_final, locations_ref


if __name__ == "__main__":

    input_path = "data/processed/df_ner3.pkl"
    output_path = "data/processed/df_spatial_analysis.pkl"
    locations_ref_path = "data/processed/locations_reference.csv"

    df = pd.read_pickle(input_path)

    df = add_clean_locations(df)

    df_final, locations_ref = add_spatial_ratios(
        df,
        location_col="locations_clean"
    )

    df_final.to_pickle(output_path)
    locations_ref.to_csv(locations_ref_path, index=False)

    print("Spatial analysis completed.")
    print(f"Saved dataframe: {output_path}")
    print(f"Saved locations reference: {locations_ref_path}")