import pandas as pd
from pathlib import Path
import zipfile
import re

def load_metadata(path):
    df = pd.read_csv(path)
    return df


def list_zip_files(folder):
    folder = Path(folder)
    zip_files = list(folder.rglob("*.zip"))
    return zip_files



def load_texts_from_zip(zip_path):
    rows = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for file_name in z.namelist():
            if file_name.endswith(".txt"):
                with z.open(file_name) as f:
                    text = f.read().decode("utf-8", errors="ignore")

                rows.append({
                    "zip_file": Path(zip_path).name,
                    "text_file": file_name,
                    "text": text
                })

    df = pd.DataFrame(rows)
    return df


def load_all_texts(folder):
    zip_files = list_zip_files(folder)
    all_dfs = []

    for zip_path in zip_files:
        df_zip = load_texts_from_zip(zip_path)
        all_dfs.append(df_zip)

    if len(all_dfs) == 0:
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    return df

def extract_id(text_file):
    return text_file.split("/")[-1].replace(".txt", "")


def add_id_to_texts(df_texts):
    df_texts = df_texts.copy()
    df_texts["id"] = df_texts["text_file"].apply(extract_id)
    return df_texts


def merge_metadata_texts(df_meta, df_texts):
    return df_meta.merge(df_texts, on="id", how="inner")

def clean_text(text):
    text = str(text)

    # enlever retours ligne
    text = text.replace("\n", " ")

    # enlever multiples espaces
    text = re.sub(r"\s+", " ", text)

    # enlever caractères bizarres OCR
    text = re.sub(r"[^\w\s\-']", " ", text)

    return text.strip()