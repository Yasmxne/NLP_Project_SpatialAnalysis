import spacy


def load_ner_model(model_name="fr_core_news_md"):
    return spacy.load(model_name)




def add_locations_column(df, text_col="text"):
    nlp = load_ner_model()

    texts = df[text_col].astype(str).tolist()

    locations_list = []

    for doc in nlp.pipe(texts, batch_size=50):
        locs = [ent.text for ent in doc.ents if ent.label_ in ["LOC", "GPE"]]
        locations_list.append(locs)

    df = df.copy()
    df["locations"] = locations_list

    return df