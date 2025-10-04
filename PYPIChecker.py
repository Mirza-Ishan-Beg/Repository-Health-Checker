import requests
from packaging import version

class PyPIChecker:
    def __init__(self):
        # Optionally cache results to avoid repeated API calls
        self.latest_versions_cache = {}

    def get_latest_version(self, package_name: str) -> str:
        """
        Query PyPI to get the latest version of a package.
        """
        if package_name in self.latest_versions_cache:
            return self.latest_versions_cache[package_name]

        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest = data['info']['version']
                self.latest_versions_cache[package_name] = latest
                return latest
        except Exception as e:
            print(f"[ERROR] Could not fetch latest version for {package_name}: {e}")
        return None  # Unknown or error

    def compare_with_latest(self, module_version_dict: dict) -> dict:
        """
        Input structure (same as imports_stream):
        {
            "file.py": {
                "imports": {"os": "Python 3.13.6", "requests": "2.31.0"},
                "venv": "C:/Projects/ProjectA/venv"
            }
        }
        
        Returns same structure, but values are booleans:
        True  -> module is up-to-date
        False -> module is outdated
        """
        comparison_dict = {}
        for file_path, file_info in module_version_dict.items():
            comparison_dict[file_path] = {"imports": {}, "venv": file_info.get("venv")}
            for mod, ver in file_info["imports"].items():
                # Skip built-ins (they have "Python X.Y.Z")
                if ver.startswith("Python"):
                    comparison_dict[file_path]["imports"][mod] = True
                    continue

                latest_ver = self.get_latest_version(mod)
                if latest_ver is None:
                    # Can't determine latest, mark as None to avoid false alarms
                    comparison_dict[file_path]["imports"][mod] = None
                    continue

                try:
                    comparison_dict[file_path]["imports"][mod] = version.parse(ver) >= version.parse(latest_ver)
                except Exception:
                    comparison_dict[file_path]["imports"][mod] = False  # fallback
        return comparison_dict
