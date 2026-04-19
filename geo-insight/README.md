# Geo-Insight: GapFinder Assistant - Databricks App

This is a live, publicly accessible Gradio app deployed on Databricks Apps.

## Prerequisites

1. Your quattroformaggi source code needs to be in the `../src/quattroformaggi/` directory relative to this app
2. The `datathon-scope/ANTHROPIC_API_KEY` secret must be configured in your workspace
3. Access to the `unocha.default.master_table_final` Unity Catalog table 

# ADD THE FORECAST TABLE HERE

### Table generation

In order to get the tables required for the app, follow these steps:

1. Download appropriate datasets from the following links:
   - https://data.humdata.org/dataset/global-hpc-hno (make sure to add the year column in order to distinguish between records in provided CSV files),
   - https://data.humdata.org/dataset/global-requirements-and-funding-data &ndash; specifically, `fts_requirements_funding_global.csv` and `fts_incoming_funding_global.csv`,
   - https://data.worldbank.org/indicator/SP.POP.TOTL?end=2023&start=2001 &ndash; in this case, the resulting CSV file should be flattened so that it has 3 columns - `Country Code`, `year` and `population`,
   - https://www.acaps.org/en/data (optional) &ndash; contains monthly severity indices for countries requires some pre

2. Create a catalog called `unocha` and ingest the downloaded files as tables. In case of most tables, the CSV file name (or its simplified version) is used as the table name. 

## Directory Structure

```
QuattroFormaggi/
├── src/
│   └── quattroformaggi/
│       ├── BriefingNoteWriter.py
│       ├── QueryInterpreter.py
│       ├── query_to_sql.py
│       └── (other modules)
│   └── prompts/
│       ├── QueryInterpreter.md
│       ├── BriefingNoteWriter.md
│       └── (other prompts)
└── gapfinder-app/
    ├── app.py
    ├── app.yaml
    ├── requirements.txt
    └── README.md (this file)
```

## Deployment Steps

### Option 1: Deploy via Databricks UI

1. Click the app switcher (waffle icon) in the top-left
2. Select **Databricks Apps**
3. Click **+ Create app**
4. Choose **Create from existing files**
5. Navigate to this directory: `/Users/janek.wyrzykowski@gmail.com/QuattroFormaggi/gapfinder-app`
6. Name your app (e.g., "gapfinder-assistant")
7. Click **Create app**
8. Wait 2-3 minutes for deployment
9. Once status shows **Running**, click the URL to access your live app!

### Option 2: Deploy via Databricks CLI

1. Install Databricks CLI:
   ```bash
   pip install databricks-cli
   ```

2. Configure authentication:
   ```bash
   databricks configure
   ```

3. Deploy the app:
   ```bash
   databricks apps deploy gapfinder-assistant \
     --source-code-path /Workspace/Users/janek.wyrzykowski@gmail.com/QuattroFormaggi/gapfinder-app
   ```

4. Check deployment status:
   ```bash
   databricks apps get gapfinder-assistant
   ```

## App Configuration

* **app.yaml**: Defines how the app runs and environment variables
* **app.py**: Main Gradio application code
* **requirements.txt**: Python dependencies (gradio is pre-installed)

## Updating the App

After making code changes:

1. Via UI: Click **Deploy** button on the app overview page
2. Via CLI: Run the same `databricks apps deploy` command

## Troubleshooting

* **App fails to start**: Check the Deployments tab for error details
* **Import errors**: Ensure quattroformaggi source is in the correct relative path
* **API key errors**: Verify the secret is configured: `databricks secrets get-secret datathon-scope ANTHROPIC_API_KEY`
* **Table access errors**: Check Unity Catalog permissions for `unocha.default.master_table`

## App URL

Once deployed, your app will be accessible at:
`https://<workspace-url>/apps/<app-name>`

This URL is publicly accessible (with workspace authentication) and can be shared with your team!