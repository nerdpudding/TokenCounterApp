# Token Counter GUI

A simple web-based GUI for analyzing code repository token counts, built using Flask and Docker.

This tool provides a user-friendly interface on top of the `codebase-token-counter` command-line tool.

**Credits:** The underlying token counting logic is based on the [liatrio/codebase-token-counter](https://github.com/liatrio/codebase-token-counter) project. This GUI version packages that logic with a web interface.

---

## Table of Contents
- [Token Counter GUI](#token-counter-gui)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Setup and Run](#setup-and-run)
  - [How to Use](#how-to-use)
  - [Stopping the Application](#stopping-the-application)
  - [docker-compose down](#docker-compose-down)
  - [License](#license)

---
## Features

-   **Web Interface:** Easy analysis via your browser.
-   **File Browser:** Navigate mounted drives to select projects.
-   **Exclusion Options:** Attempt to exclude test, documentation, or dependency files/folders.
-   **Visual Results:** View total tokens, breakdown by file type, and LLM context window comparisons.

## Setup and Run

1.  **Prerequisites:** Ensure you have [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose installed.

2.  **Clone:** Clone this repository:
    ```bash
    # Replace with the actual URL of YOUR repository if different
    git clone <your-repository-url>
    cd TokenCounterApp
    ```

3.  **Configure Mounts (Optional):**
    -   Edit `docker-compose.yml`.
    -   Modify the `volumes:` section to mount the host directories you want to analyze into `/mnt/projects` inside the container. Examples are provided for Windows, Linux, and Mac. Ensure the host paths exist.
    ```yaml
    volumes:
      # Example: Mount Windows D: drive
      - d:/:/mnt/projects/d:ro
      # Example: Mount Linux home
      # - /home:/mnt/projects/home:ro
      # Add other drives/directories as needed
    ```

4.  **Build and Run:** From the `TokenCounterApp` directory, run:
    ```bash
    # Build the Docker image
    docker-compose build

    # Start the container in the background
    docker-compose up -d
    ```

5.  **Access:** Open your web browser and navigate to:
    ```
    http://localhost:7654
    ```
    *(If you changed the port in `docker-compose.yml`, use your chosen port instead of 7654)*

## How to Use

1.  **Select Drive:** Click the "Mounted Drives" button. Choose the drive/volume containing your project.
2.  **Browse:** Click folders in the browser panel to navigate to your desired project directory or file.
3.  **Select:** Clicking a folder or file automatically selects it for analysis (its path appears in the "Selected Project Directory" field).
4.  **Advanced Options (Optional):** Toggle the switches to exclude tests, documentation, or dependencies. *(Note: Exclusion logic is based on common patterns and might not be perfect for all project structures).*
5.  **Analyze:** Click the "Analyze Token Count" button.
6.  **View Results:** The analysis results will appear on the right side.

## Stopping the Application

```bash
docker-compose down
---

## License

MIT License - Feel free to use and modify as needed.