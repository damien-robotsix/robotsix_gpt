import os
import shutil
import tempfile


def setup_fake_git_directory():
    """
    Set up a temporary fake git directory for testing purposes, mimicking 'git init'.
    Returns the path to the fake git directory.
    """
    fake_git_dir = tempfile.mkdtemp()
    git_dir = os.path.join(fake_git_dir, '.git')
    os.makedirs(git_dir, exist_ok=True)

    # Create essential git init files
    with open(os.path.join(git_dir, 'HEAD'), 'w') as head_file:
        head_file.write('ref: refs/heads/master\n')  # Default branch

    # Create necessary directories
    os.makedirs(os.path.join(git_dir, 'refs', 'heads'), exist_ok=True)
    os.makedirs(os.path.join(git_dir, 'refs', 'tags'), exist_ok=True)

    # Create placeholder files
    with open(os.path.join(git_dir, 'config'), 'w') as config_file:
        config_file.write('[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n')

    with open(os.path.join(git_dir, 'description'), 'w') as description_file:
        description_file.write('Fake repository for testing purposes')

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

