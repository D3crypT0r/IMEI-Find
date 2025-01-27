# IMEI-Find
Finder &amp; Patcher

Here is the README.md file for your program:

# IMEI Finder and Patcher

A GUI-based tool to search for specific terms (like `IMEI`) within an Android device's file system using ADB (Android Debug Bridge). The tool can also fetch mounted partitions and export search results for further analysis.

## Features
- **Search for Terms**: Search for specific terms (e.g., `IMEI`, `getImei`) across multiple directories on a connected Android device.
- **Fetch Mounted Partitions**: Display mounted partitions of the connected device for detailed analysis.
- **Progress Monitoring**: Track the progress of search operations with a visual progress bar.
- **Live Logging**: Display real-time logs for debugging and tracking the application's activity.
- **Export Results**: Export search results as a JSON file for later reference.

## Prerequisites
- **Python 3.x** installed on your system.
- **ADB (Android Debug Bridge)** installed and configured in your system's PATH.
- **PyQt5** for the graphical user interface.

## Installation
1. Clone the repository or download the script:
   ```bash
   git clone https://github.com/D3crypT0r/IMEI-Find.git
   cd IMEI-Find

2. Install the required Python packages:

pip install PyQt5 pyqt5-tools


3. Ensure ADB is properly installed and configured:

Follow ADB installation instructions.


Usage

1. Connect your Android device to your computer via USB.


2. Ensure ADB is enabled on the device:

Enable Developer Options on the phone.

Enable USB Debugging.



3. Run the script:

python imei_finder.py


4. Features available in the tool:

Fetch Mounted Partitions: Click "🗂️ Show Mounted Partitions" to view a list of partitions.

Search for Terms:

1. Enter comma-separated search terms (e.g., IMEI, getImei, NVD_IMEI) in the input field.


2. Click "🔍 Search" to start searching for terms in predefined directories.



Export Results: Click "📁 Export Results" to save search results as a JSON file.




Supported Directories

The tool searches the following directories by default:

/system

/system_root

/vendor

/efs

/cache

/product


Limitations
The program requires ADB access and physical or local network connectivity to the Android device.

It cannot track phones or access IMEI-related data remotely via networks.

IMEI tracking is beyond the scope of this program; it is limited to searching device files.


Legal Disclaimer
This tool is for educational and debugging purposes only. Unauthorized use of this program, such as accessing data on devices without permission, is illegal. The authors are not responsible for misuse of the tool.
