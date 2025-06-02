#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

def remove_constants(file_path: str, constants: list) -> bool:
    """
    Remove specific constants from a Java file.
    
    Args:
        file_path: Path to the Java file
        constants: List of constants to remove
    
    Returns:
        bool: True if changes were made, False otherwise
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Remove constant declarations
        for constant in constants:
            # Pattern for public static final String CONSTANT = "value";
            pattern = rf'public\s+static\s+final\s+String\s+{constant}\s*=\s*"[^"]*";\s*'
            content = re.sub(pattern, '', content)
            
            # Pattern for CONSTANT usage
            usage_pattern = rf'{constant}\s*'
            content = re.sub(usage_pattern, '', content)
        
        # Remove empty lines and extra spaces
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def process_directory(directory: str, constants: list):
    """
    Process all Java files in a directory recursively.
    
    Args:
        directory: Root directory to process
        constants: List of constants to remove
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"Directory {directory} does not exist")
        return
    
    java_files = list(directory_path.rglob('*.java'))
    total_files = len(java_files)
    modified_files = 0
    
    print(f"Found {total_files} Java files to process")
    
    for file_path in java_files:
        if remove_constants(str(file_path), constants):
            modified_files += 1
            print(f"Modified: {file_path}")
    
    print(f"\nProcessing complete:")
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {modified_files}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python remove_constants.py <directory> <constant1> [constant2 ...]")
        print("Example: python remove_constants.py src/main/java PARAM_STR_KPL_LOG_LEVEL_PARAM PARAM_STR_KPL_METRICS_LEVEL_PARAM")
        sys.exit(1)
    
    directory = sys.argv[1]
    constants = sys.argv[2:]
    
    print(f"Removing constants: {', '.join(constants)}")
    print(f"From directory: {directory}")
    
    process_directory(directory, constants)

if __name__ == "__main__":
    main() 