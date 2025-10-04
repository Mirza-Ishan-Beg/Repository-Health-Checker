# TasksManager.py

from pathlib import Path
from datetime import datetime, timedelta

class TaskCreator:
    def __init__(self, service):
        """
        service: an authorized Google Tasks API service object
        """
        self.service = service

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
        """
        if not self.service:
            print("ERROR:       NO SERVICE!!!")
            return  # No service provided

        for file_path, file_info in imports_up_to_date.items():
            project_root = Path(file_info["venv"]).parent if file_info.get("venv") else "Unknown"
            folder_name = project_root.name if project_root != "Unknown" else "Unknown"

            for module_name, status in file_info["imports"].items():
                # Task 1: Deprecancy Potency
                if status is False or status is None:
                    title = f"Module {module_name} Deprecancy Potency"
                    notes = f"Check {module_name} within {folder_name}, it can be found in {project_root}."
                    task_body = self._create_task_body(title, notes)
                    self.service.tasks().insert(tasklist='@default', body=task_body).execute()
                    print(f"TASK TYPE 1: {title}")

                # Task 2: Doc Deprecated
                if status is None:
                    title = f"Module {module_name} Doc Deprecated"
                    notes = f"Check PyPI doc for availability of {module_name} of project {folder_name}, it can be found in {project_root}. Documentation may no longer exist."
                    task_body = self._create_task_body(title, notes)
                    self.service.tasks().insert(tasklist='@default', body=task_body).execute()
                    print(f"TASK TYPE 2: {title}")
