import json
from tqdm import tqdm
import os
import pandas as pd
import warnings
from pathlib import Path
from ai_assistant.git_utils import find_git_root, load_gitignore, PathSpec, GitWildMatchPattern
from tree_sitter_languages import get_parser
from magika import Magika
from magika.types import MagikaResult
from collections import defaultdict
import hashlib

warnings_list = []
REPO_DIR = find_git_root(os.getcwd())
CONFIG_PATH = os.path.join(REPO_DIR, '.ai_assistant', 'config.json')

def load_config(config_path):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        warnings_list.append(f"Warning: Configuration file not found at {config_path}. Please run 'ai_init' to create it.")
        exit(1)

config = load_config(CONFIG_PATH)
MAX_TOKENS = config.get('max_tokens', 500)
gitignore_spec = load_gitignore(REPO_DIR)
config_ignore_patterns = config.get('ignore_patterns', [])
config_spec = PathSpec.from_lines(GitWildMatchPattern, config_ignore_patterns)
IGNORE_PATTERNS = config_spec + gitignore_spec

def detect_file_type(file_path: str) -> MagikaResult:
    """Detect the file type using Magika."""
    magika = Magika()
    path = Path(file_path)
    return magika.identify_path(path)

def should_ignore(file_path: str, ignore_spec: PathSpec) -> bool:
    """Determine whether to ignore a file or directory based on PathSpec."""
    return ignore_spec.match_file(file_path)

import tiktoken

def count_tokens(source_code: str) -> int:
    """Count tokens in the source code using tiktoken."""
    encoding = tiktoken.get_encoding("gpt2")
    tokens = encoding.encode(source_code)
    return len(tokens)

def traverse_tree(node, source_lines, max_tokens, chunks, file_relative_path, parent_node="file_root", warnings=None):
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
            'token_count': token_count,
            'parent_node': parent_node
        }
        chunks.append(chunk)
    else:    
        if not node.children:
            if warnings is not None:
                warnings.append(f"Warning: Node from line {start_line} to {end_line} in {file_relative_path} exceeds max tokens and has no children. Adding full node.")
            chunk = {
                'file_path': file_relative_path,
                'line_start': start_line,
                'line_end': end_line,
                'token_count': token_count,
                'parent_node': parent_node
            }
            chunks.append(chunk)
        else:
            # If the node is too large, traverse its children
            for child in node.children:
                traverse_tree(child, source_lines, max_tokens, chunks, file_relative_path, node, warnings)

def chunk_file(file_path: str, max_tokens: int = MAX_TOKENS, chunker_warnings=None) -> list:
    """Chunk a file using tree-sitter based on its detected type."""
    warnings_list = []
    result = detect_file_type(file_path)
    file_type = result.dl.ct_label
    if not file_type:
        if chunker_warnings is not None:
            chunker_warnings.append(f"Could not detect file type for {file_path}. Skipping.")
        return []

    # Check if the total token count of the file exceeds 50 times the max chunk size
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            source_code = file.read()
        total_token_count = count_tokens(source_code)
        if total_token_count > 50 * max_tokens:
            user_input = input(f"The file {file_path} has {total_token_count} tokens, which exceeds 50 times the max chunk size. Do you want to include it? (y/n): ")
            if user_input.lower() != 'y':
                return []
    except Exception as e:
        if chunker_warnings is not None:
            chunker_warnings.append(f"Error reading file {file_path}: {e}")
        return []

    if file_type == 'shell':
        file_type = 'bash'

    if file_type == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                source_code = file.read()
        except Exception as e:
            if chunker_warnings is not None:
                chunker_warnings.append(f"Error reading file {file_path}: {e}")
            return []

        source_lines = source_code.splitlines()
        chunks = []
        file_relative_path = os.path.relpath(file_path, REPO_DIR)

        # Chunk text files based on max_tokens
        current_chunk = {
            'file_path': file_relative_path,
            'line_start': 1,
            'line_end': 0,
            'token_count': 0,
            'parent_node': 'file_root'
        }
        for i, line in enumerate(source_lines, start=1):
            line_token_count = count_tokens(line)
            if current_chunk['token_count'] + line_token_count > max_tokens:
                current_chunk['line_end'] = i - 1
                chunks.append(current_chunk)
                current_chunk = {
                    'file_path': file_relative_path,
                    'line_start': i,
                    'line_end': 0,
                    'token_count': line_token_count,
                    'parent_node': 'file_root'
                }
            else:
                current_chunk['token_count'] += line_token_count

        # Add the last chunk
        if current_chunk['token_count'] > 0:
            current_chunk['line_end'] = len(source_lines)
            chunks.append(current_chunk)

        return chunks
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                parser = get_parser(file_type)
        except Exception as e:
            if chunker_warnings is not None:
                chunker_warnings.append(f"No parser available for file type '{file_type}' in {file_path}. Error: {e}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                source_code = file.read()
        except Exception as e:
            if chunker_warnings is not None:
                chunker_warnings.append(f"Error reading file {file_path}: {e}")
            return []

        try:
            tree = parser.parse(bytes(source_code, 'utf8'))
        except Exception as e:
            if chunker_warnings is not None:
                chunker_warnings.append(f"Error parsing file {file_path}: {e}")
            return []

        root_node = tree.root_node
        source_lines = source_code.splitlines()
        chunks = []
        file_relative_path = os.path.relpath(file_path, REPO_DIR)

        traverse_tree(root_node, source_lines, max_tokens, chunks, file_relative_path, warnings=chunker_warnings)

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
        current_agg = {
            'file_path': file_path,
            'line_start': None,
            'line_end': None,
            'token_count': 0
        }
        for chunk in chunks:
            if current_agg['line_start'] is None:
                # Initialize the first chunk
                current_agg['line_start'] = chunk['line_start']
                current_agg['line_end'] = chunk['line_end']
                current_agg['token_count'] = chunk['token_count']
                current_agg['parent_node'] = chunk['parent_node']
            else:
                if current_agg['token_count'] + chunk['token_count'] <= max_tokens and current_agg['parent_node'] == chunk['parent_node']:
                    # Aggregate the chunk
                    current_agg['line_end'] = chunk['line_end']
                    current_agg['token_count'] += chunk['token_count']
                else:
                    # Save the current aggregated chunk
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        lines = file.readlines()
                        content = ''.join(lines[current_agg['line_start']-1:current_agg['line_end']]).strip()
                    agglomerated.append({
                        'file_path': current_agg['file_path'],
                        'line_start': current_agg['line_start'],
                        'line_end': current_agg['line_end'],
                        'token_count': current_agg['token_count'],
                        'relative_path': os.path.relpath(current_agg['file_path'], REPO_DIR),
                        'hash': hashlib.sha256(content.encode('utf-8')).hexdigest()
                    })
                    # Start a new aggregated chunk
                    current_agg = {
                        'file_path': file_path,
                        'line_start': chunk['line_start'],
                        'line_end': chunk['line_end'],
                        'token_count': chunk['token_count'],
                        'parent_node': chunk['parent_node']
                    }
        # Don't forget to add the last aggregated chunk
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            content = ''.join(lines[current_agg['line_start']-1:current_agg['line_end']]).strip()
        if current_agg['line_start'] is not None:
            agglomerated.append({
                'file_path': current_agg['file_path'],
                'line_start': current_agg['line_start'],
                'line_end': current_agg['line_end'],
                'token_count': current_agg['token_count'],
                'relative_path': os.path.relpath(current_agg['file_path'], REPO_DIR),
                'hash': hashlib.sha256(content.encode('utf-8')).hexdigest()
            })
    return agglomerated

def get_file_modification_time(file_path: str) -> float:
    """Get the last modification time of a file with higher precision."""
    return os.path.getmtime(file_path)

def main():
    # Load existing chunks from CSV
    output_dir = os.path.join(REPO_DIR, '.ai_assistant')
    csv_path = os.path.join(output_dir, 'repo_chunks.csv')
    if os.path.exists(csv_path):
        existing_chunks_df = pd.read_csv(csv_path)
    else:
        existing_chunks_df = pd.DataFrame()
    all_chunks = []

    processed_files = []
    processing_warnings = []

    # Walk through the repository with a progress bar
    for root, dirs, files in tqdm(os.walk(REPO_DIR), desc="Processing files"):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), IGNORE_PATTERNS)]
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, REPO_DIR)
            if not os.path.exists(file_path) or should_ignore(relative_path, IGNORE_PATTERNS):
                continue

            # Check if the file has been modified since the last chunking
            file_mod_time = get_file_modification_time(file_path)
            if 'file_path' in existing_chunks_df.columns:
                existing_chunk = existing_chunks_df[existing_chunks_df['file_path'] == relative_path]
            else:
                existing_chunk = pd.DataFrame()  # Create an empty DataFrame if 'file_path' column is missing
            if not existing_chunk.empty and 'mod_time' in existing_chunk.columns and existing_chunk['mod_time'].iloc[0] >= file_mod_time - 0.001:
                # File has not been modified, skip re-chunking
                continue

            # File has been modified, is new, or missing mod_time, re-chunk it
            chunks = chunk_file(file_path, MAX_TOKENS, chunker_warnings=processing_warnings)
            if chunks:
                for chunk in chunks:
                    chunk['mod_time'] = file_mod_time  # Add modification time to each chunk
                all_chunks.extend(chunks)
                processed_files.append(relative_path)
            else:
                processing_warnings.append(f"No chunks created for {relative_path}.")

    if all_chunks:
        # Agglomerate chunks
        agglomerated_chunks = agglomerate_chunks(all_chunks, MAX_TOKENS)
        print(f"Agglomerated into {len(agglomerated_chunks)} chunks.")

        # Create DataFrame and merge with existing data
        new_chunks_df = pd.DataFrame(agglomerated_chunks)
        # Remove old chunks for modified files if existing_chunks_df is not empty
        # Copy the embedding column from existing_chunks_df if the hash matches
        if not existing_chunks_df.empty:
            if 'hash' in new_chunks_df.columns and 'hash' in existing_chunks_df.columns:
                new_chunks_df['embedding'] = new_chunks_df['hash'].apply(
                    lambda x: existing_chunks_df[existing_chunks_df['hash'] == x]['embedding'].iloc[0] if x in existing_chunks_df['hash'].values else None
                )
            existing_chunks_df = existing_chunks_df[~existing_chunks_df['file_path'].isin(new_chunks_df['file_path'])]
        
        # Concatenate new and existing chunks
        final_chunks_df = pd.concat([existing_chunks_df, new_chunks_df], ignore_index=True)

        # Remove entries for files that no longer exist
        final_chunks_df = final_chunks_df[final_chunks_df['file_path'].apply(lambda x: os.path.exists(os.path.join(REPO_DIR, x)))]

        # Ensure 'mod_time' column exists
        if 'mod_time' not in final_chunks_df.columns or final_chunks_df['mod_time'].isnull().any():
            final_chunks_df['mod_time'] = final_chunks_df['file_path'].apply(
                lambda x: get_file_modification_time(os.path.join(REPO_DIR, x))
            )
        final_chunks_df.to_csv(csv_path, index=False)
        print("Agglomerated chunks saved to repo_chunks.csv.")
        if processing_warnings:
            print("\nWarnings:")
            for warning in processing_warnings:
                print(warning)
    else:
        print("No chunks were created from the repository.")

    print("\nProcessed files:")
    for file in processed_files:
        print(file)

if __name__ == '__main__':
    main()
