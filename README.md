# Archelec Spatial Analysis

This project analyses the spatial orientation of political manifestos from the Archelec corpus.  
The main goal is to study whether candidates' discourses are mainly rooted in their local territory, or whether they refer more to national and international issues.

## Objective

The project uses NLP techniques to extract location mentions from political manifestos and classify them into spatial categories:

- `local`: references linked to the candidate's department
- `national_international`: references outside the local department or broader political spaces
- `unknown`: noisy, ambiguous, or unreliable extracted mentions

The final output is a set of document-level spatial indicators such as:

- `local_ratio`
- `national_international_ratio`
- `unknown_ratio`
- `dominant_scale`

## Dataset

The project is based on the Archelec corpus, a collection of electoral manifestos from candidates in elections of the French Fifth Republic.

The raw OCR texts are not included in this repository because of their size. They must be downloaded separately.

## Project structure

```text
NLP_Project_SpatialAnalysis/
│
├── data/
│   ├── raw/                  # raw OCR data, not tracked by git
│   └── processed/            # processed datasets
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_ner_extraction.ipynb
│   └── 03_analysis_visualization.ipynb
│
├── outputs/                  # generated figures or outputs
│
├── report/                   # final report
│
├── src/
│   ├── preprocess.py         # loading, merging and cleaning text data
│   ├── ner.py                # location extraction with spaCy NER
│   └── analysis.py           # geocoding, classification and spatial ratios
│
├── requirements.txt
└── README.md
```

## Pipeline

The project follows this pipeline:

1. Load metadata and OCR texts
2. Merge texts with metadata using document identifiers
3. Apply light text cleaning
4. Extract location mentions with spaCy NER
5. Clean extracted locations
6. Geocode unique location mentions with Nominatim
7. Classify mentions as local, national/international, or unknown
8. Compute spatial ratios for each document
9. Analyse the results through descriptive visualizations

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows with Git Bash:

```bash
source .venv/Scripts/activate
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

Install the spaCy French model:

```bash
python -m spacy download fr_core_news_md
```

## Data setup

The raw data is not included in this repository.

To reproduce the experiments, download the OCR transcriptions inside the `data/raw` folder:

```bash
cd data/raw
git clone https://gitlab.teklia.com/ckermorvant/arkindex_archelec.git
```

After this step, the preprocessing scripts and notebooks can be run normally.

## How to run

From the root of the project, run the notebooks in this order:

```text
01_data_exploration.ipynb
02_ner_extraction.ipynb
03_analysis_visualization.ipynb
```

The main scripts are located in the `src/` folder:

```bash
python src/analysis.py
```

This generates the spatial analysis outputs in:

```text
data/processed/
```

including the final dataframe and the location reference table.

## Notes

The full pipeline can take time to run because the geocoding step is slow.  
For the report, the analysis was run on a sample of 500 texts in order to keep execution time reasonable.