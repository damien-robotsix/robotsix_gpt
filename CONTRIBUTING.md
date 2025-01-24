## Code Style Guidelines

### General Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style conventions.
- Where applicable, also consider [PEP 257](https://www.python.org/dev/peps/pep-0257/) for docstring conventions.

### Code Layout

- **Indentation:** Use 4 spaces per indentation level. Do not use tabs.
- **Line Length:** Limit all lines to a maximum of 79 characters.
- **Blank Lines:** Surround top-level function and class definitions with two blank lines. Method definitions inside a class are surrounded by a single blank line.

### Imports

- Imports should always be at the top of the file, just after any module comments and docstrings.
- Follow the order: standard library imports, third-party imports, local application/library-specific imports. Each group should be separated by a blank line.
  
```python
import os
import sys

import requests

from mymodule import my_function
```

### Naming Conventions

- **Function and Variable Names:** Use lowercase words separated by underscores, e.g., `my_function`, `variable_name`.
- **Class Names:** Follow the CapWords convention, e.g., `MyClass`.
- **Constants:** Use all uppercase words separated by underscores, e.g., `MAX_OVERFLOW`.

### Comments

- Comments should be complete sentences. Use one or two spaces after a sentence-ending period.
- Ensure that comments are up to date with the code they describe.
- Use inline comments sparingly and only if necessary.

### Docstrings

- Write docstrings for all public modules, functions, classes, and methods.
- Follow the conventions outlined in [PEP 257](https://www.python.org/dev/peps/pep-0257/) for writing docstrings.

### Strings

- Prefer using single quotes (`'`) for strings unless the string contains a single quote character.

### Whitespaces

- Avoid extraneous whitespace in the following situations:
  ```python
  # Correct:
  spam(ham[1], {eggs: 2})
  
  # Wrong:
  spam( ham[ 1 ], { eggs: 2 } )
  ```

### Exceptions

- Use specific exception types whenever possible.
- Use "try-except" block for handling exceptions when necessary. Clean up resources after exceptions using "finally".

### Best Practices

- **Type Hints:** Use type hints to specify the expected types of function arguments and return values.
- **Linter Usage:** Use tools like Flake8 or pylint to automatically check for style violations.
- **Testing:** Write unit tests for new code and changes with frameworks such as pytest or unittest.
  
```python
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b
```

Please ensure you follow these guidelines when contributing new code to maintain consistency across the project. For any queries related to these guidelines, please reach out in our project's communication channel.
