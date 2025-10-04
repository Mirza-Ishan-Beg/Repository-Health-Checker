import FileIO
import sys
import ast
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PYPIChecker import PyPIChecker
from TasksManager import TaskCreator

# Constants
TARGET_FILES_DICTIONARY_KEY = "TARGETS"
TARGET_IMPORTS_DICTIONARY_KEY = "imports"


class ExtractImports:
    def __init__(self):
        pass

    def extract_imports_from_file(self, path: str) -> set:
        """Extract all imported modules from a Python file."""
        imports = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except Exception as e:
            print(f"[ERROR] Can't parse file {path}: {e}")
        return imports

    def get_package_version(self, module_name: str, venv_path: str) -> str:
        """
        Get version of a module inside a virtual environment.
        If pip cannot find it, assume it's a built-in and return Python version.
        """
        python_path = Path(venv_path) / ("Scripts" if sys.platform == 'win32' else 'bin') / "python"
        pip_path = Path(venv_path) / ("Scripts" if sys.platform == 'win32' else 'bin') / 'pip'

        # Try pip show first
        try:
            result = subprocess.run([pip_path, 'show', module_name], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        except Exception as e:
            print(f"[ERROR] Can't fetch version for {module_name} in {venv_path}: {e}")

        # Fallback → assume built-in, get Python version
        try:
            result = subprocess.run([python_path, "--version"], capture_output=True, text=True)
            return result.stdout.strip()  # e.g., "Python 3.13.6"
        except Exception:
            return "built-in (unknown version)"

    def extraction_driller_py(self, targeted_files: dict) -> dict:
        """
        targeted_files: dict of file_path -> {"venv": str or None}
        Returns: dict of file_path -> {"imports": {module: version}, "venv": str}
        """
        modules = {}
        try:
            for file_path, info in targeted_files.items():
                imports_set = self.extract_imports_from_file(file_path)
                venv_path = info.get("venv")
                imports_with_versions = {}

                for mod in imports_set:
                    if venv_path:
                        version = self.get_package_version(mod, venv_path)
                    else:
                        version = "unknown"
                    imports_with_versions[mod] = version

                modules[file_path] = {
                    TARGET_IMPORTS_DICTIONARY_KEY: imports_with_versions,
                    "venv": venv_path
                }
        except Exception as e:
            print(f"[ERROR] Can't filter DataStream: {e}")
        return modules


class CreateDataStream:
    def __init__(self, google_task_service=None):
        self.app = QApplication(sys.argv)
        self.json_obj = FileIO.JSONSetup()
        self.extraction_obj = FileIO.ExtensionsExtractions()
        self.imports_extractor_obj = ExtractImports()
        self.DataStream = {TARGET_FILES_DICTIONARY_KEY: []}
        self.imports_stream = {}
        self.pypi_checker = PyPIChecker()
        self.imports_up_to_date = {}  # booleans comparison
        self.task_manager = TaskCreator(google_task_service) if google_task_service else None

    def execute_extractor(self, amt: int = 1):
        # Save folder selections to JSON
        for _ in range(amt):
            self.extraction_obj.save_folder_extension_to_json("value.json")

        # Load JSON and extract files + venv
        data_dict = self.extraction_obj.JSON_based_files_extraction(
            filename="value.json", extension="py"
        )

        # Build a file_path -> {"venv": str} dictionary
        file_venv_mapping = {}
        for project_root, info in data_dict.items():
            venv_path = str(info.get("venv")) if info.get("venv") else None
            for file_path in info["files"]:
                file_venv_mapping[file_path] = {"venv": venv_path}

        # Flattened file paths for DataStream
        self.DataStream[TARGET_FILES_DICTIONARY_KEY] = list(file_venv_mapping.keys())

        # Extract imports per file and fetch versions
        self.imports_stream = self.imports_extractor_obj.extraction_driller_py(
            targeted_files=file_venv_mapping
        )

        # Booleans for if deprecation per venv is found
        self.imports_up_to_date = self.pypi_checker.compare_with_latest(self.imports_stream)

        # If task manager exists, push tasks to Google Tasks
        if self.task_manager:
            self.task_manager.create_tasks(self.imports_up_to_date)


if __name__ == "__main__":
    # Initialize your Google Tasks service first (auth required)
    google_task_service = None  # Replace this with your authorized Google Tasks API service
    obj = CreateDataStream(google_task_service=google_task_service)
    obj.execute_extractor(amt=1)

    print("Imports with versions per file:")
    print(obj.imports_stream)
    print("\nBooleans indicating up-to-date modules:")
    print(obj.imports_up_to_date)
    obj.app.quit()
