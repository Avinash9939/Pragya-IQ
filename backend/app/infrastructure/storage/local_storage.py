import os
from pathlib import Path

class LocalStorage:
    """
    Local filesystem storage manager for saving and retrieving dataset files.
    Why: Handles file persistence inside an isolated 'storage/' workspace directory.
    """
    def __init__(self, base_dir: str = "storage") -> None:
        # If running from the root directory that contains 'backend',
        # point base_dir to 'backend/storage' to share files between frontend and backend.
        if base_dir == "storage" and os.path.exists("backend/storage"):
            self.base_dir = Path("backend/storage")
        else:
            self.base_dir = Path(base_dir)

    def save(self, user_id: int, dataset_id: int, filename: str, content: bytes) -> str:
        """
        Saves user-uploaded file content to the local filesystem.
        Why: Isolates dataset uploads by user ID and prefixing with dataset ID to avoid naming overrides.
        """
        user_dir = self.base_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        target_filename = f"{dataset_id}_{filename}"
        target_path = user_dir / target_filename
        with open(target_path, "wb") as f:
            f.write(content)

        return str(target_path)

    def get_path(self, storage_path: str) -> str:
        """
        Retrieve clean path of dataset file.
        Why: Translates database storage paths using fallbacks for root directory and legacy paths.
        """
        path_str = str(storage_path).replace("\\", "/")
        
        # 1. Direct resolve
        resolved_path = Path(storage_path).resolve()
        if resolved_path.exists() and resolved_path.is_file():
            return str(resolved_path)

        # 2. Map storage/ -> backend/storage/ (cwd alignment fallback)
        if path_str.startswith("storage/"):
            modified_path = path_str.replace("storage/", "backend/storage/", 1)
            resolved_mod = Path(modified_path).resolve()
            if resolved_mod.exists() and resolved_mod.is_file():
                return str(resolved_mod)

            # 3. Legacy C:/Project/backend/storage/ fallback
            legacy_path = Path("C:/Project/backend") / path_str
            if legacy_path.exists() and legacy_path.is_file():
                return str(legacy_path)

        return str(resolved_path)
