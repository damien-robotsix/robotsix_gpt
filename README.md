# GPT Repository Assistant

This repository provides a framework for integrating a GPT-powered AI assistant into your software development workflow. The assistant is designed to assist with development and maintenance tasks by leveraging OpenAI's models. It allows for executing shell commands, searching files, and handling issues directly through the repository interface.

## Features

- **Interactive Assistant:** Communicate with the assistant for tasks such as running shell commands and fetching configurations.
- **Automated Workflows:** GitHub Actions workflows for creating, configuring, and updating the assistant.
- **File Management:** Scripts for loading and cleaning files in the assistant's vector store for efficient data handling.

## Installation

1. **Clone the Repository**

   ```sh
   git clone https://github.com/your_username/gpt-repo-assistant.git
   cd gpt-repo-assistant
   ```

2. **Set up the Python Environment**
   ```sh
   python3 -m pip install --upgrade pip
   pip3 install -r requirements.txt
   ```

3. **Environment Variables**

   Set up your OpenAI API key in the environment variables:

   ```sh
   export OPENAI_API_KEY=<your_openai_api_key>
   ```

## Usage

- **Run Assistant Script:** Use `run_assistant.py` to interact with the assistant.

   ```sh 
   python3 tools/run_assistant.py "Your message here"
   ```

- **GitHub Actions Workflows:**
  - Use the `Load Files into Assistant` action to update the files in your assistant's vector store.
  - The `Run Assistant on Issue` workflow triggers the assistant whenever a new issue is created.

## Repository Structure

```plaintext
├── .github/
│   └── workflows/
│       ├── assistant-load-file.yaml
│       ├── create_gpt_assistant.yaml
│       └── run_assistant_on_issue.yaml
├── tools/
│   ├── assistant_functions.py
│   ├── clean_assistant_files.py
│   ├── configure_assistant.py
│   ├── create_assistant.py
│   ├── generate_repo_structure.py
│   ├── load_files_assistant.py
│   ├── run_assistant.py
│   └── utils.py
├── assistant_config.json
├── repo_structure.txt
└── requirements.txt
```

## Contributing

Contributions are welcome! Please create a pull request to propose any changes or improvements.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Dependencies

- Python 3.x
- [OpenAI Python SDK](https://pypi.org/project/openai/)
- [Pydantic](https://pypi.org/project/pydantic/)

## Example Commands

- To update the vector store from your repository files:
  ```sh
  python tools/update_vector_store.py <repo_path>
  ```
- To clean the vector store:
  ```sh
  python tools/clean_vector_store.py
  ```

## Troubleshooting

If you encounter issues, ensure that:
- Your OpenAI API key is correctly set in your environment variables.
- All dependencies are installed as specified in the `requirements.txt`.