# Contributing to fabric-toolkit

Thank you for your interest in contributing. All contributions are welcome: bug fixes, new tools, documentation improvements, and ideas.

## How to contribute

1. **Fork** this repository to your own GitHub account
2. **Clone** your fork locally
   ```bash
   git clone https://github.com/your-username/fabric-toolkit.git
   cd fabric-toolkit
   ```
3. **Create a branch** for your change
   ```bash
   git checkout -b feat/your-feature-name
   ```
4. **Make your changes.** See guidelines below.
5. **Commit** with a clear message
   ```bash
   git commit -m "feat: add workspace inventory tool"
   ```
6. **Push** to your fork
   ```bash
   git push origin feat/your-feature-name
   ```
7. **Open a Pull Request** against the `main` branch of this repo

## Guidelines for new tools

- No hardcoded workspace IDs, tenant IDs, client IDs, or item IDs
- No client-specific names, URLs, or connection strings
- The tool must work interactively. Prompt for workspace, item types, and any other required input.
- Authentication must use `config.py` (the shared `CLIENT_ID` pattern)
- No dependency on other toolkit scripts. Each tool is self-contained.
- Add a one-line description of your tool to the tools table in `README.md`

## Commit message format

Use conventional commits:

| Prefix | Use for |
|---|---|
| `feat:` | A new tool or feature |
| `fix:` | A bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change that isn't a fix or feature |
| `chore:` | Maintenance (dependencies, config) |

## Questions

Open an issue if you are unsure whether your idea fits the toolkit before building it.
