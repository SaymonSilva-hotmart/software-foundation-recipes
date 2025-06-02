# OpenRewrite Recipe Manager

This project provides a Python script to manage and apply OpenRewrite recipes across multiple GitHub repositories.

## Features

- Clone or update multiple GitHub repositories
- Apply OpenRewrite recipes to repositories
- Generate draft pull requests with the changes
- Configurable through JSON configuration file

## Prerequisites

- Python 3.7+
- Git
- Maven
- GitHub Personal Access Token (for PR creation)

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your GitHub token:
```
GITHUB_TOKEN=your_github_token_here
```

## Configuration

Edit the `config.json` file to configure:

- List of repositories to process
- OpenRewrite recipes to apply
- Settings for PR generation and repository download

Example configuration:
```json
{
    "repositories": [
        {
            "name": "example-repo",
            "url": "https://github.com/example/example-repo.git",
            "branch": "main"
        }
    ],
    "recipes": [
        {
            "name": "org.openrewrite.java.spring.boot2.SpringBoot2to3Migration",
            "description": "Migrate Spring Boot 2.x to 3.x"
        }
    ],
    "settings": {
        "GENERATE_PR": true,
        "DOWNLOAD_REPOS": true,
        "WORKSPACE_DIR": "./workspace"
    }
}
```

## Usage

Run the script:
```bash
python openrewrite_manager.py
```

The script will:
1. Download or update repositories if `DOWNLOAD_REPOS` is true
2. Apply each recipe to each repository
3. Create draft pull requests if `GENERATE_PR` is true

## Notes

- Make sure you have write access to the repositories you want to modify
- The script will create a `workspace` directory to store the repositories
- Each recipe application will create a new branch and PR 