# WeebCentral Manga Downloader

A powerful and efficient Python script for downloading manga from WeebCentral, designed for ease of use, performance, and flexibility.

This script allows you to search for manga, download specific chapters, resume downloads, and archive chapters into `.cbz` or `.zip` formats. It features parallel image downloading, robust error handling, and rate-limiting to ensure smooth and reliable operation.

## Features

- **Manga Search**: Find manga by title or use a direct series ID.
- **Chapter Selection**: Download all chapters, specific chapters, or only new chapters since your last download.
- **High-Speed Downloads**: Utilizes parallel image downloading to significantly speed up the process.
- **Sequential Mode**: Option to download images one by one for sites that are sensitive to high traffic.
- **Flexible Archiving**: Save chapters as `.cbz` (default) or `.zip` archives.
- **Bulk Processing**: Download multiple series at once from a text file.
- **Smart Resuming**: Automatically detect the last downloaded chapter and continue from there.
- **Error Handling**: Robust error handling and retry mechanisms for network issues.
- **Rate-Limiting**: Avoids overwhelming the server by pausing between chapter downloads.
- **Verbose Logging**: Optional detailed output for debugging and monitoring.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/weebcentral-dl.git
    cd weebcentral-dl
    ```

2.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script is controlled via command-line arguments, offering a wide range of options to customize your downloads.

### Basic Syntax

```bash
python main.py [query] [options]
```

### Command-Line Arguments

| Argument              | Short | Description                                                                                                 |
| --------------------- | ----- | ----------------------------------------------------------------------------------------------------------- |
| `query`               |       | The title of the manga to search for (e.g., `"Solo Leveling"`). Ignored if using `--bulk` or `--series-id`.      |
| `--chapter`           | `-c`  | Download specific chapters, separated by commas (e.g., `12,14.5,16`).                                       |
| `--output`            | `-o`  | The directory where downloaded manga will be saved. Defaults to `./manga_downloads`.                       |
| `--latest`            | `-l`  | Download only chapters newer than the latest one found in the output directory.                             |
| `--zip`               | `-z`  | Archive chapters as `.zip` files instead of the default `.cbz` format.                                      |
| `--verbose`           | `-v`  | Enable verbose logging for detailed debug output.                                                           |
| `--bulk`              | `-b`  | Path to a text file containing manga titles or series IDs (one per line).                                   |
| `--sequence`          | `-s`  | Disable parallel downloading and download images sequentially.                                              |
| `--rlc`               |       | The number of chapters to download before pausing for rate-limiting. Defaults to `10`.                      |
| `--max-sleep`         |       | The maximum time (in seconds) to sleep for rate-limiting or retries. Defaults to `120`.                   |
| `--max-retries`       |       | The maximum number of times to retry downloading a failed image. Defaults to `5`.                           |
| `--series-id`         | `-id` | Bypass the search and download directly using a WeebCentral series ID.                                      |

--- 

### Examples

1.  **Download all chapters of a manga:**

    ```bash
    python main.py "Wistoria: Wand and Sword"
    ```

2.  **Download specific chapters:**

    ```bash
    python main.py "Kagurabachi" -c 1,2,3.5
    ```

3.  **Resume downloading from the latest chapter and save as `.zip`:**

    ```bash
    python main.py "Sakamoto Days" -l -z
    ```

4.  **Download a manga using its series ID:**

    ```bash
    python main.py -id 01J76XYFM1TWGNNQ2Y2T8V7E8Y
    ```

5.  **Bulk download from a text file:**

    Create a file named `manga_list.txt` with the following content:

    ```
    One-Punch Man
    01H9S3T35N14MQR314X4J1V4B1 # Jujutsu Kaisen
    My Hero Academia
    ```

    Then run the script:

    ```bash
    python main.py -b manga_list.txt
    ```

### Output Structure

By default, the script organizes downloaded chapters into the following structure:

```
manga_downloads/
└── [manga-title]/
    ├── [manga-title]-[chapter_number].cbz
    ├── [manga-title]-[chapter_number].cbz
    └── ...
```

If the `--zip` flag is used, the output will be:

```
manga_downloads/
└── [manga-title]/
    ├── vol_[chapter_number].zip
    ├── vol_[chapter_number].zip
    └── ...
```

## Code Structure

The project is organized into three main files to ensure clarity and maintainability:

-   **`main.py`**: Handles command-line argument parsing and orchestrates the download process.
-   **`downloader.py`**: Contains the `WeebCentralDownloader` class, which encapsulates all the core logic for searching, fetching, and downloading.
-   **`utils.py`**: A collection of helper functions for tasks like sanitizing filenames and formatting chapter names.