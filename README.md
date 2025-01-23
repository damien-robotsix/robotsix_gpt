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

## 📦 Dependencies

The project relies on several key packages:
- `langgraph` - For graph-based processing
- `langsmith` - Language model tooling
- `langchain` and variants - For AI model integration
- `tavily-python` - Search functionality
- `GitPython` - Git repository handling

## 🏗 Project Structure

```
rsgpt/
├── main.py              # Main application entry point
├── graphs/              # Graph-based processing components
│   ├── dispatcher.py
│   ├── repo_diver.py
│   └── specialist_with_memory.py
├── tools.py             # Repository interaction tools
└── utils/
    └── git.py          # Git utilities
```

## 🔧 Configuration

The project uses several configuration files:
- `compose.yml` - Container orchestration setup
- `project.yml` - Project configuration and environment setup
- `pyproject.toml` - Project metadata and dependencies

## 💡 Usage

[Usage instructions to be added based on specific implementation details]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

[License information to be added]

## 👥 Authors

- Initial work - [Author Name]

## 🙏 Acknowledgments

- Thanks to all contributors and maintainers
- Built with [LangChain](https://github.com/hwchase17/langchain)

---
For more information or to report issues, please visit the repository's issue tracker.
