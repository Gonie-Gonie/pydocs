# docscriptor

Docscriptor is an early-stage, Python-first alternative to LaTeX for teams who want documents to be defined with regular Python code.
The long-term goal is to compose structured content in scripts, reuse templates and components, and render the same source into PDF and DOCX outputs.

## Vision

- define documents with normal Python modules, functions, and data structures
- make document generation programmable, testable, and reusable
- support multiple export targets without committing to a TeX-centric workflow

## Development

Assuming Python 3.14 is already installed on the machine, run the setup script:

```powershell
.\setup.ps1
```

The script will:

- find Python 3.14
- create or reuse `.venv`
- upgrade `pip`
- install the project in editable mode with `dev` dependencies

To activate the virtual environment manually after setup:

```powershell
.\.venv\Scripts\Activate.ps1
```

## VS Code

This repository commits workspace settings for VS Code.
After running `.\setup.ps1`, opening the folder in VS Code should pick `.venv` as the default interpreter and enable pytest discovery for the `tests` folder.

Run the test suite:

```powershell
pytest
```

Build distribution artifacts:

```powershell
python -m build
```
