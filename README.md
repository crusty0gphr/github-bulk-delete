# GitHub Repository Bulk Deletion Tool

A simple Python tool to safely perform bulk deletion of your GitHub repositories.

![Demo](images/demo.gif)

## Prerequisites

- Python 3.x
- `requests` library

You can install the required dependencies using:
```bash
pip install requests
```

## GitHub Token Requirements

To use this script, you need a GitHub Personal Access Token (PAT) with appropriate permissions.

### Option 1: Classic Token (Recommended)
Create a classic token at [GitHub Settings](https://github.com/settings/tokens) with the following scopes:
- **`repo`**: Full control of private and public repositories.
- **`delete_repo`**: Required to actually delete repositories.

### Option 2: Fine-grained Token
Create a fine-grained token at [GitHub Settings](https://github.com/settings/tokens?type=beta) with:
- **Repository selection**: All repositories (or specific ones you wish to delete).
- **Permissions**:
    - **Administration**: Read and Write (this allows deletion).
    - **Metadata**: Read-only (mandatory for listing repositories).

## How to Run

1. **Set your token** (Optional but recommended):
   You can set your token as an environment variable to avoid entering it manually every time:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

2. **Execute the script**:
   ```bash
   python3 main.py
   ```

3. **Follow the prompts**:
   - The script will list all your repositories.
   - Select the repositories you want to delete by entering their numbers (e.g., `1, 3, 5-8`).
   - Confirm the deletion by typing `DELETE` when prompted.

## Safety Features

- **Bulk Selection**: Supports comma-separated lists and ranges (e.g., `1,2,5-10`).
- **Confirmation Keyword**: You must explicitly type `DELETE` (case-sensitive) to proceed with any deletion.
- **Dry Run**: You can see exactly which repositories are targeted before any action is taken.

## Running Tests

To ensure the script's logic is working correctly, you can run the provided test suite:
```bash
python3 test_github_delete.py
```
