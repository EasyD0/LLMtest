# 最好的版本
import git
from git import Repo

def get_file_changed_lines(repo_path: str, file_path: str, commit1_hash: str, commit2_hash: str) -> list[int]:
    """
    Returns a list of line numbers that have been changed for a specific file
    between two commits.

    Args:
        repo_path (str): The path to the root of the Git repository.
        file_path (str): The path to the file relative to the repository root.
        commit1_hash (str): The hash of the first commit (older).
        commit2_hash (str): The hash of the second commit (newer).

    Returns:
        list[int]: A list of line numbers that have been changed. Returns an
                   empty list if the file was not changed or the paths are invalid.
    """
    try:
        repo = Repo(repo_path)
        
        # Get the commit objects
        commit1 = repo.commit(commit1_hash)
        commit2 = repo.commit(commit2_hash)
        
        # Check if the file exists in the repository at commit2
        # This prevents errors if the file was deleted or the path is wrong.
        try:
            tree2 = commit2.tree
            tree2[file_path]
        except KeyError:
            print(f"File not found in the repository at commit: {file_path}")
            return []

        # Get the diff between the two commits for the specific file
        diff_index = commit1.diff(commit2, paths=[file_path], create_patch=True)
        
        # If the diff_index is empty, the file hasn't changed
        if not diff_index:
            return []
            
        diff_text = diff_index[0].diff.decode('utf-8')
        
        # Parse the diff text to find changed line numbers
        changed_lines = set()
        current_line_number = 0
        
        for line in diff_text.splitlines():
            # Match diff hunk headers, e.g., "@@ -1,8 +1,9 @@"
            if line.startswith('@@'):
                # Extract the starting line number from the second part of the hunk header
                # This corresponds to the newer commit (commit2)
                try:
                    parts = line.split()
                    if len(parts) > 2:
                        hunk_info = parts[2]
                        # The format is +start_line,num_lines
                        start_line_str = hunk_info.split(',')[0].strip('+')
                        current_line_number = int(start_line_str) - 1 # Use -1 to get the correct start line index
                except (IndexError, ValueError):
                    continue

            elif line.startswith('+'):
                # Added line, corresponds to the newer commit
                changed_lines.add(current_line_number)
                current_line_number += 1
            elif line.startswith('-'):
                # Deleted line, do not increment line number as it's not in the new file
                pass
            else:
                # Unchanged line, increment line number
                current_line_number += 1
                
        return sorted(list(changed_lines))

    except git.InvalidGitRepositoryError:
        print(f"Error: The provided path is not a valid Git repository: {repo_path}")
        return []
    except git.BadObject:
        print("Error: One or both of the provided commit hashes are invalid.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

if __name__ == '__main__':
    oldhash = "80036b3c09c6673f020607074016e8523b994914"
    newhash = "36079d22971fdd8ca2f372edef906b489df6366e"
    print(get_file_changed_lines("./","preprocess/a.py",oldhash, newhash))
    print(get_file_changed_lines("./","preprocess/a.py",newhash, oldhash))
