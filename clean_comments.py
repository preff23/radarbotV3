#!/usr/bin/env python3
import os
import re

def remove_comments_from_file(file_path):
    """Remove comments from Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove docstrings (triple quotes)
            if '"""' in line and line.strip().startswith('"""'):
                continue
            if "'''" in line and line.strip().startswith("'''"):
                continue
            
            # Remove single line comments
            if line.strip().startswith('#'):
                continue
            
            # Remove inline comments (but keep the code part)
            if '#' in line and not line.strip().startswith('#'):
                # Find the # that's not inside a string
                in_string = False
                quote_char = None
                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                            quote_char = None
                    elif char == '#' and not in_string:
                        line = line[:i].rstrip()
                        break
            
            cleaned_lines.append(line)
        
        # Remove empty lines at the beginning and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        cleaned_content = '\n'.join(cleaned_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"Cleaned: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error cleaning {file_path}: {e}")
        return False

def clean_python_files(directory):
    """Clean all Python files in directory."""
    cleaned_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['__pycache__', '.git', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if remove_comments_from_file(file_path):
                    cleaned_count += 1
    
    print(f"Cleaned {cleaned_count} Python files")

if __name__ == "__main__":
    clean_python_files(".")
