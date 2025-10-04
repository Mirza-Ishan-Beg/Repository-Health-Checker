import subprocess
import sys
import platform
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from development.M_CLI_M import CLI_Menu

# CONSTANTS
FOLDERS_DICTIONARY_STRING = "folder_destination"

class DependencyChecker:
    def __init__(self):
        pass

    def _works_with_this_os(self) -> bool:
        current_os = platform.system()
        if current_os in ("Windows", "Linux"):
            return True
        else: return False

    
class JSONSetup:
    # This will be responsible for a dictionary getting parsed.
    """
    DATA FORMAT:
    {
        "extension": [list of files],
        "py": ["C:/user/documents/pythonic.py"]
    }
    
    OR

    {
        FOLDERS_DICTIONARY_STRING: [list of folders]        
    }
    """
    def __init__(self):
        pass

    def write_JSON(self, data: dict, filename: str) -> None:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def read_JSON(self, filename: str) -> dict:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    
    def append_JSON(self, data: dict, filename: str) -> None:
        existing_data = self.read_JSON(filename=filename)
        print(existing_data)
        print(data)
        for i in existing_data:
            if existing_data[i]:
                existing_data[i].extend(data[i])
                existing_data[i] = list(set(existing_data[i]))
            else:
                existing_data[i] = data[i]
        self.write_JSON(existing_data, filename=filename)


class ExtensionsExtractions(JSONSetup, DependencyChecker):
    def __init__(self):
        pass

    def find_venv(self, project_root, venv_names=("venv", ".venv", "env", ".env")) -> str:
        current = Path(project_root).resolve()
        root = current.anchor

        while True:
            for name in venv_names:
                candidate = current / name / "pyvenv.cfg"
                if candidate.exists():
                    return current / name  # return folder, not file
            if current == Path(root):
                raise ValueError(f"[ERROR] The folder {project_root} is not part of a venv/evn project!")
            current = current.parent

    def folder_dialog_opener(self, custom_title: str =  "Select Python Projects Folder") -> str:
        fileName = QFileDialog.getExistingDirectory(None, custom_title)
        return fileName
    
    def save_folder_extension_to_json(self, json_filename: str) -> None:
        filename_to_save = self.folder_dialog_opener(custom_title="Save which folder extension?")
        print(json_filename)
        json_path = Path(json_filename)
        if json_path.exists():
            self.append_JSON(
                filename=json_filename,
                data={FOLDERS_DICTIONARY_STRING: [filename_to_save]}
                )
            print(f"[SUCCESS] APPENDED DATA TO JSON FILE {json_filename}")
        else:
            self.write_JSON(
                data={FOLDERS_DICTIONARY_STRING: [filename_to_save]},
                filename=json_filename
            )
            print(f"[SUCCESS] WRITTEN JSON AS {json_filename}")
    
    def direct_file_path_extraction(self, path: str, extension: str) -> list:
        if not self._works_with_this_os:
            print(f"[OS FAILURE]    We do not support this OS, only Windows and Linux for now...")
            return []
        cmd = ""
        
        if platform.system() == "Windows":
            cmd = f'powershell -Command "Get-ChildItem -Path \'{path}\' -Filter *.{extension} | ForEach-Object {{ $_.FullName }}"'
        elif platform.system() == "Linux":
            cmd = f'find {path} -type f -name "*.{extension}"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        files = result.stdout.strip().split('\n') if result.returncode == 0 else []

        return files
    
    def JSON_based_files_extraction(self, filename: str, extension: str) -> dict:
        data = self.read_JSON(filename=filename)
        projects = {}
        print(data)
        for path_to_folder in data[FOLDERS_DICTIONARY_STRING]:
            print("\n\nJSON_based_imports_extraction SAYS: ", path_to_folder)
            files_list = self.direct_file_path_extraction(path=path_to_folder, extension=extension)
            try:
                venv_path = self.find_venv(project_root=path_to_folder)
            except ValueError:
                venv_path = None

            projects[path_to_folder] = {
                "files": files_list,
                "venv": venv_path
            }
        return projects

if __name__ == "__main__":
    app = QApplication(sys.argv)

    EE_obj = ExtensionsExtractions()
    # path_to_folder = EE_obj.folder_dialog_opener()
    # print(path_to_folder)
    # py_files = EE_obj.direct_file_path_extraction(path=path_to_folder, extension="py")
    # print('python files:')    

    # for i in py_files:
    #     print(i)
    for i in range(3):
        EE_obj.save_folder_extension_to_json("value.json")

    data_dict = EE_obj.JSON_based_files_extraction(filename="value.json", extension="py")
    print(data_dict)
    print("\n\n==============================\n")
    for i in data_dict:
        for j in data_dict[i]:
            print(j)
    
    CLI_obj = CLI_Menu()

    app.quit()
