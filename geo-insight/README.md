# Geo-Insight: GapFinder Assistant - Databricks App

This folder contains a live demo of the Geo-Insight app, hosted using [Databricks Apps](https://www.databricks.com/product/databricks-apps).

## Prerequisites

- An active [Databricks](https://www.databricks.com/) workspace
- [Claude API Key](https://platform.claude.com/settings/workspaces/default/keys)

## Setup

### 1. Configure Databricks Secrets

The app reads credentials from a Databricks secret scope named `datathon-scope`. Create the scope and add the required secrets:

```bash
databricks secrets create-scope datathon-scope
databricks secrets put-secret datathon-scope ANTHROPIC_API_KEY --string-value <your-claude-api-key>
databricks secrets put-secret datathon-scope DATABRICKS_TOKEN --string-value <your-databricks-token>
```

### 2. Update the Warehouse HTTP Path

In `src/app.yaml`, set `DATABRICKS_HTTP_PATH` to the HTTP path of your SQL warehouse. You can find it in the Databricks workspace under **SQL Warehouses → your warehouse → Connection details**.

### 3. Deploy the App

1. Go to the Databricks Apps dashboard and click **Create app**
2. Choose **Custom app** and give it a name
3. Under **Source**, point the app at this repository or upload the contents of the `src/` folder
4. Click **Deploy** — Databricks Apps will install dependencies from `requirements.txt` automatically
5. `DATABRICKS_HOST` is injected by the platform; all other secrets are pulled from `datathon-scope`

## App Configuration

| File | Purpose |
|---|---|
| `src/app.yaml` | Runtime command, secret bindings, and environment variables |
| `src/app.py` | Main Gradio application and AI pipeline |
| `src/requirements.txt` | Python dependencies (`gradio` and `pandas` are pre-installed) |

### Environment Variables

| Variable | Source | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | `datathon-scope` secret | Claude API key for query interpretation and report generation |
| `DATABRICKS_HOST` | Auto-injected | Workspace hostname |
| `DATABRICKS_TOKEN` | `datathon-scope` secret | Token for Databricks SQL access |
| `DATABRICKS_HTTP_PATH` | `app.yaml` (hardcoded) | HTTP path of the target SQL warehouse |

## App URL

Once deployed, your app will be accessible at the URL shown in the App overview.
