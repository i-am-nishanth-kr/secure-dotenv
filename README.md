
# 🔐 Secure dotenv

<img src="./assets/logo.png" alt="Secure dotenv" width="800"/>

**Secure dotenv** is a secure replacement for traditional `.env` files.  
It automatically moves secrets into a secure vault while keeping your development workflow unchanged.

Your application still reads environment variables the same way — but **secrets never remain in plaintext `.env` files**.

---

# Why Secure dotenv?

Traditional `.env` files are convenient but unsafe.

Common problems:

- Secrets stored in plaintext
- Secrets accidentally committed to Git

**Secure dotenv fixes this automatically.**

- Secrets are moved to a secure vault
- `.env` files keep only the keys
- Secrets are restored to memory at runtime
- No changes required in your application logic

---

# Features

- 🔐 Automatically moves secrets to a secure vault
- 🧠 Drop-in replacement for `dotenv`
- 🚫 Prevents accidental secret commits
- 🔁 Incremental secret migration
- 🗂 Supports multiple projects
- 🌎 Multiple environment profiles (`.env`, `.env.stage`, etc.)
- 🖥 Built-in local UI for managing secrets

---

# Quickstart

## Step 1: Installation

```bash
pip install secure-dotenv
````

---

## Step 2: Init the project
Run the following commands once to initialize

```bash
# 1. initialize a vault
secure-dotenv init
```

## Step 3: (Optional) Migrate an existing `.env` file

For any existing .env files in any existing project, Migrate your secrets.

```bash
# migrate secrets to vault
secure-dotenv migrate
```

---

# Step 4: Python Usage

Replace the standard dotenv import.

```python
#from dotenv import load_dotenv   <- simply replace this with below

from secure_dotenv import load_dotenv

load_dotenv()

print(os.environ['OPENAI_API_KEY'])
```

Your application code remains unchanged.

---

# More features:
# Web UI

Secure dotenv includes a simple UI for managing secrets.

Start the UI with:

```bash
secure-dotenv ui
```

---

# How It Works

1. You create a normal `.env` file with keys and secret values.

```
OPENAI_API_KEY=sk-xxxx
DATABASE_PASSWORD=secret
```

2. When your program runs:

```
load_dotenv()
```

Secure dotenv will:

* Move secret values into the vault
* Remove the values from the `.env` file
* Leave only the variable names behind
* Load the secrets into memory at runtime

Example result:

```
OPENAI_API_KEY=
DATABASE_PASSWORD=
```

Your secrets now live securely in the vault.

---

# Basics

### Vault Structure

Secrets are organized in a hierarchy:

```
 Vault
   └── Project (unique id)
         ├── Profile (.env)
         ├── Profile (.env.stage)
         └── Profile (.env.local)
```

Each profile contains its own secrets.

---

### Automatic Secret Protection

Every time `load_dotenv()` runs:

* Secret values are **removed from `.env`**
* Secrets are **loaded from vault into memory**
* Your application reads them normally using `os.environ`

---

### Incremental Secret Migration

You can keep editing your `.env` file normally.

Secure dotenv automatically detects changes.

* **Add a new secret** → automatically moved to vault
* **Update a secret value** → vault is updated
* **Existing secrets remain untouched**

No manual syncing required.

---

# CLI Commands

```bash
Usage: secure-dotenv [OPTIONS] COMMAND [ARGS]...

secure_dotenv: The AI-safe replacement for .env files.

Options:
  --help  Show this message and exit.

Commands:
  delete          Delete a secret from a profile.
  delete-profile  Delete an entire environment profile (e.g., .env.local).
  init            Initializes the current folder as a secure_dotenv project.
  migrate         Syncs vault with local .env files.
  projects        List all secured projects in the vault.
  restore         Brings back the values from the vault into the env file.
  secrets         List secrets for the current project.
  set             Add or update a secret.
  ui              Starts the local web UI for managing secrets.
```

---

# Security Guarantee

With **Secure dotenv**, your project can never accidentally commit secrets to a repository.

Secrets are:

* stored in a vault
* removed from `.env` files
* loaded only in memory during runtime

---

# Example Workflow

1️⃣ Create `.env`

```
OPENAI_API_KEY=sk-xxxx
```

2️⃣  Create app.py

```python
import os
from secure_dotenv import load_dotenv
load_dotenv()

print(os.environ['OPENAI_API_KEY'])

```
3️⃣ Run command

```bash
secure-dotenv init
```
4️⃣ Run your program
```bash
python app.py
```

5️⃣ .env file automatically becomes:

```
OPENAI_API_KEY=
```

6️⃣ Restore to see the saved vaules

```bash
secure-dotenv restore
```
---

# When to Use Secure dotenv

* Local development
* AI / LLM projects
* DevOps pipelines
* Applications using API keys
* Teams worried about secret leaks

---

# Contributing

Contributions are welcome.

If you find bugs or have feature ideas, please open an issue or pull request.

---

# License

MIT License

---

⭐ **If this project helps protect your secrets, consider giving it a star.**
