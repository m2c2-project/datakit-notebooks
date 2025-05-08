# datakit-notebooks  
📓 Companion notebooks for the `datakit` Python package  
🌐 Documentation: https://m2c2-project.github.io/datakit/site/index.html

---

## Overview  
The `datakit-notebooks` repository provides a collection of example Jupyter notebooks that demonstrate the usage, capabilities, and best practices for working with the `datakit` Python package. The notebooks are intended to serve as interactive guides for researchers, data scientists, and developers using the M2C2 Platform, which supports mobile cognitive data collection and analysis.

The notebooks cover workflows such as:

- Loading and exploring data from mobile cognitive tasks  
- Data cleaning and quality assurance  
- Scoring and summarizing participant performance  
- Visualizing cognitive and behavioral trends  
- Exporting data for statistical analysis  


## 🧠 L.A.S.S.I.E. Pipeline Summary

| Step | Method           | Purpose                                                                 |
|------|------------------|-------------------------------------------------------------------------|
| L    | `load()`         | Load raw data from a supported source (e.g., MongoDB, UAS, MetricWire). |
| A    | `assure()`       | Validate that required columns exist before processing.                 |
| S    | `score()`        | Apply scoring logic based on predefined or custom rules.                |
| S    | `summarize()`    | Aggregate scored data by participant, session, or custom groups.        |
| I    | `inspect()`      | Visualize distributions or pairwise plots for quality checks.           |
| E    | `export()`       | Save scored and summarized data to tidy files and optionally metadata.  |

---


## 📦 Supported Sources

| Source Type   | Loader Class          | Key Arguments                            | Notes                                 |
|---------------|------------------------|-------------------------------------------|----------------------------------------|
| `mongodb`     | `MongoDBImporter`      | `source_path` (JSON)                      | Expects flat or nested JSON documents. |
| `uas`         | `UASImporter`          | `source_path` (URL)                       | Parses newline-delimited JSON.         |
| `metricwire`  | `MetricWireImporter`   | `source_path` (glob pattern or default)   | Processes JSON files from unzipped export. |
| `multicsv`    | `MultiCSVImporter`     | `source_map` (dict of CSV paths)          | Each activity type is its own file.    |


---

## About the M2C2 DataKit 📦  

`datakit` is a core Python package within the M2C2 Platform, designed to streamline:

- Data ingestion from various study formats  
- Validation and integrity checks  
- Automated scoring for supported tasks  
- Summarization and visual reporting tools  

To learn more, visit the full [package documentation](https://m2c2-project.github.io/datakit/site/index.html).

---

## Repository Structure

```bash
datakit-notebooks/
│
├── notebooks/
│   ├── 01-loading-data.ipynb
│   ├── 02-cleaning-data.ipynb
│   ├── 03-visualizations.ipynb
│   └── ...
│
├── data/               # Sample datasets (if applicable)
├── requirements.txt    # Optional, for reproducible environments
└── README.md
```

---

## Installation

```bash
git clone https://github.com/m2c2-project/datakit-notebooks.git
cd datakit-notebooks
```

### Install dependencies  
*(It is recommended to use a virtual environment.)*

```bash
pip install -r requirements.txt
```

### Launch the notebooks

```bash
jupyter lab
```

---

## Contributing  

If you have ideas for new notebooks or examples, feel free to open an issue or submit a pull request. We're excited to collaborate and expand the utility of the DataKit!
