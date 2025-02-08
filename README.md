# RSGPT - Repository Structure and Analysis Tool

RSGPT is an advanced tool designed to assist developers in analyzing and understanding code repositories through AI-powered insights and repository structure analysis. It leverages graph-based architectures and various AI models to provide comprehensive information about repository content.

## 🚀 Features

- Repository content analysis and search capabilities
- Graph-based architecture for flexible processing
- Integration with various AI models for enhanced insights
- Git repository manipulation and analysis tools
- Specialized tools for repository structure generation

## 📋 Prerequisites

- Python 3.x
- `hatch` for environment management
- Git

## 🛠 Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd rsgpt
```

2. Install the required dependencies:
```bash
pip install hatch
hatch shell
```

## 🧑‍💻 CLI Usage

RSGPT can be used through the following commands:

### `rsgpt`

This command starts an interactive session using the RSGPT tool. It allows you to provide inputs interactively to analyze and process repository data.

Usage:
```bash
rsgpt
```
You will be prompted to provide inputs interactively, and the tool will process repository-specific data based on your queries.

### `rsgpt --commit`

This command invokes the Commit Assistant mode of RSGPT. It helps in analyzing repository changes and generating commit messages programmatically.

Usage:
```bash
rsgpt --commit
```
RSGPT will analyze the current repository's changes (e.g., Git diff) and assist in creating a commit message based on the modifications.

## 👤 Author

Damien SIX - [damien@robotsix.net](mailto:damien@robotsix.net)

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.