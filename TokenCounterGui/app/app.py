import os
import sys
import json
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session

# codebase_token_counter is installed via pip install -e ., no need for sys.path modification
from codebase_token_counter.token_counter import (
    process_repository, format_number, FILE_EXTENSIONS
)

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Define the models and their context windows (Updated per user request May 2025)
LLM_MODELS = {
    "OpenAI": {
        "GPT-4.1 / mini (1M)": 1000000, # Combined as per user table
        "GPT-4o / Turbo (128K)": 128000, # Combined as per user table
    },
    "Anthropic": {
        "Claude 3.7 Sonnet (200K)": 200000,
    },
    "Google": {
        "Gemini 2.5 Pro / Flash (1M)": 1000000, # Combined as per user table
    },
    "Meta": {
        "Llama 4 Scout (10M)": 10000000,
    },
    "Mistral": {
        "Mistral Large 2 (128K)": 128000,
        "Mistral Small 3.1 (128K)": 128000,
        "Mistral NeMo (128K)": 128000,
    },
    "Other": {
        "Cohere Command R+ (128K)": 128000,
        "DBRX Instruct (32K)": 32768,
    }
}

@app.route('/')
def index():
    # Get the mounted volumes for display in the UI
    mounted_volumes = []
    projects_dir = '/mnt/projects'
    if os.path.exists(projects_dir) and os.path.isdir(projects_dir):
        try:
            for item in os.listdir(projects_dir):
                volume_path = os.path.join(projects_dir, item)
                if os.path.isdir(volume_path) and os.access(volume_path, os.R_OK):
                    # Handle display name for the volume
                    # Could be a Windows drive or Linux/Mac directory
                    volume_name = item
                    mounted_volumes.append(volume_name)
        except (PermissionError, OSError):
            pass
    
    # Sort the volume list alphabetically
    mounted_volumes.sort()
    
    return render_template('index.html', models=LLM_MODELS, mounted_drives=mounted_volumes)

@app.route('/get-drives', methods=['GET'])
def get_drives():
    """Get the explicitly mounted volumes in the Docker container"""
    drives = []
    
    # Check the mounted volumes in /mnt/projects
    projects_dir = '/mnt/projects'
    if os.path.exists(projects_dir) and os.path.isdir(projects_dir):
        try:
            for item in os.listdir(projects_dir):
                volume_path = os.path.join(projects_dir, item)
                if os.path.isdir(volume_path) and os.access(volume_path, os.R_OK):
                    # Determine if this might be a Windows drive letter
                    is_win_drive = len(item) == 1 and item.isalpha()
                    
                    # Create a user-friendly name
                    if is_win_drive:
                        display_name = f"{item.upper()}: Drive"
                    else:
                        # For Linux/Mac paths, use the directory name
                        display_name = f"{item}"
                    
                    drives.append({
                        'name': display_name,
                        'path': volume_path,
                        'icon': 'hdd-fill'
                    })
        except (PermissionError, OSError):
            pass
    
    # If no drives found, provide root as fallback
    if not drives and os.path.exists('/') and os.access('/', os.R_OK):
        drives.append({
            'name': 'Root File System',
            'path': '/',
            'icon': 'hdd-rack-fill'
        })
    
    return jsonify(drives)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    path = data.get('directory')
    options = data.get('options', {}) # Get exclusion options

    # Ensure the path exists (process_repository handles file/dir check internally now)
    if not path or not os.path.exists(path):
         return jsonify({'error': f"Path does not exist or is not accessible: {path}"}), 400

    try:
        # Prepare exclusion arguments based on options
        exclude_dirs_set = set()
        exclude_patterns_list = []

        if options.get('excludeTests'):
            # Exclude common test directory names
            exclude_dirs_set.update(['tests', '__tests__', 'test', 'spec', 'specs'])
            # Exclude common test file patterns
            exclude_patterns_list.extend(['*_test.py', 'test_*.py', '*.spec.js', '*.test.js', '*.spec.ts', '*.test.ts'])

        if options.get('excludeDocs'):
            # Exclude common documentation directory names
            exclude_dirs_set.update(['docs', 'documentation', 'doc'])
            # Exclude common documentation file patterns/extensions
            exclude_patterns_list.extend(['*.md', '*.rst', '*.wiki', '*.adoc'])

        if options.get('excludeDependencies'):
            # Exclude common dependency/build artifact directory names/patterns
            # Using path patterns (with '/') to avoid excluding unrelated files/dirs
            exclude_patterns_list.extend([
                'node_modules/',
                'vendor/',
                'packages/',
                'dist/',
                'build/',
                'target/',
                'out/',
                'bin/',
                'obj/',
                '.next/',
                '.nuxt/',
                '.svelte-kit/',
                '.cache/',
                '*.egg-info/',
            ])
            exclude_dirs_set.update(['bower_components']) # Also exclude by name

        # Call the updated process_repository with exclusions
        total_tokens, extension_stats, file_counts = process_repository(
            path,
            exclude_dirs=exclude_dirs_set,
            exclude_patterns=exclude_patterns_list
        )

        # --- Post-processing remains largely the same ---

        # Group results by technology category
        tech_stats = {}
        tech_file_counts = {}
        for ext, count in extension_stats.items():
            tech = FILE_EXTENSIONS.get(ext, "Other")  # Default to "Other" if extension not found
            tech_stats[tech] = tech_stats.get(tech, 0) + count
            tech_file_counts[tech] = tech_file_counts.get(tech, 0) + file_counts[ext]
        
        # Calculate model percentages
        model_percentages = {}
        for category, models in LLM_MODELS.items():
            for model, window in models.items():
                percentage = (total_tokens / window) * 100
                color = "danger" if percentage > 100 else "success"
                model_percentages[model] = {
                    'percentage': round(percentage, 1),
                    'color': color
                }
        
        # Format extensions for display
        formatted_extensions = []
        for ext, count in sorted(extension_stats.items(), key=lambda x: x[1], reverse=True):
            formatted_extensions.append({
                'extension': ext,
                'tokens': count,
                'tokens_formatted': f"{format_number(count)} ({count:,})",
                'files': file_counts[ext],
                'files_text': f"{file_counts[ext]} file{'s' if file_counts[ext] != 1 else ''}"
            })
        
        # Format technologies for display
        formatted_technologies = []
        for tech, count in sorted(tech_stats.items(), key=lambda x: x[1], reverse=True):
            formatted_technologies.append({
                'technology': tech,
                'tokens': count,
                'tokens_formatted': f"{format_number(count)} ({count:,})",
                'files': tech_file_counts[tech],
                'files_text': f"{tech_file_counts[tech]} file{'s' if tech_file_counts[tech] != 1 else ''}"
            })
        
        return jsonify({
            'total_tokens': total_tokens,
            'total_tokens_formatted': f"{format_number(total_tokens)} ({total_tokens:,})",
            'extensions': formatted_extensions,
            'technologies': formatted_technologies,
            'models': model_percentages
        })
    
    except Exception as e:
        return jsonify({
            'error': f"Error analyzing directory: {str(e)}"
        }), 500

@app.route('/browse', methods=['POST'])
def browse_directories():
    data = request.get_json()
    requested_path = data.get('path', '/')
    
    # Normalize path
    current_path = os.path.normpath(requested_path)
    # Ensure it's absolute (should be, but belt-and-suspenders)
    if not os.path.isabs(current_path):
         current_path = os.path.abspath(current_path)

    app.logger.info(f"Browsing requested path: {requested_path}, normalized to: {current_path}") # Logging

    if not os.path.isdir(current_path):
        app.logger.error(f"Path is not a directory: {current_path}") # Logging
        return jsonify({
            'error': f"Path is not a valid directory: {current_path}"
        }), 400
    
    try:
        # Check read access
        if not os.access(current_path, os.R_OK):
             app.logger.error(f"No read access for directory: {current_path}") # Logging
             return jsonify({
                 'error': f"Permission denied: Cannot read directory {current_path}"
             }), 403 # Use 403 Forbidden

        # Get parent directory
        parent_path = os.path.dirname(current_path)
        parent_info = {
            'name': '..',
            'path': parent_path,
            'is_dir': True,
            'is_parent': True
        }
        
        # Get all items in the directory
        items = []
        listed_items = os.listdir(current_path)
        app.logger.info(f"Found {len(listed_items)} items in {current_path}") # Logging
        for item in listed_items:
            full_path = os.path.join(current_path, item)
            # Use try-except for isdir in case of broken symlinks etc.
            try:
                 is_dir = os.path.isdir(full_path)
            except OSError:
                 is_dir = False # Treat inaccessible items as non-directories
                 app.logger.warning(f"Could not determine type for: {full_path}")
            
            # Skip hidden files starting with . (like .git)
            if item.startswith('.'):
                continue
                
            item_info = {
                'name': item,
                'path': full_path,
                'is_dir': is_dir,
                'is_parent': False
            }
            items.append(item_info)
        
        # Sort: directories first, then alphabetically
        items = sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        # Add parent directory at the beginning if we're not at the root
        if current_path != '/':
            items.insert(0, parent_info)
        
        return jsonify({
            'current_path': current_path,
            'items': items,
            'path_parts': current_path.split('/')
        })
    
    except Exception as e:
        return jsonify({
            'error': f"Error browsing directories: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Use Waitress for production
    from waitress import serve
    serve(app, host='0.0.0.0', port=7654)