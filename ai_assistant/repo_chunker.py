import json
import os
import pandas as pd
from pathlib import Path
from tree_sitter_languages import get_parser
from magika import Magika
from magika.types import MagikaResult
from collections import defaultdict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '.ai_assistant', 'config.json')

def load_config(config_path):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        print(f"Warning: Configuration file not found at {config_path}. Please run 'ai_init' to create it.")
        exit(1)

config = load_config(CONFIG_PATH)
REPO_DIR = config.get('repo_dir', '.')
MAX_TOKENS = config.get('max_tokens', 250)
IGNORE_PATTERNS = config.get('ignore_patterns', [])

def detect_file_type(file_path: str) -> MagikaResult:
    """Detect the file type using Magika."""
    magika = Magika()
    path = Path(file_path)
    return magika.identify_path(path)

def should_ignore(file_path: str, ignore_patterns: list) -> bool:
    """Determine whether to ignore a file or directory based on patterns."""
    for pattern in ignore_patterns:
        if pattern.startswith('*.'):
            # Handle wildcard patterns for file extensions
            if file_path.endswith(pattern[1:]):
                return True
        elif pattern in file_path:
            return True
    return False

def count_tokens(source_code: str) -> int:
    """Count tokens in the source code. Placeholder for accurate tokenization."""
    # Implement a proper tokenizer if needed. For now, use word count.
    return len(source_code.split())

def traverse_tree(node, source_lines, max_tokens, chunks, file_relative_path):
    """Recursively traverse the syntax tree to create initial chunks with token counts."""
    # Extract the text corresponding to the node
    start_line = node.start_point[0] + 1  # 1-based indexing
    end_line = node.end_point[0] + 1
    node_text = '\n'.join(source_lines[node.start_point[0]:node.end_point[0]+1])
    token_count = count_tokens(node_text)

    if token_count <= max_tokens:
        chunk = {
            'file_path': file_relative_path,
            'line_start': start_line,
            'line_end': end_line,
            'token_count': token_count
        }
        chunks.append(chunk)
    else:
        # If the node is too large, traverse its children
        for child in node.children:
            traverse_tree(child, source_lines, max_tokens, chunks, file_relative_path)

def chunk_file(file_path: str, max_tokens: int = MAX_TOKENS) -> list:
    """Chunk a file using tree-sitter based on its detected type."""
    result = detect_file_type(file_path)
    file_type = result.dl.ct_label
    if not file_type:
        print(f"Could not detect file type for {file_path}. Skipping.")
        return []

    try:
        parser = get_parser(file_type)
    except Exception as e:
        print(f"No parser available for file type '{file_type}' in {file_path}. Error: {e}")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            source_code = file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

    try:
        tree = parser.parse(bytes(source_code, 'utf8'))
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return []

    root_node = tree.root_node
    source_lines = source_code.splitlines()
    chunks = []
    file_relative_path = os.path.relpath(file_path, REPO_DIR)

    traverse_tree(root_node, source_lines, max_tokens, chunks, file_relative_path)

    return chunks

def agglomerate_chunks(all_chunks, max_tokens):
    """
    Agglomerate chunks to reach as close as possible to max_tokens per aggregated chunk.
    """
    agglomerated = []
    # Group chunks by file_path
    chunks_by_file = defaultdict(list)
    for chunk in all_chunks:
        chunks_by_file[chunk['file_path']].append(chunk)
    
    for file_path, chunks in chunks_by_file.items():
        # Sort chunks by starting line
        sorted_chunks = sorted(chunks, key=lambda x: x['line_start'])
        current_agg = {
            'file_path': file_path,
            'line_start': None,
            'line_end': None,
            'token_count': 0
        }
        
        for chunk in sorted_chunks:
            if current_agg['line_start'] is None:
                # Initialize the first chunk
                current_agg['line_start'] = chunk['line_start']
                current_agg['line_end'] = chunk['line_end']
                current_agg['token_count'] = chunk['token_count']
            else:
                if current_agg['token_count'] + chunk['token_count'] <= max_tokens:
                    # Aggregate the chunk
                    current_agg['line_end'] = chunk['line_end']
                    current_agg['token_count'] += chunk['token_count']
                else:
                    # Save the current aggregated chunk
                    agglomerated.append({
                        'file_path': current_agg['file_path'],
                        'line_start': current_agg['line_start'],
                        'line_end': current_agg['line_end'],
                        'token_count': current_agg['token_count']
                    })
                    # Start a new aggregated chunk
                    current_agg = {
                        'file_path': file_path,
                        'line_start': chunk['line_start'],
                        'line_end': chunk['line_end'],
                        'token_count': chunk['token_count']
                    }
        # Don't forget to add the last aggregated chunk
        if current_agg['line_start'] is not None:
            agglomerated.append({
                'file_path': current_agg['file_path'],
                'line_start': current_agg['line_start'],
                'line_end': current_agg['line_end'],
                'token_count': current_agg['token_count']
            })
    return agglomerated

def main():
    all_chunks = []

    # Walk through the repository
    for root, dirs, files in os.walk(REPO_DIR):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), IGNORE_PATTERNS)]
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, REPO_DIR)
            if should_ignore(relative_path, IGNORE_PATTERNS):
                continue

            chunks = chunk_file(file_path, MAX_TOKENS)
            if chunks:
                all_chunks.extend(chunks)
                print(f"Parsed {relative_path} into {len(chunks)} initial chunks.")
            else:
                print(f"No chunks created for {relative_path}.")

    if all_chunks:
        # Agglomerate chunks
        agglomerated_chunks = agglomerate_chunks(all_chunks, MAX_TOKENS)
        print(f"Agglomerated into {len(agglomerated_chunks)} chunks.")

        # Optionally, remove the token_count if not needed in the final CSV
        for chunk in agglomerated_chunks:
            del chunk['token_count']

        # Create DataFrame
        df = pd.DataFrame(agglomerated_chunks)
        print(df.head())

        # Save to CSV or any desired format
        output_dir = os.path.join(REPO_DIR, '.ai_assistant')
        df.to_csv(os.path.join(output_dir, 'repo_chunks.csv'), index=False)
        print("Agglomerated chunks saved to repo_chunks.csv.")
    else:
        print("No chunks were created from the repository.")

if __name__ == '__main__':
    main()
