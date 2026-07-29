# LASSIE Streamlit App

A Streamlit interface for the multi-platform LASSIE workflow in the supplied notebook.

## Supported platforms

- MetricWire ZIP exports
- Qualtrics CSV exports
- MongoDB JSON exports
- Multiple task-level CSV files
- M2C2 Static CSV exports
- M2C2 Production Backend API (experimental)

The first required app selection is the source platform. The rest of the form changes based on that choice.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- MetricWire: upload the unzipped export folder after compressing it into one ZIP. The app safely extracts the archive and searches recursively for JSON files.
- Multiple CSVs: upload one CSV per task and specify the activity name associated with each file.
- API credentials are entered at runtime and are not written to disk. You may also set `m2c2api_username` and `m2c2api_password` environment variables.
- Outputs are created in a temporary directory and returned as a downloadable ZIP, so the server does not retain user data after the run.
