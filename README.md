# Token Counter GUI

A browser-based graphical user interface for the Code Token Counter tool, packaged in Docker for easy deployment.

## Features

- **Web-based Interface**: Access token counting functionality through your browser
- **Directory Browser**: Easily navigate and select directories to analyze
- **Advanced Options**: Exclude tests, documentation, and dependencies
- **Visual Results**: See token usage across different file types and LLM context windows
- **Docker-based**: Easy setup with Docker and Docker Compose

## Quick Start

1. Make sure you have [Docker](https://www.docker.com/products/docker-desktop/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

2. Clone this repository:
   ```bash
   git clone https://github.com/liatrio/codebase-token-counter.git
   cd codebase-token-counter
   ```

3. Navigate to the TokenCounterGui directory:
   ```bash
   cd TokenCounterGui
   ```

4. Build and start the container:
   ```bash
   docker-compose up -d
   ```

5. Open your browser and go to:
   ```
   http://localhost:7654
   ```

## Using the GUI

1. **Navigate Directories**:
   - Use the directory browser on the left to navigate through your file system
   - Double-click on a directory to navigate into it
   - Click on the parent directory (..) to go back
   - Single-click on a directory to select it for analysis

2. **Run Analysis**:
   - Select a directory by clicking on it
   - Click the "Analyze Tokens" button to start the analysis
   - Wait for the results to appear (larger codebases will take longer)

3. **View Results**:
   - See the total token count at the top
   - Browse tokens by file extension
   - Browse tokens by technology/programming language
   - Check how your codebase fits into different LLM context windows

4. **Advanced Options**:
   - Exclude test directories to focus on core code
   - Exclude documentation files
   - Exclude dependency directories like node_modules, venv, etc.

## Customization

### Mounting Different Directories

By default, the application mounts your host's `/mnt/d` directory to `/mnt/projects` in the container. To mount different directories, edit the `docker-compose.yml` file:

```yaml
services:
  token-counter-gui:
    # ... other configuration ...
    volumes:
      - /your/host/path:/mnt/projects:ro  # Change this to your desired path
      # You can add more mount points as needed
```

### Changing the Port

If port 7654 is already in use on your system, you can change it in the `docker-compose.yml` file:

```yaml
services:
  token-counter-gui:
    # ... other configuration ...
    ports:
      - "your-preferred-port:7654"  # Change the first number to your desired port
```

## Troubleshooting

- If you can't access the GUI, make sure the container is running with `docker ps`
- Check the container logs with `docker-compose logs`
- If you get permission errors when analyzing directories, make sure the mounted volumes have proper read permissions

## License

MIT License - Feel free to use and modify as needed.