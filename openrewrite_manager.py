import json
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

class OpenRewriteManager:
    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)
        self.workspace_dir = Path(self.config["settings"]["WORKSPACE_DIR"])
        self.workspace_dir.mkdir(exist_ok=True)
        load_dotenv()

        self.rewrite_version = "8.21.0"

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)

    def _add_rewrite_dependencies(self, pom_path):
        """Add OpenRewrite dependencies to pom.xml if they don't exist"""
        with open(pom_path, 'r') as f:
            content = f.read()

        # Check if rewrite.version already exists
        if '<rewrite.version>' not in content:
            # Add rewrite.version to properties
            properties_end = content.find('</properties>')
            if properties_end != -1:
                content = content[:properties_end] + f'\n        <rewrite.version>{self.rewrite_version}</rewrite.version>\n    ' + content[properties_end:]

        # Check if OpenRewrite dependencies already exist
        while 'rewrite-java' not in content:
            # Find the main dependencies section (not in dependencyManagement)
            dependencies_start = content.find('<dependencies>')
            dependencies_end = content.find('</dependencies>')
            
            # Check if this dependencies section is inside dependencyManagement
            dependency_management_start = content.find('<dependencyManagement>')
            dependency_management_end = content.find('</dependencyManagement>')
            
            if dependency_management_start != -1 and dependencies_start > dependency_management_start:
                dependencies_start = content.find('<dependencies>',dependency_management_end)
                dependencies_end = content.find('</dependencies>',dependency_management_end)

            # Add OpenRewrite dependencies
            rewrite_deps = f'''
        <!-- OpenRewrite Dependencies -->
        <dependency>
            <groupId>org.openrewrite</groupId>
            <artifactId>rewrite-java</artifactId>
            <version>${{rewrite.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.openrewrite</groupId>
            <artifactId>rewrite-maven</artifactId>
            <version>${{rewrite.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.openrewrite</groupId>
            <artifactId>rewrite-yaml</artifactId>
            <version>${{rewrite.version}}</version>
        </dependency>
    '''
            content = content[:dependencies_end] + rewrite_deps + content[dependencies_end:]


        # Write back to file
        with open(pom_path, 'w') as f:
            f.write(content)

    def clone_or_update_repo(self, repo_config):
        repo_path = self.workspace_dir / repo_config["name"]
        
        if repo_path.exists():
            print(f"Repository {repo_config['name']} already exists. Updating...")
            subprocess.run(["git", "fetch"], cwd=repo_path)
            subprocess.run(["git", "checkout", repo_config["branch"]], cwd=repo_path)
            subprocess.run(["git", "pull"], cwd=repo_path)
        else:
            print(f"Cloning repository {repo_config['name']}...")
            subprocess.run(["git", "clone", repo_config["url"], repo_path])
            subprocess.run(["git", "checkout", repo_config["branch"]], cwd=repo_path)

    def apply_recipe(self, repo_name, recipe):
        repo_path = self.workspace_dir / repo_name
        if not repo_path.exists():
            print(f"Repository {repo_name} not found!")
            return False

        # Add OpenRewrite dependencies to pom.xml
        pom_path = repo_path / "pom.xml"
        if pom_path.exists():
            print(f"Adding OpenRewrite dependencies to {repo_name}...")
            self._add_rewrite_dependencies(pom_path)

        print(f"Applying recipe {recipe['name']} to {repo_name}...")
        try:
            # Run the recipe using Maven
            subprocess.run([
                "mvn",
                "-Dmaven.wagon.http.ssl.insecure=true",
                "org.openrewrite.maven:rewrite-maven-plugin:run",
                f"-Drewrite.recipeArtifactCoordinates=org.openrewrite:rewrite-java:{self.rewrite_version},org.openrewrite:rewrite-maven:{self.rewrite_version},org.openrewrite:rewrite-yaml:{self.rewrite_version}",
                f"-Drewrite.activeRecipes={recipe['name']}",
                f"-Drewrite.configLocation={recipe.get('configLocation', 'recipes/')}"
            ], cwd=repo_path, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error applying recipe: {e}")
            return False

    def create_pull_request(self, repo_name, recipe):
        """Create a pull request using GitHub CLI"""
        # Find the repository config to get the base branch
        repo_config = next((repo for repo in self.config["repositories"] if repo["name"] == repo_name), None)
        if not repo_config:
            print(f"Repository {repo_name} not found in config!")
            return

        base_branch = repo_config["branch"]
        branch_name = self.config["settings"]["CARD_JIRA"]
        repo_path = self.workspace_dir / repo_name
        
        # Create new branch
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path)
        
        # Commit changes
        subprocess.run(["git", "add", "."], cwd=repo_path)
        subprocess.run(["git", "commit", "-m", f"Apply OpenRewrite recipe: {recipe['name']}"], cwd=repo_path)
        subprocess.run(["git", "push", "origin", branch_name], cwd=repo_path)

        # Create PR using GitHub CLI
        try:
            pr_title = f"Apply OpenRewrite recipe: {recipe['name']}"
            pr_body = f"Automated PR applying OpenRewrite recipe: {recipe['name']}\n\n{recipe['description']}"
            
            # Create PR using gh CLI
            result = subprocess.run([
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_body,
                "--base", base_branch,
                "--head", branch_name,
                "--draft"
            ], cwd=repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Created PR: {result.stdout.strip()}")
            else:
                print(f"Error creating PR: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            print(f"Error creating PR: {e}")
            return

    def run(self):
        if self.config["settings"]["DOWNLOAD_REPOS"]:
            for repo in self.config["repositories"]:
                self.clone_or_update_repo(repo)

        for repo in self.config["repositories"]:
            for recipe in self.config["recipes"]:
                if self.apply_recipe(repo["name"], recipe):
                    if self.config["settings"]["GENERATE_PR"]:
                        self.create_pull_request(repo["name"], recipe)
if __name__ == "__main__":
    manager = OpenRewriteManager()
    manager.run() 