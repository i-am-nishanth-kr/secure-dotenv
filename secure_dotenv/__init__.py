import os
import warnings
from pathlib import Path
from .core import get_project_secrets, parse_env_file

def load_dotenv(dotenv_path=".env", override=False, **kwargs):
    project_root = Path.cwd()
    env_path = project_root / dotenv_path
    id_file = project_root / ".secure-env-id"
    
    if not id_file.exists():
        return # Standard behavior if not initialized
        
    project_id = id_file.read_text().strip()
    
    # 1. Perform Migration/Sync automatically
    if env_path.exists():
        from .core import migrate_and_clear_env
        migrate_and_clear_env(str(env_path), project_id)
        
    # 2. Load into memory from Vault
    secrets = get_project_secrets(project_id, Path(dotenv_path).name)
    for key, value in secrets.items():
        if override or key not in os.environ:
            os.environ[key] = value