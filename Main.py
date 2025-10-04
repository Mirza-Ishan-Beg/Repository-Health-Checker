import FileIO
import sys
import ast
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Constants
TARGET_FILES_DICTIONARY_KEY = "TARGETS"
TARGET_IMPORTS_DICTIONARY_KEY = "imports"

class ExtractImports:
    def __init__(self):
        pass

    def extract_imports_from_file(self, path: str) -> set:
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
            print(f"[ERROR]     Can't Parse the python file {path}\nErrortype:\t\t{e}")
        return imports

    def extraction_driller_py(self, TARGETED_FILES: dict) -> dict:
        modules = {TARGET_IMPORTS_DICTIONARY_KEY: {}}
        try:
            for file in TARGETED_FILES[TARGET_FILES_DICTIONARY_KEY]:
                temp_modules = self.extract_imports_from_file(path=file)
                modules[TARGET_IMPORTS_DICTIONARY_KEY][file] = temp_modules
            for file in modules[TARGET_IMPORTS_DICTIONARY_KEY]:
                for import_list in modules[TARGET_IMPORTS_DICTIONARY_KEY][file]:
                    for import_content in import_list:
                        pass

        except Exception as e:
            print(f"[ERROR]     Can't filter through DataStream -> {TARGET_FILES_DICTIONARY_KEY}\nErrortype:\t\t{e}")

class CreateDataStream:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.json_obj = FileIO.JSONSetup()
        self.extraction_obj = FileIO.ExtensionsExtractions()
        self.imports_extractor_obj = ExtractImports()
        self.DataStream = {TARGET_FILES_DICTIONARY_KEY: []}
        self.imports_stream = {TARGET_IMPORTS_DICTIONARY_KEY: set()}

    def execute_extractor(self, amt: int = 1):
        for i in range(amt):
            self.extraction_obj.save_folder_extension_to_json("value.json")
        data_dict = self.extraction_obj.JSON_based_files_extraction(filename="value.json", extension="py")
        print(data_dict)
        print("\n\n==============================\n")
        for i in data_dict:
            for j in data_dict[i]:
                # print(j)
                print("\n=============\n", j, "\n=============")
                self.DataStream[TARGET_FILES_DICTIONARY_KEY].append(j.strip())
        self.imports_stream = self.imports_extractor_obj.extraction_driller_py(TARGETED_FILES=self.DataStream)
        

if __name__ == "__main__":
    obj1 = CreateDataStream()
    obj1.execute_extractor(amt = 2)
    print(obj1.DataStream)  # DATA STREAM IN DICTIONARY FORMAT IS DONE, NOW USE THE PATHS EXTRACTED OF PY FILES TO SEARCH THEIR IMPORTS AND THE VERSIONS WITH PIP IF POSSIBLE...
    obj1.app.quit()
