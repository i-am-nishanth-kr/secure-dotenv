import click
import os
import uuid
from pathlib import Path
from .core import parse_env_file, save_project_secrets, _load_vault, _save_vault

@click.group()
def cli():
    """secure_dotenv: Secure your .env files."""
    pass

@cli.command()
def init():
    """Initializes the current folder as a secure_dotenv project."""
    project_root = Path.cwd()
    id_file = project_root / ".secure-env-id"
    
    if id_file.exists():
        click.secho("✅ This project is already initialized.", fg="yellow")
        return
        
    project_id = str(uuid.uuid4())
    id_file.write_text(project_id)
    
    # Register the project in the vault with an empty environment
    # We pass an empty dict so it exists in the vault JSON
    from .core import save_project_secrets
    save_project_secrets(project_id, ".env", {}, str(project_root))
    
    # Add to gitignore automatically
    ignore_file = project_root / ".gitignore"
    if ignore_file.exists():
        with open(ignore_file, "a") as f:
            f.write("\n# Added by secure_dotenv\n.secure-env-id\n")
            
    click.secho(f"🚀 Initialized secure_dotenv for this folder (ID: {project_id[:8]})", fg="green")

def _get_current_project_id():
    id_file = Path.cwd() / ".secure-env-id"
    if not id_file.exists():
        click.secho("Error: Not a secured project. Run 'secure-dotenv migrate' first.", fg="red")
        raise click.Abort()
    return id_file.read_text().strip()

@cli.command()
@click.argument("env_name", default=".env")
def restore(env_name):
    """Brings back the values from the vault into the env file."""
    project_id = _get_current_project_id()
    env_file = Path.cwd() / env_name
    
    if not env_file.exists():
        click.secho(f"⚠️ {env_name} does not exist.", fg="red")
        return
        
    from .core import restore_env_file
    restore_env_file(str(env_file), project_id)
    click.secho(f"✅ Restored values to {env_name}", fg="green")

# Only migrate keys that actually have values
@cli.command()
def migrate():
    """Syncs vault with local .env files."""
    project_id = _get_current_project_id()
    env_files = list(Path.cwd().glob(".env*"))
    env_files.remove(".env.example")
    from .core import migrate_and_clear_env
    for f in env_files:
        if f.name == ".secure-env-id": continue
        migrate_and_clear_env(str(f), project_id)
    click.secho("✅ Sync complete: Secrets moved to vault, files cleared.", fg="green")

# --- CRUD COMMANDS ---

@cli.command()
def projects():
    """List all secured projects in the vault."""
    vault = _load_vault()
    click.secho("🛡️ Secured Projects:", fg="blue", bold=True)
    for pid, data in vault.items():
        envs = list(data.get("environments", {}).keys())
        click.echo(f"- {data['path']} (Profiles: {', '.join(envs)})")

@cli.command()
@click.argument("env_name", default=".env")
def secrets(env_name):
    """List secrets for the current project."""
    # Logic to handle if user hasn't run init yet
    id_file = Path.cwd() / ".secure-env-id"
    if not id_file.exists():
        click.secho("⚠️ Project not initialized. Run 'secure-dotenv init' first.", fg="yellow")
        return
        
    project_id = id_file.read_text().strip()
    vault = _load_vault()
    secrets_dict = vault.get(project_id, {}).get("environments", {}).get(env_name, {})
    
    if not secrets_dict:
        click.echo(f"No secrets found for {env_name}.")
        return

    click.secho(f"🔑 Secrets for {env_name}:", fg="blue", bold=True)
    for k, v in secrets_dict.items():
        masked = v[:2] + "•" * (len(v) - 2) if len(v) > 2 else "•••"
        click.echo(f"  {k}: {masked}")

@cli.command()
@click.argument("key")
@click.argument("value")
@click.option("--env", default=".env", help="Environment profile (e.g., .env.local)")
def set(env, key, value):
    """Add or update a secret. Defaults to .env if --env is not provided."""
    project_id = _get_current_project_id()
    vault = _load_vault()
    
    # 1. Get the current project data
    proj_data = vault.get(project_id)
    if not proj_data:
        click.secho("Error: Project not found in vault.", fg="red")
        return
    
    # 2. Ensure the 'environments' dict exists (handles older versions)
    if "environments" not in proj_data:
        proj_data["environments"] = {}
        
    # 3. Ensure the specific env (e.g., .env.local) exists
    if env not in proj_data["environments"]:
        proj_data["environments"][env] = {}
        
    # 4. Set the secret
    proj_data["environments"][env][key] = value
    
    # 5. Save back to vault
    _save_vault(vault)
    click.secho(f"✅ Set {key} in {env}", fg="green")

@cli.command()
@click.argument("env_name")
@click.argument("key")
def delete(env_name, key):
    """Delete a secret from a profile."""
    project_id = _get_current_project_id()
    vault = _load_vault()
    try:
        del vault[project_id]["environments"][env_name][key]
        _save_vault(vault)
        click.secho(f"🗑️ Deleted {key} from {env_name}", fg="yellow")
    except KeyError:
        click.secho(f"⚠️ Key {key} not found.", fg="red")

@cli.command()
@click.argument("port", default=8084)
def ui(port):
    """Starts the local web UI for managing secrets."""
    import uvicorn
    click.secho(f"🚀 Starting Secure Vault UI on http://localhost:{port}", fg="blue")
    uvicorn.run("secure_dotenv.ui:app", host="127.0.0.1", port=port, log_level="warning")

@cli.command()
@click.argument("env_name")
def delete_profile(env_name):
    """Delete an entire environment profile (e.g., .env.local)."""
    project_id = _get_current_project_id()
    vault = _load_vault()
    
    if project_id in vault and env_name in vault[project_id].get("environments", {}):
        del vault[project_id]["environments"][env_name]
        _save_vault(vault)
        click.secho(f"🗑️ Deleted environment profile: {env_name}", fg="yellow")
    else:
        click.secho(f"⚠️ Profile '{env_name}' not found.", fg="red")