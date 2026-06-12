<div align="center">

# fabric-toolkit

Python utilities for Microsoft Fabric. Schedule management, pipeline auditing, Teams alerting, and more from the terminal.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Microsoft Fabric](https://img.shields.io/badge/Microsoft%20Fabric-compatible-00B0F0?style=flat-square&logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/fabric/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-a855f7?style=flat-square)](CONTRIBUTING.md)

</div>

---

A small set of command-line tools for day-to-day Microsoft Fabric workspace management. Each tool connects to your workspace at runtime, asks what it needs, and gets out of your way. No hardcoded IDs, no portal clicking, no dependencies between scripts.

## Tools

| Script | What it does |
|---|---|
| `schedule_extractor.py` | Pulls a full schedule inventory across pipelines, semantic models, dataflows, notebooks, and Spark jobs and writes it to Excel |
| `schedule_disabler.py` | Disables active schedules in bulk. Works from a live API scan or a file you provide. Confirms before touching anything. |
| `legacy_pipeline_audit.py` | Finds `_LEGACY` duplicate pipelines, checks if they are still running or scheduled, and flags which are safe to remove |
| `data_freshness_check.py` | Identifies stale semantic models and lakehouses and narrows down whether the problem is the refresh schedule or the source |
| `pipeline_watermark_check.py` | Inspects pipeline parameters for watermarks and date ranges to tell incremental loads apart from full loads |
| `audit_log_check.py` | Queries the Fabric activity log to show who created, modified, or deleted pipeline items over a date range |
| `teams_alert_scanner.py` | Maps every existing Teams or webhook notification across all pipelines, including the notebook or URL being called |
| `alerting_readiness_check.py` | Classifies each pipeline as Safe Now, Review First, or Do Not Touch before you start adding alert wiring to production |

## Getting started

```bash
# Clone and install
git clone https://github.com/ABIGAILDEBBY/fabric-toolkit.git
cd fabric-toolkit
pip install -r requirements.txt

# Add your Azure App Client ID
cp config.example.py config.py
# Edit config.py and paste your CLIENT_ID

# Run any tool
python tools/schedule_extractor.py
```

On first run, a browser window opens for Microsoft sign-in. The token is cached locally so subsequent runs skip that step.

You need an Azure App Registration with delegated permissions for Microsoft Fabric and Power BI. See [SETUP.md](SETUP.md) for the full walkthrough, including which permissions to add and how to share a single app registration across a team.

## Teams alerting system

The toolkit includes a complete pipeline alerting setup that posts Adaptive Cards to a Microsoft Teams channel through Power Automate.

When a pipeline activity fails, it fires a notebook with the exact error message from `@activity('name').error.message` and sends a red card to Teams. On success, a green card goes out with the pipeline name, run ID, and timestamp. Both use the same notebook, driven by parameters injected at runtime.

Full setup walkthrough in `alerting/README.md` (coming in a future PR).

## Requirements

```txt
Python 3.8+
msal
requests
openpyxl
rich
```

## Contributing

Contributions are welcome. If you have a Fabric utility script that might be useful to others, open a PR. The main rule is that tools must have no hardcoded IDs and must work interactively on any workspace.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on the branch and commit conventions.

---

<div align="center">
<sub>MIT License - Built using the <a href="https://learn.microsoft.com/en-us/rest/api/fabric/articles/">Microsoft Fabric REST API</a></sub>
</div>
