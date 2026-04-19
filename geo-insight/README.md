# Geo-Insight: GapFinder Assistant - Databricks App

This is a live, publicly accessible Gradio app deployed on Databricks Apps.

## Prerequisites

1. Your quattroformaggi source code needs to be in the `../src/quattroformaggi/` directory relative to this app
2. The `datathon-scope/ANTHROPIC_API_KEY` secret must be configured in your workspace
3. Access to the `unocha.default.master_table` Unity Catalog table

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