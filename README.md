# AI Assistant Repository

This repository houses a GPT-powered AI assistant designed to integrate smoothly into software development workflows. Leveraging OpenAI’s models, the assistant aids in a variety of development and maintenance tasks such as executing shell commands, searching files, and managing GitHub issues directly through the repository.

## Table of Contents
- [AI Assistant Repository](#ai-assistant-repository)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [General Usage](#general-usage)
    - [GitHub Actions Workflows](#github-actions-workflows)
  - [Repository Structure](#repository-structure)
  - [Contributing](#contributing)
  - [License](#license)
  - [Dependencies](#dependencies)
  - [Troubleshooting](#troubleshooting)

## Features

- **Interactive Assistant**: Communicate interactively with the assistant to run shell commands, fetch configurations, etc.
- **Automated Workflows**: GitHub Actions workflows for creating, configuring, and updating the assistant.
- **File Management**: Scripts for loading, cleaning, and managing files in the assistant's vector store for efficient data handling.

## Installation

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/your_username/ai_assistant.git
    cd ai_assistant
    ```

2. **Set Up Python Environment**:
    ```sh
    python3 -m pip install --upgrade pip
    pip3 install -r requirements.txt
    ```

3. **Install the Package**:
    ```sh
    pip install .
    ```

4. **Set Up Environment Variables**:
    Set up your OpenAI API key in the environment variables:
    ```sh
    export OPENAI_API_KEY=<your_openai_api_key>
    ```

## Usage

With the package installed, you can interact with the AI assistant using the provided CLI commands.

### General Usage

- **Run the Assistant**:
  ```sh
  ai_assistant --message "Your message here"
  ```

- **Using Specific Assistants**:
  ```sh
  ai_assistant --message "Your message here" --assistant <assistant_name>
  ```

- **Storing and Loading Threads**:
  - **Save Thread ID**:
    ```sh
    ai_assistant --message "Your message here" --save-thread-id <path_to_save_thread_id>
    ```
  - **Load Thread ID**:
    ```sh
    ai_assistant --message "Your message here" --load-thread-id <path_to_load_thread_id>
    ```

### GitHub Actions Workflows

- **Load Files into Assistant**:
  This action updates the files in your assistant's vector store.
  
- **Run Assistant on Issue**:
  This workflow triggers the assistant whenever a new issue is created in the repository.

## Repository Structure

```
.github/
├── workflows/
│   ├── clean_before_merge.yaml
│   ├── create_repo_assistant.yml
│   ├── handle_branch_deletion.yml
│   ├── run_assistant_on_issue.yaml
│   ├── update_assistant.yml
│   └── update_assistant_files.yml
ai_assistant/
├── utils/
│   ├── generate_repo_structure.py
│   └── utils.py
├── __init__.py
├── assistant_config.json
├── assistant_functions.py
├── assistant_gpt.py
├── create_repo_assistant.py
├── delete_repo_assistant.py
├── generate_commit.py
├── run_assistant.py
├── squash_branch.py
├── update_assistant.py
└── update_files.py
ai_assistant.egg-info/
├── dependency_links.txt
├── entry_points.txt
├── PKG-INFO
├── requires.txt
├── SOURCES.txt
└── top_level.txt
build/
├── bdist.linux-x86_64/
└── lib/
    └── ai_assistant/
        ├── utils/
        │   ├── generate_repo_structure.py
        │   └── utils.py
        ├── __init__.py
        ├── assistant_config.json
        ├── assistant_functions.py
        ├── assistant_gpt.py
        ├── create_repo_assistant.py
        ├── delete_repo_assistant.py
        ├── generate_commit.py
        ├── run_assistant.py
        ├── squash_branch.py
        ├── update_assistant.py
        └── update_files.py
scripts/
└── clean_backup_files.sh
tools/
├── open_ai_configuration/
│   ├── configure_assistant.py
│   ├── delete_all_open_ai_files.py
│   ├── dump_assistant_config.py
│   └── initial_config.json
└── workflow_specific/
    └── fetch_ids_from_names.py
.gitignore
LICENSE
README.md
repo_assistant_config.json
requirements.txt
setup.py
thread-id
```

## Contributing

Contributions are welcome! Please create a pull request to propose any changes or improvements.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Dependencies

- Python 3.x
- [OpenAI Python SDK](https://pypi.org/project/openai/)
- [Pydantic](https://pypi.org/project/pydantic/)


## Troubleshooting

If you encounter issues, ensure that:

- Your OpenAI API key is correctly set in your environment variables.
- All dependencies are installed as specified in the `requirements.txt`.