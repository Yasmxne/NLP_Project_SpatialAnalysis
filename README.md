# NLP_Project_SpatialAnalysis

# Archelec Spatial Analysis

## Objective
Analyze local vs national discourse using NLP

## Dataset
- Archelec corpus

## Pipeline
1. Data preprocessing
2. NER extraction
3. Location classification
4. Analysis

## How to run
pip install -r requirements.txt

## Data

The raw data is not included in this repository.

To reproduce the experiments, you need to download the OCR transcriptions:

1. Go to the `data/raw` folder:
   ```bash
   cd data/raw
```

Clone the following repository:

```bash
git clone https://gitlab.teklia.com/ckermorvant/arkindex_archelec.git
```

Once this is done, you can run the preprocessing and notebooks normally.