import os
import re
import clang.cindex
from typing import List, Dict, Tuple

clang.cindex.Config.set_library_file('/usr/lib/llvm-14/lib/libclang-14.so.1')


def keep_full(content: str, start_line: int = 1, end_line: int = None) -> List[Dict]:
    """
    Returns the entire content as a single chunk with line information.
    """
    if end_line is None:
        end_line = content.count('\n') + 1
    return [{
        'content': content,
        'start_line': start_line,
        'end_line': end_line
    }]

def check_test_macros(content: str) -> bool:
    """
    Checks if the content contains test macros.
    """
    return re.match(r'^\s*TEST', content)


def chunk_cpp_file(filepath: str) -> Tuple[List[Dict], str]:
    """
    Splits a .cpp file into individual functions using libclang.
    Each chunk includes the function's content along with its start and end lines.
    Also generates an overview where each function is replaced by a comment.
    """
    index = clang.cindex.Index.create()
    try:
        translation_unit = index.parse(filepath, args=['-std=c++20', '-I./include'])
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return [], ""

    chunks = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Collect all function extents
    elements = []

    def visit_node(node):
        # Capture function implementations
        if (node.kind == clang.cindex.CursorKind.CXX_METHOD \
        or node.kind == clang.cindex.CursorKind.CONSTRUCTOR) \
        and node.location.file.name == filepath:
            skip = False
            start_line = node.extent.start.line
            end_line = node.extent.end.line
            name = node.spelling or node.displayname
            elem_type = "method" if node.kind == clang.cindex.CursorKind.CXX_METHOD else "constructor"
            if start_line == end_line and check_test_macros(lines[start_line - 1]):
                skip = True
            if not skip:
                elements.append((start_line, end_line, elem_type, name))
                chunks.append({
                    'type': elem_type,
                    'content': ''.join(lines[start_line - 1:end_line]).strip(),
                    'start_line': start_line,
                    'end_line': end_line,
                    'name': name
                })
        for child in node.get_children():
            visit_node(child)

    visit_node(translation_unit.cursor)

    # Sort functions by start_line
    elements.sort(key=lambda x: x[0])

    # Generate overview by replacing function parts with comments
    overview_lines = []
    current_line = 1
    for func_start, func_end, elem_type, name in elements:
        if current_line < func_start:
            # Add non-function lines with prepending with line number
            overview_lines.extend([f"{i + current_line}: {line}" for i, line in enumerate(lines[current_line - 1:func_start - 1])])
        # Replace function lines with a comment
        overview_lines.append(f"// {elem_type} {name} definition\n")
        current_line = func_end + 1

    # Handle any remaining lines after the last function
    total_lines = len(lines)
    if current_line <= total_lines:
        overview_lines.extend([f"{i + current_line}: {line}" for i, line in enumerate(lines[current_line - 1:total_lines])])

    overview_content = ''.join(overview_lines)

    return chunks, overview_content


def chunk_md_file(content: str) -> Tuple[List[Dict], str]:
    """
    Splits a Markdown file into sections based on headings.
    Each chunk includes the section's content along with its start and end lines.
    Also generates an overview where each section is replaced by a comment.

    Returns:
        - List of section chunks.
        - Overview content as a string.
    """
    lines = content.split('\n')
    chunks = []
    overview_lines = []
    current_chunk = []
    start_line = 1
    current_line = 1
    inside_section = False  # To track whether we're inside a section with content

    for _, line in enumerate(lines):
        # Detect a heading (e.g., lines starting with "#", "##", etc.)
        if re.match(r'^\s*#', line):
            if inside_section:  # If we are inside a section with content, end the current chunk
                end_line = current_line - 1
                chunks.append({
                    'content': '\n'.join(current_chunk).strip(),
                    'start_line': start_line,
                    'end_line': end_line
                })
                current_chunk = []  # Reset the chunk content
                inside_section = False  # Reset the section tracking

            # Add the heading to the overview
            overview_lines.append(f"{line}\n")

            # Start a new section
            start_line = current_line
            current_chunk.append(line)  # Add the heading to the current chunk
        else:
            # For non-heading lines, add them to the current chunk
            if line.strip():  # Non-empty lines indicate content
                inside_section = True
            current_chunk.append(line)

        current_line += 1

    # Add the last chunk if it has content
    if current_chunk and inside_section:
        end_line = current_line - 1
        chunks.append({
            'content': '\n'.join(current_chunk).strip(),
            'start_line': start_line,
            'end_line': end_line
        })

    # Generate the overview content
    overview_content = ''.join(overview_lines)

    return chunks, overview_content


def is_text_file(filepath: str) -> bool:
    """
    Checks if a file is a text file by attempting to decode a portion of it.
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return False
            # Try decoding as UTF-8
            chunk.decode('utf-8')
            return True
    except (UnicodeDecodeError, OSError):
        return False


def chunk_file(filepath: str) -> Tuple[Dict[str, List[Dict]], Dict[str, str]]:
    """
    Determines the file type and applies the appropriate chunking method.
    Returns two dictionaries:
        - Chunks: mapping file paths to lists of chunks.
        - Overviews: mapping file paths to their overview content.
    Each chunk contains 'content', 'start_line', and 'end_line'.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if not is_text_file(filepath):
        return {}, {}

    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    chunks = None
    overview = None

    if ext == '.cpp':
        chunks, overview = chunk_cpp_file(filepath)
    elif ext == '.md':
        chunks, overview = chunk_md_file(content)
    else:
        chunks = keep_full(content)

    return ({filepath: chunks} if chunks else {}, {filepath: overview} if overview else {})


def process_repository(repo_path: str) -> Tuple[Dict[str, List[Dict]], Dict[str, str]]:
    """
    Processes all relevant files in the repository and returns two dictionaries:
        - Chunked Files: mapping file paths to their respective chunks.
        - Overviews: mapping file paths to their overview content.
    Each chunk contains 'content', 'start_line', and 'end_line'.
    """
    chunked_files = {}
    overviews = {}

    for root, _, files in os.walk(repo_path):
        for file in files:
            filepath = os.path.join(root, file)
            file_chunks, file_overview = chunk_file(filepath)
            if file_chunks:
                chunked_files.update(file_chunks)
            if file_overview:
                overviews[filepath] = file_overview

    return chunked_files, overviews
