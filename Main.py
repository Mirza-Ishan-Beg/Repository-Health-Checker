import FileIO
import sys
import ast
import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PYPIChecker import PyPIChecker
from TasksManager import TaskCreator
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from development.M_CLI_M import CLI_Menu

# Constants
TARGET_FILES_DICTIONARY_KEY = "TARGETS"
TARGET_IMPORTS_DICTIONARY_KEY = "imports"
SCOPES = ['https://www.googleapis.com/auth/tasks']

def get_google_tasks_service():
    """Automatically load credentials or generate a new token."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("[INFO]       Loaded existing token.json")
    else:
        if not os.path.exists('credentials.json'):
            raise FileNotFoundError(
                "Missing credentials.json — please download it from Google Cloud Console (OAuth Client ID)."
            )
        print("[INFO]       No token.json found, generating one...")
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("[INFO]       token.json generated successfully.")

    return build('tasks', 'v1', credentials=creds)


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
            print(f"[ERROR]     Can't parse file {path}: {e}")
        return imports

    def get_package_version(self, module_name: str, venv_path: str) -> str:
        """
        Get version of a module inside a virtual environment.
        If pip cannot find it, assume it's a built-in and return Python version.
        """
        if not venv_path:
            return "unknown"

        python_path = Path(venv_path) / ("Scripts" if sys.platform == 'win32' else 'bin') / "python"
        pip_path = Path(venv_path) / ("Scripts" if sys.platform == 'win32' else 'bin') / 'pip'

        try:
            result = subprocess.run([str(pip_path), 'show', module_name], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        except Exception as e:
            print(f"[ERROR]     Can't fetch version for {module_name} in {venv_path}: {e}")

        try:
            result = subprocess.run([str(python_path), "--version"], capture_output=True, text=True)
            out = (result.stdout or result.stderr).strip()
            return out or "built-in (unknown version)"
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
            print(f"[ERROR]     Can't filter DataStream: {e}")
        return modules


class CreateDataStream:
    def __init__(self, google_task_service=None):
        self.app = object
        self.json_obj = FileIO.JSONSetup()
        self.extraction_obj = FileIO.ExtensionsExtractions()
        self.imports_extractor_obj = ExtractImports()
        self.DataStream = {TARGET_FILES_DICTIONARY_KEY: []}
        self.imports_stream = {}
        self.pypi_checker = PyPIChecker()
        self.imports_up_to_date = {}  # booleans comparison

        # ALWAYS create TaskCreator so create_tasks gets called; service may be None
        self.task_manager = TaskCreator(google_task_service)

    def execute_JSON_update(self, amt: int = 1) -> None:
        self.app = QApplication(sys.argv)
        for _ in range(amt):
            self.extraction_obj.save_folder_extension_to_json("value.json")
        self.app.quit()
    
    def execute_extrator(self) -> None:
        data_dict = self.extraction_obj.JSON_based_files_extraction(
            filename="value.json", extension="py"
        )

        file_venv_mapping = {}
        for project_root, info in data_dict.items():
            venv_path = str(info.get("venv")) if info.get("venv") else None
            for file_path in info["files"]:
                file_venv_mapping[file_path] = {"venv": venv_path}
        
        self.DataStream[TARGET_FILES_DICTIONARY_KEY] = list(file_venv_mapping.keys())

        self.imports_stream = self.imports_extractor_obj.extraction_driller_py(
            targeted_files=file_venv_mapping
        )

        self.imports_up_to_date = self.pypi_checker.compare_with_latest(self.imports_stream)

        if self.task_manager:
            print(f'[INFO]      running self.task_mananger... object variable right now is as {self.task_manager}')
            self.task_manager.create_tasks(self.imports_up_to_date)


class CLI_CRUD_Operatator:
    def __init__(self, service):
        """
        It is purposed to keep the screens initialization in a format of a dictionary.
        As the CLI module is supposed to represent an question with options to refer to per instance, therefore multiple
        objects of the same module will be created to allow usage accordingly.

        the structure will be as the following dictionary layout:
        {
            "Main menu": {
                "OPT-1 for the choice making": {
                    "OPT-1 for going back" : BACK TO PARENT KEY IN THIS HIERARCHY...
                    "OPT-2 for selecting amount of folders to choose from.": OBJECT 2
                    "OPT-3 for dialog box based selection process.": OBJECT 3
                    }
                "OPT-2 for pure execution": OBJECT 4 <THIS OBJECT IS WHAT WILL RUN CONTINUOUSLY IN THE BACKGROUND...
                "OPT-3 for quitting": DESTROYES THE FINAL OBJECT AND ALL WITHIN HERE...
                }
        }
        """
        self.datastreamer = CreateDataStream(google_task_service=service)
        self.amt_of_dialogs = 1
        self.modulo_cli_obj_dictionary = {}
        self.main_menu = None
        self.opt1 = None
        self.options_builder()
    
    def _set_amt_of_dialogs(self) -> None:
        self.amt_of_dialogs = int(input("Enter amount of dialogs to open: "))
    
    def _return_to_main(self) -> None:
        if self.main_menu:
            print(self.main_menu.opts)
            self.main_menu.option_maker(self.main_menu.opts)
    
    def _destroy_all_menu_nodes(self) -> None:
        self.opt1 = None
        self.main_menu = None
        print("[INFO]     Exiting program...")

    def options_builder(self):
        main_menu_title = "Select what operation you intend to choose, deprecancy health checker:"
        main_menu_subtitle = "PROGRAM BY SEED AND SYNTAX (seedandsyntax@gmail.com)"
        opt1_title = "Select amount of folders and then the directories you want to have depth one scan for python files in:"
        opt1_subtitle = "Do not worry, JSON file uniquely stores and appends as well, to reset everything just delete the value.json..."

        
        self.main_menu = CLI_Menu(
            opts_lists=
            {
                "1. EDIT value.json TO PRE-SELECT WHICH FOLDER'S py FILES TO MONITOR": lambda: CLI_Menu(
                    opts_lists=
                    {
                        "1. ENTER AMOUNT OF DIRECTORIES SELECTION": lambda: self._set_amt_of_dialogs(),
                        "2. OPEN DIALOG FIELD": lambda: self.datastreamer.execute_JSON_update(amt=self.amt_of_dialogs),
                        "q. QUIT THIS OPTION": lambda: self._return_to_main()
                    },
            title=opt1_title,
            sub_title=opt1_subtitle
        ),
                "2. EXECUTE (THIS OPTION CAN BE AUTOMATED TO RUN)": lambda: self.datastreamer.execute_extrator(),
                "q. QUIT THE MODULO MENU...": lambda: self._destroy_all_menu_nodes()
            },
            title=main_menu_title,
            sub_title=main_menu_subtitle
        )

if __name__ == "__main__":
    # Initialize your Google Tasks service first (auth required) if you want real tasks.
    # For testing without Google, leave google_task_service = None so TaskCreator runs debug only.
    service = get_google_tasks_service()
    # obj = CreateDataStream(google_task_service=service)
    # obj.execute_JSON_update(amt=1)
    # obj.execute_extractor()
    obj = CLI_CRUD_Operatator(service=service)

    # obj.app.quit()
