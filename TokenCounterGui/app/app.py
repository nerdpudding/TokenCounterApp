import os
import sys
import json
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session

# Add the parent directory to the path so we can import the token counter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from codebase_token_counter.token_counter import (
    process_repository, format_number, FILE_EXTENSIONS
)

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Define the models and their context windows
LLM_MODELS = {
    "OpenAI": {
        "GPT-3.5 (4K)": 4096,
        "GPT-4 (8K)": 8192,
        "GPT-4 (32K)": 32768,
        "GPT-4 Turbo (128K)": 128000,
    },
    "Anthropic": {
        "Claude 2 (100K)": 100000,
        "Claude 3 Opus (200K)": 200000,
        "Claude 3 Sonnet (200K)": 200000,
        "Claude 3 Haiku (200K)": 200000,
    },
    "Google": {
        "Gemini Pro (32K)": 32768,
        "PaLM 2 (8K)": 8192,
    },
    "Meta": {
        "Llama 2 (4K)": 4096,
        "Code Llama (100K)": 100000,
    },
    "Other": {
        "Mistral Large (32K)": 32768,
        "Mixtral 8x7B (32K)": 32768,
        "Yi-34B (200K)": 200000,
        "Cohere Command (128K)": 128000,
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
    
    # Check if the path is a file or directory
    is_file = os.path.isfile(path)
    is_dir = os.path.isdir(path)
    
    # Ensure the path exists
    if not (is_file or is_dir):
        return jsonify({
            'error': f"Path does not exist: {path}"
        }), 400
    
    try:
        # Process either a single file or a directory
        if is_file:
            # For a single file, we'll create similar output structure as for a directory
            file_extension = os.path.splitext(path)[1].lower().lstrip('.')
            if not file_extension:
                file_extension = 'no_extension'
                
            # Process the individual file
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                token_count = len(content.split())  # Simple token count
                
            # Create the same structure as process_repository but for a single file
            extension_stats = {file_extension: token_count}
            file_counts = {file_extension: 1}
            total_tokens = token_count
        else:
            # Process a directory as before
            total_tokens, extension_stats, file_counts = process_repository(path)
        
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
    current_path = data.get('path', '/')
    
    if not os.path.isdir(current_path):
        return jsonify({
            'error': f"Directory does not exist: {current_path}"
        }), 400
    
    try:
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
        for item in os.listdir(current_path):
            full_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(full_path)
            
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