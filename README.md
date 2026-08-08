# PencilTrace

PencilTrace is a modern, unified Optical Mark Recognition (OMR) software. It merges the robust and accurate computer vision pipeline of [OMRChecker](https://github.com/Udayraj123/OMRChecker) with a sleek, user-friendly graphical interface inspired by [open-mcr](https://github.com/iansan5653/open-mcr).

## Features

- 📁 **Batch Processing Dashboard**: Easily select entire folders of scanned exams and process them in bulk.
- ✏️ **Visual Template Creator**: Upload a blank sheet and draw bounding boxes directly on the image to generate custom JSON layouts without writing a single line of code.
- 📊 **Results & Analytics**: View your graded results in a clean, modern data table with CSV export capabilities.
- 🚀 **Fast & Accurate**: Powered by OpenCV and the highly accurate OMRChecker core engine.
- 💻 **Standalone Executable**: Built with a FastAPI backend and packaged using PyInstaller, it runs entirely offline as a local web application.

## Prerequisites

If you are running the application from the source code, you will need:
- Python 3.8+
- pip

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/PencilTrace.git
   cd PencilTrace
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running Locally

To start the local server and open the web dashboard:
```bash
python backend/app.py
```
Your default web browser will automatically open to `http://127.0.0.1:8000`.

### Building for Distribution (Windows)

To package the entire application into a standalone executable that doesn't require Python to be installed on the host machine:
```bash
python build.py
```
The compiled executable will be located in the `dist/PencilTrace` folder.

## License

This project incorporates the computer vision engine of [OMRChecker](https://github.com/Udayraj123/OMRChecker) (MIT License) and concepts from [open-mcr](https://github.com/iansan5653/open-mcr) (GPL-3.0 License).
