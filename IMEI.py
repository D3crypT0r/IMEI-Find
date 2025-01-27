import subprocess
import json
import sys


try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyqt5-tools"])
    os.execv(sys.executable, [sys.executable] + sys.argv)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QFileDialog, QLabel, QWidget, QProgressBar, QTableWidget, QTableWidgetItem, QMenuBar, QAction, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal


class PartitionFetcher(QThread):
    log_message = pyqtSignal(str)
    partitions_fetched = pyqtSignal(list)

    def run(self):
        self.log_message.emit("Fetching mounted partitions...")
        try:
            command = "adb shell cat /proc/mounts"
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                partitions = result.stdout.strip().split("\n")
                parsed_partitions = [line.split() for line in partitions]
                self.partitions_fetched.emit(parsed_partitions)
            else:
                self.log_message.emit(f"Error: {result.stderr}")
        except Exception as e:
            self.log_message.emit(f"Error fetching partitions: {e}")


class ADBCommandExecutor(QThread):
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str)
    partial_results = pyqtSignal(str, str, str) 
    finished = pyqtSignal(dict)

    def __init__(self, terms, directories):
        super().__init__()
        self.terms = terms
        self.directories = directories
        self.results = {}

    def run(self):
        total_tasks = len(self.terms) * len(self.directories)
        completed_tasks = 0

        self.log_message.emit("Connecting to ADB in root mode...")
        root_result = subprocess.run(["adb", "root"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "adbd is already running as root" not in root_result.stdout:
            self.log_message.emit("Error: Failed to get root access via ADB.")
            return

        self.log_message.emit("Entering root shell...")
        try:
            shell_test = subprocess.run(["adb", "shell", "echo 'root access confirmed'"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "root access confirmed" not in shell_test.stdout:
                self.log_message.emit("Error: Failed to access root shell.")
                return
        except Exception as e:
            self.log_message.emit(f"Error entering root shell: {str(e)}")
            return

        for directory in self.directories:
            self.results[directory] = {}
            for term in self.terms:
                try:
                    self.log_message.emit(f"Searching for '{term}' in {directory}...")
                    command = f"adb shell 'grep -ri \"{term}\" {directory}'"
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        self.partial_results.emit(directory, term, line.strip())
                        self.results.setdefault(directory, {}).setdefault(term, []).append(line.strip())

                    process.wait()
                except Exception as e:
                    self.results[directory][term] = [f"Execution error: {str(e)}"]
                completed_tasks += 1
                self.progress.emit(int((completed_tasks / total_tasks) * 100))

        self.finished.emit(self.results)


class IMEIFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMEI Finder and Patcher")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QPushButton { padding: 10px; border-radius: 5px; color: white; background-color: #3b3b3b; }
            QPushButton:hover { background-color: #5a5a5a; }
            QTableWidget { border: 1px solid #555; background-color: #2e2e2e; color: white; }
            QTextEdit { background-color: #2e2e2e; color: #90ee90; border: 1px solid #555; }
            QLineEdit { background-color: #2e2e2e; color: white; border: 1px solid #555; }
            QLabel { color: white; font-size: 14px; }
            QProgressBar { text-align: center; color: white; background-color: #3b3b3b; border: 1px solid #555; }
        """)

        self.initUI()
        self.output_data = {}

    def initUI(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.search_label = QLabel("Search terms (comma-separated):")
        left_layout.addWidget(self.search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Example: IMEI, getImei, NVD_IMEI")
        left_layout.addWidget(self.search_input)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Directory", "Term", "Result"])
        left_layout.addWidget(self.results_table)

        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)

        self.search_button = QPushButton("🔍 Search")
        self.search_button.clicked.connect(self.start_search)
        left_layout.addWidget(self.search_button)

        self.export_button = QPushButton("📁 Export Results")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_to_json)
        left_layout.addWidget(self.export_button)

        self.log_output = QTextEdit()
        left_layout.addWidget(self.log_output)

        right_layout = QVBoxLayout()
        self.partition_table = QTableWidget(0, 4)
        self.partition_table.setHorizontalHeaderLabels(["Source", "Mount Point", "Type", "Options"])
        right_layout.addWidget(self.partition_table)

        self.fetch_partitions_button = QPushButton("🗂️ Show Mounted Partitions")
        self.fetch_partitions_button.clicked.connect(self.fetch_partitions)
        right_layout.addWidget(self.fetch_partitions_button)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def log(self, message):
        self.log_output.append(message)

    def fetch_partitions(self):
        self.log("Fetching mounted partitions...")
        self.partition_fetcher = PartitionFetcher()
        self.partition_fetcher.log_message.connect(self.log)
        self.partition_fetcher.partitions_fetched.connect(self.display_partitions)
        self.partition_fetcher.start()

    def display_partitions(self, partitions):
        self.partition_table.setRowCount(0)
        for partition in partitions:
            if len(partition) >= 4:
                row_position = self.partition_table.rowCount()
                self.partition_table.insertRow(row_position)
                for col, value in enumerate(partition[:4]):
                    self.partition_table.setItem(row_position, col, QTableWidgetItem(value))

    def start_search(self):
        self.results_table.setRowCount(0)
        self.output_data = {}

        search_terms = [term.strip() for term in self.search_input.text().split(",")]
        directories = ["/system", "system_root", "/vendor", "/efs", "/cache", "/product"]
        self.worker = ADBCommandExecutor(search_terms, directories)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.log)
        self.worker.partial_results.connect(self.add_result_row)
        self.worker.finished.connect(self.finalize_results)
        self.worker.start()

    def add_result_row(self, directory, term, match):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        self.results_table.setItem(row_position, 0, QTableWidgetItem(directory))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(term))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(match))

    def finalize_results(self, results):
        self.output_data = results
        self.log("Search completed.")
        self.export_button.setEnabled(True)

    def export_to_json(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Results", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, "w") as json_file:
                    json.dump(self.output_data, json_file, indent=4)
                self.log(f"Results exported successfully to {file_name}")
            except Exception as e:
                self.log(f"Export error: {e}")


if __name__ == "__main__":
    app = QApplication([])
    window = IMEIFinderApp()
    window.show()
    app.exec_()
