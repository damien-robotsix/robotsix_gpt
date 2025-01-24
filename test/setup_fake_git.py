import os
import shutil
import tempfile

def setup_fake_git_directory():
    """
    Set up a temporary fake git directory for testing purposes.
    Returns the path to the fake git directory.
    """
    fake_git_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(fake_git_dir, '.git'), exist_ok=True)
    return fake_git_dir

def cleanup_fake_git_directory(fake_git_dir):
    """
    Clean up the temporary fake git directory.
    """
    shutil.rmtree(fake_git_dir)

if __name__ == "__main__":
    # Example usage
    dir_path = setup_fake_git_directory()
    print(f"Fake git directory created at: {dir_path}")
    cleanup_fake_git_directory(dir_path)
    print("Fake git directory cleaned up.")
