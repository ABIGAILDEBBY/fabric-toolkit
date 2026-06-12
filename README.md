<div align="center">

<img src="docs/fabric-logo.svg" alt="Microsoft Fabric" width="80" height="80" />

# fabric-toolkit

### A collection of Python utilities for Microsoft Fabric

Manage schedules, audit pipelines, set up Teams alerting, check data freshness,
and more. All from the command line, without writing a single line of DAX or clicking through portals.

<br/>

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Microsoft Fabric](https://img.shields.io/badge/Microsoft%20Fabric-compatible-00B0F0?style=flat-square&logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/fabric/)
[![Power BI](https://img.shields.io/badge/Power%20BI-compatible-F2C811?style=flat-square&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-a855f7?style=flat-square)](CONTRIBUTING.md)

<br/>

[**Tools**](#tools) &nbsp;·&nbsp; [**Quick Start**](#quick-start) &nbsp;·&nbsp; [**Setup Guide**](#setup-guide) &nbsp;·&nbsp; [**Alerting System**](#teams-alerting-system) &nbsp;·&nbsp; [**Contributing**](#contributing)

</div>

---

## Overview

`fabric-toolkit` is an open-source Python toolkit that gives Microsoft Fabric engineers and administrators a set of ready-to-run command-line tools for everyday workspace management tasks.

No hardcoded workspace IDs. No dependencies between tools. Authenticate once and work interactively. Every tool discovers your workspaces at runtime and walks you through what it needs.

```
✔  Audit every schedule in a workspace and export to Excel
✔  Bulk-disable schedules by item type: pipelines, dataflows, notebooks, and more
✔  Find legacy duplicate pipelines and flag them for cleanup
✔  Check whether your data is actually fresh or quietly stale
✔  Scan for Teams-wired alert activities across all pipelines
✔  Classify every pipeline by alerting readiness before touching production
✔  Wire up a full Teams adaptive card alerting system in minutes
```

---

## Tools

| Tool | What it does |
|---|---|
| [`schedule_extractor.py`](tools/schedule_extractor.py) | Scans every item in a workspace and exports a full schedule inventory to Excel: pipelines, semantic models, dataflows, notebooks, and Spark jobs |
| [`schedule_disabler.py`](tools/schedule_disabler.py) | Bulk-disables active schedules. Choose item types, discover live or load from a file, confirm before anything changes |
| [`legacy_pipeline_audit.py`](tools/legacy_pipeline_audit.py) | Finds `_LEGACY` duplicate pipelines, checks if they are still scheduled or running, and flags which ones are safe to clean up |
| [`data_freshness_check.py`](tools/data_freshness_check.py) | Identifies semantic models and lakehouses with stale data. Pinpoints whether the issue is in the refresh schedule or the source tables |
| [`pipeline_watermark_check.py`](tools/pipeline_watermark_check.py) | Inspects pipelines for watermark and date parameters to distinguish incremental vs full loads |
| [`audit_log_check.py`](tools/audit_log_check.py) | Pulls the Fabric audit log to show who created, modified, ran, or deleted pipeline items, with date filtering |
| [`teams_alert_scanner.py`](tools/teams_alert_scanner.py) | Scans all pipelines to surface every existing Teams/webhook notification activity and what notebook or URL it calls |
| [`alerting_readiness_check.py`](tools/alerting_readiness_check.py) | Classifies every pipeline into **Safe Now**, **Review First**, or **Do Not Touch** based on complexity, existing alerting, and recent run history |

---

## Teams Alerting System

The toolkit includes a complete **pipeline failure and success alerting system** that posts Adaptive Cards to a Microsoft Teams channel via Power Automate.

<div align="center">

| Failure alert | Success alert |
|:---:|:---:|
| Red header, exact error message, failed activity name | Green header, pipeline name, run ID, timestamp |

</div>

The system has three parts:

1. **`nb_send_pipeline_alert`** — a Fabric notebook that builds and posts the Adaptive Card. Parameters are injected by the pipeline at runtime.
2. **Failure branch wiring** — each pipeline activity gets its own alert node on failure, passing the exact `@activity('name').error.message` expression.
3. **Success branch wiring** — a separate alert node fires on the success path with `PipelineStatus = Success`.

See [`alerting/README.md`](alerting/README.md) for the full setup walkthrough.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/ABIGAILDEBBY/fabric-toolkit.git
cd fabric-toolkit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the config template and fill in your Client ID
cp config.example.py config.py
# Edit config.py and paste your Azure App Registration Client ID

# 4. Run any tool
python tools/schedule_extractor.py
```

On first run a browser window opens for Microsoft sign-in. Your token is cached locally and subsequent runs skip the login prompt.

---

## Setup Guide

### Step 1 — Register an Azure App (5 minutes, one-time)

You need an Azure App Registration so the toolkit can authenticate with Microsoft APIs on your behalf. This is free and requires only a Microsoft account.

1. Go to [portal.azure.com](https://portal.azure.com) and sign in
2. Search for **App registrations** and click **New registration**
3. Fill in:
   - **Name:** `fabric-toolkit` (or anything you like)
   - **Supported account types:** _Accounts in any organizational directory_
4. Click **Register**
5. On the app overview page, copy the **Application (client) ID**

   > This is the value that goes in `config.py`. It looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

6. Go to **API permissions**, click **Add a permission**, and add the following:

   | API | Permission | Type |
   |---|---|---|
   | Microsoft Fabric API | `user_impersonation` | Delegated |
   | Power BI Service | `Dataset.ReadWrite.All` | Delegated |
   | Power BI Service | `Workspace.Read.All` | Delegated |
   | Power BI Service | `Pipeline.ReadWrite.All` | Delegated |

7. Click **Grant admin consent** if you have admin rights, or ask your IT admin to approve

For a detailed walkthrough with screenshots, see [SETUP.md](SETUP.md).

### Step 2 — Configure the toolkit

```python
# config.py
CLIENT_ID = "paste-your-application-client-id-here"
```

`config.py` is listed in `.gitignore` and will never be accidentally committed.

### Step 3 — Run

Every tool is self-contained. Run any script directly:

```bash
python tools/schedule_extractor.py
python tools/legacy_pipeline_audit.py
python tools/alerting_readiness_check.py
```

Each tool will:
1. Authenticate using your Client ID and your Microsoft account
2. Fetch and list the workspaces you have access to
3. Ask which workspace to target
4. Walk you through any remaining options interactively

---

## Requirements

```
Python 3.8+
msal
requests
openpyxl
rich
```

All packages are installed automatically on first run if not already present.

---

## Compatibility

| Platform | Supported |
|---|---|
| Microsoft Fabric (all regions) | Yes |
| Power BI Service | Yes |
| Fabric Free / Trial capacity | Yes (read operations only) |
| Sovereign clouds (GCC, GCC-H) | Untested |

---

## Contributing

Contributions are welcome. If you have built a useful Fabric utility script and want to add it to the toolkit, open a pull request.

Please make sure any contribution:
- Has no hardcoded workspace IDs, tenant IDs, or client-specific values
- Works interactively (prompts for workspace, item type, etc.)
- Uses the shared auth pattern from `config.py`
- Includes a one-line description update in this README

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

---

## License

MIT. See [LICENSE](LICENSE) for details.

---

<div align="center">

Built with the [Microsoft Fabric REST API](https://learn.microsoft.com/en-us/rest/api/fabric/articles/) &nbsp;·&nbsp; [Microsoft Fabric Icons](https://learn.microsoft.com/en-us/fabric/fundamentals/icons)

</div>
