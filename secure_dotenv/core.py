import os
import json
import uuid
import keyring
from pathlib import Path
from cryptography.fernet import Fernet

VAULT_DIR = Path.home() / ".secure_dotenv"
VAULT_FILE = VAULT_DIR / "vault.enc"
SERVICE_NAME = "secure_dotenv"
KEY_NAME = "master_key"

def _get_or_create_key() -> bytes:
    key = keyring.get_password(SERVICE_NAME, KEY_NAME)
    if not key:
        key = Fernet.generate_key().decode()
        keyring.set_password(SERVICE_NAME, KEY_NAME, key)
    return key.encode()

def _load_vault() -> dict:
    if not VAULT_FILE.exists():
        return {}
    key = _get_or_create_key()
    cipher = Fernet(key)
    with open(VAULT_FILE, "rb") as f:
        encrypted_data = f.read()
    try:
        return json.loads(cipher.decrypt(encrypted_data))
    except Exception:
        return {}

def _save_vault(data: dict):
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    key = _get_or_create_key()
    cipher = Fernet(key)
    with open(VAULT_FILE, "wb") as f:
        f.write(cipher.encrypt(json.dumps(data).encode()))

def save_project_secrets(project_id: str, env_name: str, secrets: dict, project_path: str):
    """Saves secrets under a specific environment profile (e.g., '.env.local')."""
    vault = _load_vault()
    if project_id not in vault:
        vault[project_id] = {"path": project_path, "environments": {}}
    
    if "environments" not in vault[project_id]: # Migration safety
        vault[project_id]["environments"] = {}
        
    vault[project_id]["environments"][env_name] = secrets
    _save_vault(vault)

def get_project_secrets(project_id: str, env_name: str = ".env") -> dict:
    vault = _load_vault()
    return vault.get(project_id, {}).get("environments", {}).get(env_name, {})

def get_all_vault_data() -> dict:
    return _load_vault()

def delete_project(project_id: str):
    """Deletes an entire project and all of its environments from the vault."""
    vault = _load_vault()
    if project_id in vault:
        del vault[project_id]
        _save_vault(vault)

def parse_env_file(filepath: str) -> dict:
    secrets = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, val = line.split("=", 1)
                secrets[key.strip()] = val.strip().strip("'\"")
    return secrets

def migrate_and_clear_env(filepath: str, project_id: str):
    """
    1. Parse the file.
    2. Check if there are any keys with non-empty values.
    3. If NO values are found, return immediately (Zero-Touch).
    4. If values are found, sync to vault and rewrite only the dirty lines.
    """
    env_name = Path(filepath).name
    current_secrets_in_file = parse_env_file(str(filepath))
    
    # Check what already exists in the vault for this project/env
    existing_vault_secrets = get_project_secrets(project_id, env_name)
    
    # Determine which keys need to be migrated to the vault
    keys_to_migrate = {}
    for k, v in current_secrets_in_file.items():
        # Migrate the key if the user provided a non-empty value (it takes precedence)
        # OR if it's an empty key that does not yet exist in the vault.
        if (v and v.strip()) or (k not in existing_vault_secrets):
            keys_to_migrate[k] = v
            
    # Always sync to vault to register the project/env (even if keys_to_migrate is empty)
    updated_vault_secrets = existing_vault_secrets.copy()
    updated_vault_secrets.update(keys_to_migrate)
    save_project_secrets(project_id, env_name, updated_vault_secrets, str(Path.cwd()))
    
    # We only need to rewrite the .env file to strip values from keys that HAD non-empty values
    keys_to_strip = {k: v for k, v in current_secrets_in_file.items() if v and v.strip()}
    
    if not keys_to_strip:
        return 

    # Rewrite the file only for the keys we just stripped values from
    with open(filepath, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    for line in lines:
        line_clean = line.strip()
        # Check if line matches a key we just stripped
        is_dirty = False
        for k in keys_to_strip.keys():
            if line_clean.startswith(f"{k}="):
                new_lines.append(f"{k}=\n")
                modified = True
                is_dirty = True
                break
        
        if not is_dirty:
            new_lines.append(line)
            
    # Save file only if a change was actually made
    if modified:
        with open(filepath, "w") as f:
            f.writelines(new_lines)


def restore_env_file(filepath: str, project_id: str):
    env_name = Path(filepath).name
    secrets = get_project_secrets(project_id, env_name)

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    restored_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.lstrip()

        # Ignore comments and invalid lines
        if stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue

        key_part, value_part = line.split("=", 1)
        key = key_part.strip()

        if key in secrets:
            newline = "\n" if line.endswith("\n") else ""
            new_lines.append(f"{key_part}={secrets[key]}{newline}")
            restored_keys.add(key)
        else:
            new_lines.append(line)

    # Append vault keys that don't exist in file
    missing_keys = [k for k in secrets if k not in restored_keys]

    if missing_keys:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"

        for k in missing_keys:
            new_lines.append(f"{k}={secrets[k]}\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)