from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .core import _load_vault, _save_vault

app = FastAPI(title="Secure DotEnv Vault")

class SecretUpdate(BaseModel):
    key: str
    value: str

@app.post("/api/project/init")
def init_project():
    project_root = str(Path.cwd())
    project_id = str(uuid.uuid4())
    # Create the tracker file
    (Path.cwd() / ".secure-env-id").write_text(project_id)
    # Save to vault
    save_project_secrets(project_id, ".env", {}, project_root)
    return {"status": "success"}
    
@app.get("/api/vault")
def get_vault():
    return _load_vault()

@app.post("/api/vault/{project_id}/{env_name}")
def update_secret(project_id: str, env_name: str, payload: SecretUpdate):
    vault = _load_vault()
    if project_id in vault:
        if env_name not in vault[project_id]["environments"]:
            vault[project_id]["environments"][env_name] = {}
        vault[project_id]["environments"][env_name][payload.key] = payload.value
        _save_vault(vault)
    return {"status": "success"}

@app.delete("/api/vault/{project_id}/{env_name}/{key}")
def delete_secret(project_id: str, env_name: str, key: str):
    vault = _load_vault()
    try:
        del vault[project_id]["environments"][env_name][key]
        _save_vault(vault)
    except KeyError:
        pass
    return {"status": "success"}

@app.delete("/api/vault/{project_id}/{env_name}")
def delete_environment_profile(project_id: str, env_name: str):
    vault = _load_vault()
    if project_id in vault and env_name in vault[project_id].get("environments", {}):
        del vault[project_id]["environments"][env_name]
        _save_vault(vault)
    return {"status": "success"}

@app.post("/api/vault/{project_id}/{env_name}")
def create_or_update_profile(project_id: str, env_name: str, payload: SecretUpdate):
    vault = _load_vault()
    if project_id in vault:
        if "environments" not in vault[project_id]:
            vault[project_id]["environments"] = {}
        
        # If profile doesn't exist, create it
        if env_name not in vault[project_id]["environments"]:
            vault[project_id]["environments"][env_name] = {}
            
        # Add the secret (the placeholder)
        vault[project_id]["environments"][env_name][payload.key] = payload.value
        _save_vault(vault)
        
    return {"status": "success"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """A fully functional Single Page Application UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>secure_dotenv UI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style> body { background-color: #f3f4f6; } </style>
    </head>
    <body class="p-8">
        <div class="max-w-5xl mx-auto bg-white shadow-lg rounded-lg flex overflow-hidden min-h-[600px]">
            
            <!-- Left Sidebar (Projects) -->
            <div class="w-1/3 bg-gray-800 text-white p-4">
                <h2 class="text-xl font-bold mb-4">🛡️ Secured Projects</h2>
                <ul id="project-list" class="space-y-2"></ul>
            </div>

            <!-- Right Content (Secrets) -->
            <div class="w-2/3 p-6">
                <h2 id="current-project" class="text-2xl font-bold text-gray-800 mb-2">Select a Project</h2>
                <div id="env-tabs-container" class="flex flex-wrap gap-2 mb-4 border-b pb-2">
                    <div id="env-tabs" class="flex space-x-2"></div>
                    <div class="flex items-center space-x-2">
                        <input type="text" id="new-env-name" placeholder=".env.new" class="border p-1 rounded text-sm w-24">
                        <button onclick="addProfile()" class="bg-green-600 text-white px-2 py-1 rounded text-sm">+</button>
                    </div>
                </div>
                
                <table class="w-full text-left border-collapse" id="secrets-table" style="display:none;">
                    <thead>
                        <tr class="bg-gray-100"><th class="p-2 border">Key</th><th class="p-2 border">Value</th><th class="p-2 border">Action</th></tr>
                    </thead>
                    <tbody id="secrets-body"></tbody>
                </table>

                <div id="add-form" class="mt-4" style="display:none;">
                    <input type="text" id="new-key" placeholder="API_KEY" class="border p-2 rounded">
                    <input type="text" id="new-val" placeholder="Value..." class="border p-2 rounded">
                    <button onclick="addSecret()" class="bg-blue-600 text-white px-4 py-2 rounded">Add</button>
                </div>
            </div>
        </div>

        <script>
            let vaultData = {};
            let currentProj = null;
            let currentEnv = null;

            async function loadVault() {
                const res = await fetch('/api/vault');
                vaultData = await res.json();
                renderProjects();
            }

            function renderProjects() {
                const list = document.getElementById('project-list');
                list.innerHTML = '';
                for (const [id, data] of Object.entries(vaultData)) {
                    const li = document.createElement('li');
                    li.className = "cursor-pointer hover:bg-gray-700 p-2 rounded truncate";
                    li.innerText = data.path;
                    li.onclick = () => selectProject(id);
                    list.appendChild(li);
                }
            }

            function selectProject(id, envToSelect = null) {
                currentProj = id;
                document.getElementById('current-project').innerText = vaultData[id].path;
                
                // If an envToSelect is provided, use it; otherwise, default to the first one
                const envs = Object.keys(vaultData[id].environments || {});
                currentEnv = (envToSelect && envs.includes(envToSelect)) ? envToSelect : (envs[0] || null);
                
                renderTabs();
                renderSecrets();
            }

            function renderTabs() {
                const tabs = document.getElementById('env-tabs');
                tabs.innerHTML = '';
                const envs = Object.keys(vaultData[currentProj].environments || {});
                
                envs.forEach(env => {
                    const container = document.createElement('div');
                    container.className = "flex items-center space-x-1";
                    
                    const btn = document.createElement('button');
                    btn.className = `px-3 py-1 rounded ${env === currentEnv ? 'bg-blue-500 text-white' : 'bg-gray-200'}`;
                    btn.innerText = env;
                    btn.onclick = () => selectEnv(env);
                    
                    // Add a "X" button to delete the profile
                    const delBtn = document.createElement('button');
                    delBtn.innerHTML = '&times;';
                    delBtn.className = "text-red-500 font-bold px-1 hover:text-red-700";
                    delBtn.onclick = (e) => {
                        e.stopPropagation();
                        deleteProfile(env);
                    };
                    
                    container.appendChild(btn);
                    container.appendChild(delBtn);
                    tabs.appendChild(container);
                });
            }

            async function addProfile() {
                const envName = document.getElementById('new-env-name').value;
                if (!envName || !currentProj) return;

                // Use a POST request to create an empty profile
                await fetch(`/api/vault/${currentProj}/${envName}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key: "placeholder", value: "placeholder"}) // Add a placeholder
                });
                
                document.getElementById('new-env-name').value = '';
                await loadVault();
                currentEnv = envName;
                selectProject(currentProj);
            }

            // Add the deleteProfile function
            async function deleteProfile(env) {
                if(!confirm(`Are you sure you want to delete the ${env} profile?`)) return;
                
                // We need a new backend endpoint for this
                await fetch(`/api/vault/${currentProj}/${env}`, { method: 'DELETE' });
                await loadVault();
                currentEnv = Object.keys(vaultData[currentProj].environments)[0] || null;
                selectProject(currentProj);
            }
            
            function selectEnv(env) {
                currentEnv = env;
                renderTabs();
                renderSecrets();
            }

            function renderSecrets() {
                document.getElementById('secrets-table').style.display = 'table';
                document.getElementById('add-form').style.display = 'block';
                const body = document.getElementById('secrets-body');
                body.innerHTML = '';
                
                const secrets = vaultData[currentProj].environments[currentEnv] || {};
                for (const [key, val] of Object.entries(secrets)) {
                    const rowId = `row-${key}`;
                    body.innerHTML += `
                        <tr id="${rowId}">
                            <td class="p-2 border font-mono text-sm">${key}</td>
                            <td class="p-2 border">
                                <input type="password" id="input-${key}" value="${val}" 
                                       oninput="enableSave('${key}')"
                                       class="font-mono text-sm w-full bg-transparent outline-none" disabled>
                            </td>
                            <td class="p-2 border space-x-2">
                                <button onclick="toggleEdit('${key}')" id="btn-edit-${key}" class="text-blue-600 hover:underline">Edit</button>
                                <button onclick="saveSecret('${key}')" id="btn-save-${key}" class="text-green-600 hover:underline hidden">Save</button>
                                <button onclick="deleteSecret('${key}')" class="text-red-500 hover:underline">Delete</button>
                            </td>
                        </tr>
                    `;
                }
            }

            function toggleEdit(key) {
                const input = document.getElementById(`input-${key}`);
                const editBtn = document.getElementById(`btn-edit-${key}`);
                
                input.disabled = false;
                input.type = "text"; // Show password during edit
                input.focus();
                editBtn.classList.add('hidden');
                document.getElementById(`btn-save-${key}`).classList.remove('hidden');
            }

            function enableSave(key) {
                // The Save button is already visible after toggleEdit, 
                // this could be used for additional validation
            }

            async function saveSecret(key) {
                const val = document.getElementById(`input-${key}`).value;
                const env = currentEnv; 
                
                await fetch(`/api/vault/${currentProj}/${env}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key: key, value: val})
                });
                
                await loadVault();
                selectProject(currentProj, env); // Pass the current env here
            }

            async function addSecret() {
                const key = document.getElementById('new-key').value;
                const val = document.getElementById('new-val').value;
                const env = currentEnv; // Keep track of current env
                
                await fetch(`/api/vault/${currentProj}/${env}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key: key, value: val})
                });
                
                await loadVault();
                selectProject(currentProj, env); // Pass the current env here
            }

            async function deleteSecret(key) {
                const env = currentEnv;
                await fetch(`/api/vault/${currentProj}/${env}/${key}`, { method: 'DELETE' });
                
                await loadVault();
                selectProject(currentProj, env); // Pass the current env here
            }

            loadVault();
        </script>
    </body>
    </html>
    """