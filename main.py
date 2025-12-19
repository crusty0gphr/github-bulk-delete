import os
import sys
from getpass import getpass
from typing import List, Dict, Any, Optional

import requests

# Type aliases for better readability
Repository = Dict[str, Any]
Repositories = List[Repository]

GITHUB_API_BASE = "https://api.github.com"


class GitHubError(Exception):
    """Base class for GitHub API errors"""
    pass


class GitHubClient:
    """Client for interacting with GitHub API"""

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        })

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_repositories(self) -> Repositories:
        """Fetch all repositories for the authenticated user"""
        repos: Repositories = []
        page = 1
        per_page = 100

        while True:
            url = f"{GITHUB_API_BASE}/user/repos?page={page}&per_page={per_page}"
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    error_msg = f"Error fetching repositories: {response.status_code}"
                    try:
                        # Try to extract an error message from GitHub API response
                        error_detail = response.json()
                        if isinstance(error_detail, dict) and "message" in error_detail:
                            error_msg += f" - {error_detail['message']}"
                    except ValueError:
                        # If the response is not valid JSON, ignore it
                        pass
                    raise GitHubError(error_msg)

                data = response.json()
                if not data:
                    break

                repos.extend(data)
                page += 1
            except requests.RequestException as e:
                raise GitHubError(f"Connection error: {e}")

        return repos

    def delete_repository(self, owner: str, repo_name: str) -> bool:
        """Delete a single repository"""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}"
        try:
            response = self.session.delete(url, timeout=10)
            return response.status_code == 204
        except requests.RequestException:
            return False


def clear_screen() -> None:
    """Clear the terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")


def parse_indices(input_str: str, repos_count: int) -> Optional[List[int]]:
    """
    Parse input string (e.g., '1,3,5-8') and return 0-based indices.
    
    Returns:
        List[int]: Sorted list of unique 0-based indices.
        None: If the input format is invalid.
    """
    indices = []
    try:
        for part in input_str.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                # Handle range like '5-8'
                start_str, end_str = part.split("-")
                start, end = int(start_str), int(end_str)
                indices.extend(range(start, end + 1))
            else:
                # Handle a single number like '3'
                indices.append(int(part))
    except ValueError:
        # Raised if int() conversion fails or the range is malformed
        return None

    # Filter for valid 1-based indices (1 to repos_count)
    # Convert to 0-based indices, remove duplicates, and sort
    return sorted(list(set(i - 1 for i in indices if 1 <= i <= repos_count)))


def display_repositories(repos: Repositories) -> None:
    """Print the list of repositories in a table format"""
    if not repos:
        return

    # Table headers
    headers = ["#", "Repository Name", "Visibility"]
    
    # Prepare data for calculation of column widths
    table_data = []
    for i, repo in enumerate(repos, 1):
        name = repo.get("name", "N/A")
        # visibility can be 'public' or 'private'
        visibility = "Private" if repo.get("private") else "Public"
        
        table_data.append([str(i), name, visibility])

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in table_data:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    # Print header
    header_row = "  ".join(val.ljust(col_widths[i]) for i, val in enumerate(headers))
    print(header_row)
    print("-" * (sum(col_widths) + (len(headers) - 1) * 2))

    # Print rows
    for row in table_data:
        print("  ".join(val.ljust(col_widths[i]) for i, val in enumerate(row)))


def confirm_deletion(repos_to_delete: Repositories) -> bool:
    """Prompt user for confirmation before deleting"""
    print(f"\nWARNING: You are about to delete {len(repos_to_delete)} repositories!")
    print("The following repositories will be deleted:")
    for repo in repos_to_delete:
        owner = repo['owner']['login']
        print(f"- {repo['name']} (owner: {owner})")

    confirm = input("\nTo confirm deletion, type 'DELETE': ")
    # Requirement: exact case-sensitive match 'DELETE'
    return confirm.strip() == "DELETE"


def main() -> None:
    print("GitHub Repository Bulk Deletion Tool")
    print("=====================================")
    print("WARNING: This action is irreversible!")
    print("Please be absolutely sure before proceeding.\n")

    token = os.getenv("GITHUB_TOKEN") or getpass("Enter your GitHub Personal Access Token: ")

    if not token:
        print("Error: GitHub token is required.")
        return

    clear_screen()
    with GitHubClient(token) as client:
        try:
            print("\nFetching your repositories...")
            repos = client.get_repositories()
        except GitHubError as e:
            print(f"Error: {e}")
            return

        clear_screen()
        if not repos:
            print("No repositories found.")
            return

        print(f"\nFound {len(repos)} repositories:")
        display_repositories(repos)

        # Selection process
        print("\nEnter the numbers of repositories you want to delete, separated by commas:")
        print("Example: 1,3,5-8 (to delete repos 1, 3, and 5 through 8)")
        input_str = input("Repositories to delete: ")

        indices = parse_indices(input_str, len(repos))
        if indices is None:
            print("Invalid input format. Please use numbers and ranges like 1,3,5-8.")
            return

        if not indices:
            print("No valid repositories selected.")
            return

        selected_repos: Repositories = [repos[i] for i in indices]

        clear_screen()
        # Safety confirmation
        if not confirm_deletion(selected_repos):
            print("Operation cancelled.")
            return

        print("\nDeleting repositories...")
        success_count = 0
        for repo in selected_repos:
            name = repo["name"]
            owner = repo["owner"]["login"]
            print(f"Deleting {name}...", end=" ", flush=True)

            if client.delete_repository(owner, name):
                print("✓ Success")
                success_count += 1
            else:
                print("✗ Failed")

        print(
            f"\nOperation completed. {success_count}/{len(selected_repos)} repositories deleted successfully."
        )


def run() -> None:
    """Run the application and handle a graceful shutdown"""
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    run()
