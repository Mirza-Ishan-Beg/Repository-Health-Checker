import sys
import platform
import socket
from pathlib import Path
from datetime import datetime, timedelta

class TaskCreator:
    def __init__(self, service=None):
        """
        service: an authorized Google Tasks API service object (or None)
        """
        self.service = service
    
    def get_machine_specs(self) -> str:
        try:
            system = platform.system()
            release = platform.release()
            hostname = socket.gethostname()
            pyver = f"[SYSTEM] Python {sys.version_info.major}.{sys.version_info.minor}"
            return f"{system}-{release} | {hostname} | {pyver}"
        except Exception as e:
            return f"Unknown-System | Unknown-Host | Unknown-python.verson | Error: {e}"
        
    def task_exists(self, module_name: str, machine_sig: str, project_dir: str, status: bool) -> bool:
        if status:
            print(f"[INFO]       {module_name}, {machine_sig} does not need a warn this time\n\nPROJECT DIRECTORY: {project_dir}\nSTATUS: {status}")
            return True
        if not self.service:
            print("[DEBUG]      task_exists() called without service, skipping check and returning False.")
            return False
        try:
            results = self.service.tasks().list(tasklist='@default').execute()
            tasks = results.get("items", [])
        except Exception as e:
            print("[ERROR]      Failed to fetch tasks: {e}")
            return False
        
        for task in tasks:
            title = task.get("title", "")
            notes = task.get("notes", "")
            if (
                module_name in title and
                machine_sig in notes and
                project_dir in notes and 
                module_name in notes
            ):
                print(f'[DEBUG]     Task already exists for {module_name} on {machine_sig} within project {project_dir}\n')
                return True
        print(f"[DEBUG]      Task does not exist for this one and new will be created for\n1. module name {module_name}\n2. {machine_sig}\n3. {project_dir}\n")
        return False

    def _create_task_body(self, title: str, notes: str, due_hours: int = 6):
        """
        Generates the body for a Google Task
        """
        due_time = datetime.utcnow() + timedelta(hours=due_hours)
        due_rfc3339 = due_time.isoformat() + "Z"  # RFC3339 UTC timestamp

        return {
            "title": title,
            "notes": notes,
            "due": due_rfc3339
        }

    def create_tasks(self, imports_up_to_date: dict):
        """
        Generate Google Tasks based on module deprecation and documentation status.
        This will always run its debug/print logic. If a real `service` is provided,
        it will call the API; otherwise it prints the same TASK TYPE lines so your
        debug flow remains visible.
        """
        if not imports_up_to_date:
            print("[DEBUG]      imports_up_to_date is empty, nothing to do.")
            return

        # If no service, print an error once but continue to run debug loop
        if not self.service:
            print("[ERROR]      NO SERVICE!!! (continuing in debug-only mode)")

        machine_sig = self.get_machine_specs()

        for file_path, file_info in imports_up_to_date.items():
            project_root = Path(file_info["venv"]).parent if file_info.get("venv") else "Unknown"
            folder_name = project_root.name if project_root != "Unknown" else "Unknown"
            print(f"[DEBUG]     {file_path}, {file_info}, {project_root}, {folder_name}, inside the create_task...")

            for module_name, status in file_info["imports"].items():
                print(f"[DEBUG]     {module_name}, {status}, inside the create_task...")

                if self.task_exists(module_name=module_name, machine_sig=machine_sig, project_dir=str(project_root), status=status):
                    print(f'[INFO]      Skipping the warn for:\n1. {module_name}\n2. {machine_sig}\n3. {project_root}')
                    continue

                # Task 1: Deprecancy Potency
                if status is False:
                    title = f"Module {module_name} Deprecancy Potency"
                    notes = (
                        f"Check module {module_name} within {folder_name}, it can be found in {project_root}."
                        f"\nCritical Info of location:\n"
                        f"\n1.  {module_name}"
                        f"\n2.  {project_root}"
                        f"\n3.  {machine_sig}"
                        )
                    task_body = self._create_task_body(title, notes)
                    # send only if service exists
                    if self.service:
                        try:
                            self.service.tasks().insert(tasklist='@default', body=task_body).execute()
                        except Exception as e:
                            print(f"[ERROR]     Failed to create task '{title}': {e}")
                    # Always print TASK TYPE line so debug output remains the same
                    print(f"TASK TYPE 1: {title}")

                # Task 2: Doc Deprecated
                if status is None:
                    title = f"Module {module_name} Doc Deprecated"
                    notes = (
                        f"Check PyPI doc for availability of {module_name} in project {folder_name}.\n"
                        f"Located at {project_root}. Documentation may no longer exist.\n"
                        f"\nCritical Info of location:\n"
                        f"\n1.  {module_name}"
                        f"\n2.  {project_root}"
                        f"\n3.  {machine_sig}"
                        )
                    task_body = self._create_task_body(title, notes)
                    if self.service:
                        try:
                            self.service.tasks().insert(tasklist='@default', body=task_body).execute()
                        except Exception as e:
                            print(f"[ERROR]     Failed to create task '{title}': {e}")
                    print(f"TASK TYPE 2: {title}")
