$ErrorActionPreference = "Stop"
param(
    [string]$Profile = "profiles\example.branch-reset.yaml"
)
& "$PSScriptRoot\..\.venv\Scripts\python.exe" "$PSScriptRoot\..\src\main.py" render-config --profile $Profile

