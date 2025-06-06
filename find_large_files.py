import subprocess
import sys

def find_large_git_objects(top_n=15):
    """
    Finds the largest objects in the Git repository's history.
    This script is designed to work reliably on Windows and other OSes.
    """
    try:
        # This command lists all Git objects
        command_rev_list = "git rev-list --objects --all"
        rev_list_proc = subprocess.Popen(
            command_rev_list.split(),
            stdout=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        # This command gets details for each object. The format string is crucial.
        # We use tabs as separators.
        format_str = "%(objectname)	%(objecttype)	%(objectsize)	%(rest)"
        
        # Pass the command as a list to avoid shell parsing issues.
        cat_file_proc = subprocess.Popen(
            ["git", "cat-file", f"--batch-check={format_str}"],
            stdin=rev_list_proc.stdout,
            stdout=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # Allow rev_list_proc to receive a SIGPIPE if cat_file_proc exits.
        rev_list_proc.stdout.close()
        output, _ = cat_file_proc.communicate()

        if not output:
            print("Could not retrieve Git object information. Is this a Git repository?")
            return

        objects = []
        for line in output.strip().split('\n'):
            try:
                # The format is: <sha>\t<type>\t<size>\t<path>
                parts = line.split('\t', 3)
                if len(parts) < 4:
                    continue

                sha, obj_type, size_str, path = parts
                
                if obj_type == 'blob':  # We only care about file contents (blobs)
                    objects.append({'sha': sha, 'size': int(size_str), 'path': path})
            except (ValueError, IndexError):
                # Ignore lines that cannot be parsed correctly
                continue
        
        # Sort by size in descending order
        objects.sort(key=lambda x: x['size'], reverse=True)

        print(f"--- Top {top_n} largest files in Git history ---")
        print(f"{'Size (KB)':<12} {'Path'}")
        print(f"{'---------':<12} {'----'}")
        for obj in objects[:top_n]:
            size_kb = obj['size'] / 1024
            print(f"{size_kb:<12.2f} {obj['path']}")

    except FileNotFoundError:
        print("Error: 'git' command not found. Is Git installed and in your system's PATH?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    find_large_git_objects()