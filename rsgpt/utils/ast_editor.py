import ast
import astor
from typing import Callable
from langchain.tools import tool


class ASTEditor:
    def __init__(self, file_path: str):
        """
        Initialize the ASTEditor with the path to the Python file to be modified.
        """
        self.file_path = file_path
        self.tree = self.load_ast()

    def load_ast(self):
        """
        Load and parse the Python file into an abstract syntax tree (AST).
        """
        with open(self.file_path, "r") as file:
            return ast.parse(file.read(), filename=self.file_path)

    def apply_transformation(self, transform: Callable[[ast.AST], ast.AST]):
        """
        Apply a transformation function to the AST.

        Args:
            transform (Callable[[ast.AST], ast.AST]): A function that takes in an AST node and returns a transformed AST node.
        """
        self.tree = transform(self.tree)

    def save(self):
        """
        Save the modified AST back to the original Python file.
        """
        with open(self.file_path, "w") as file:
            file.write(astor.to_source(self.tree))


@tool
def rename_functions(file_path: str, name_map: dict):
    """
    Rename functions in a Python file based on a provided mapping.

    Args:
        file_path (str): The path to the Python file.
        name_map (dict): A dictionary where keys are original function names and values are new function names.

    Returns:
        str: Confirmation message after renaming functions.
    """
    editor = ASTEditor(file_path)

    class FunctionRenamer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name in name_map:
                node.name = name_map[node.name]
            self.generic_visit(node)
            return node

    editor.apply_transformation(lambda tree: FunctionRenamer().visit(tree))
    editor.save()
    return f"Functions renamed successfully in {file_path}."


@tool
def replace_function_body(file_path: str, function_name: str, new_body_code: str):
    """
    Replace the body of a specific function with new code in a Python file.

    Args:
        file_path (str): The path to the Python file.
        function_name (str): The name of the function to modify.
        new_body_code (str): The new body code as a string.

    Returns:
        str: Confirmation message after replacing the function body.
    """
    editor = ASTEditor(file_path)

    class FunctionBodyReplacer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == function_name:
                new_body = ast.parse(new_body_code).body
                node.body = new_body
            return node

    editor.apply_transformation(lambda tree: FunctionBodyReplacer().visit(tree))
    editor.save()
    return f"Body of function '{function_name}' replaced successfully in {file_path}."
