import hashlib

def compute_hash(file_path):
    """Compute a SHA256 hash for a file to check for modifications."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()