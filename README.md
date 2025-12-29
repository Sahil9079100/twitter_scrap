# Twitter Scraper

A GUI application to scrape tweets from any Twitter/X profile and generate a PDF report with all collected tweets, images, and video links.

## Features

- 🔐 Automated login to Twitter/X
- 📥 Scrape tweets from any public profile
- 🖼️ Captures images and video links
- 📄 Generates a formatted PDF report
- 💾 Resumable scraping (saves progress)
- 🎨 Dark-themed modern UI

## Requirements

- **Python 3.9+** (for running from source)
- **Google Chrome** installed (for browser automation)
- **Windows 10/11** (for .exe build)

## Quick Start (from source)

```bash
# Clone the repository
git clone <your-repo-url>
cd twitter_scrap

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python panel.py
```

## Building Windows Executable (.exe)

### Prerequisites
- Python 3.9+ installed and in PATH
- Windows 10/11

### Option 1: PowerShell Script (Recommended)

```powershell
# Open PowerShell in project directory
.\build_windows.ps1

# For debug build (shows console window for error messages):
.\build_windows.ps1 -Debug

# To clean previous builds first:
.\build_windows.ps1 -Clean
```

### Option 2: Batch Script

```batch
REM Open Command Prompt in project directory
build_windows.bat

REM For debug build:
build_windows.bat debug

REM To clean first:
build_windows.bat clean
```

### Option 3: Manual Build

```powershell
# Create and activate virtual environment
python -m venv .build_venv
.\.build_venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build using spec file
pyinstaller --clean --noconfirm TwitterScraper.spec

# Or build directly (alternative):
pyinstaller --onefile --windowed --name TwitterScraper panel.py
```

### Build Output

After a successful build:
- **Executable**: `dist/TwitterScraper.exe`
- **Size**: ~50-100 MB (single file)

## Running the Application

### From Source
```bash
python panel.py
```

### From .exe
Double-click `TwitterScraper.exe` or run from terminal:
```batch
.\dist\TwitterScraper.exe
```

## Data Locations

When running as .exe on Windows:

| File | Location |
|------|----------|
| Config | `%APPDATA%\TwitterScraper\data.config.json` |
| Logs | `%APPDATA%\TwitterScraper\scraper_logs.txt` |
| Scraped JSON | `%APPDATA%\TwitterScraper\<username>_mega_scrape.json` |
| PDF Output | User-selected directory |

When running from source, files are saved in the project directory.

## Usage Guide

1. **Launch the application**
2. Click **INITIALIZE** to proceed to the main screen
3. Fill in the fields:
   - **Profile name**: Twitter handle to scrape (without @)
   - **Limit**: Max tweets to fetch (leave empty for all)
   - **Your Username**: Your Twitter login
   - **Your Password**: Your Twitter password
   - **Output Directory**: Where to save the PDF
4. Click **START SCRAPING**
5. Wait for scraping to complete
6. PDF will be generated in your selected directory

## Troubleshooting

### "Chrome failed to start"
- Ensure Google Chrome is installed
- Try running as Administrator

### "Login failed"
- Check your credentials
- Twitter may require CAPTCHA verification — complete it manually in the browser window

### Build errors
- Run with debug flag to see console output: `build_windows.bat debug`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning first: `build_windows.bat clean`

### Missing modules at runtime
If the .exe fails with import errors, add the missing module to `hiddenimports` in `TwitterScraper.spec` and rebuild.

## Project Structure

```
twitter_scrap/
├── panel.py                 # Main GUI application (entry point)
├── twitter_login_scrape.py  # Scraping logic
├── json_to_pdf.py           # PDF generation
├── requirements.txt         # Python dependencies
├── TwitterScraper.spec      # PyInstaller configuration
├── build_windows.ps1        # PowerShell build script
├── build_windows.bat        # Batch build script
└── README.md                # This file
```

## Dependencies

- **customtkinter** - Modern GUI framework
- **selenium** - Browser automation
- **undetected-chromedriver** - Bypass bot detection
- **yt-dlp** - Video URL extraction
- **Pillow** - Image processing
- **reportlab** - PDF generation
- **ijson** - Streaming JSON parser

## License

MIT License - See LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Respect Twitter's Terms of Service and rate limits. The developers are not responsible for any misuse of this software.
