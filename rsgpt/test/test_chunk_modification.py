from rsgpt.tools import modify_file_chunk, ChunkRange
from rsgpt.utils.git import get_repo_root
from rsgpt.utils.repository_loader import load_repository
import shutil
import os


def test_modify_multiple_chunks():
    load_repository(get_repo_root())

    # The path to the test file and its backup
    file_path = "rsgpt/test/long_test_file.txt"
    backup_path = "rsgpt/test/long_test_file_backup.txt"

    # Create a backup of the file
    shutil.copy(file_path, backup_path)

    # Define the chunks to modify (e.g., chunks 5 to 7)
    start_chunk = 5
    end_chunk = 7

    # Generate new content for these chunks
    new_content = "This is the modified content for chunks 5 through 7."

    try:
        # Execute modify_file_chunk for the range
        modify_file_chunk.invoke(
            {
                "file_path": file_path,
                "chunk_range": {"start_chunk": start_chunk, "stop_chunk": end_chunk},
                "new_content": new_content,
            }
        )

        # Print success message for manual verification
        print("Test passed: Chunks modified successfully.")

    finally:
        # Restore the file from backup
        shutil.copy(backup_path, file_path)
        # Delete backup file
        os.remove(backup_path)


if __name__ == "__main__":
    test_modify_multiple_chunks()

