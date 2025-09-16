import os

# Define the directory structure
structure = {
    "backend": [
        "main.py",
        "models.py",
        "db.py",
        "settings.py",
        "logging_middleware.py"
    ],
    "agent": [
        "graph.py",
        "state.py",
        "runners.py",
        "policies.py"
    ],
    "tools": [
        "mobile_ui.py",
        "gestures.py",
        "auth_wait.py",
        "post_auth.py",
        "selectors.py",
        "utils.py"
    ],
    "drivers": [
        "appium_client.py",
        "capabilities.py"
    ],
    "data": [
        "constants.py",
        "samples.json"
    ],
    "tests": [
        "e2e_outlook_creation.py",
        "test_year_edge_case.py",
        "test_captcha_long_press.py",
        "test_post_auth_fast_path.py"
    ],
    "scripts": [
        "run_local.sh",
        "init_db.py"
    ],
    "diagrams": [
        "outlook_agent_architecture.mermaid",
        "outlook_agent_sequence.mermaid"
    ]
}

# Create root-level files
root_files = ["requirements.txt", "README.md"]

# Create all directories and files
for directory, files in structure.items():
    os.makedirs(directory, exist_ok=True)
    for file in files:
        file_path = os.path.join(directory, file)
        with open(file_path, 'w') as f:
            f.write(f"# {file}\n")
            
# Create root files
for file in root_files:
    with open(file, 'w') as f:
        f.write(f"# {file}\n")

print("Directory structure created successfully!")