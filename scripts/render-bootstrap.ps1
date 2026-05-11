$ErrorActionPreference = "Stop"
param(
    [string]$Profile = "profiles\example.branch-reset.yaml"
)
& "$PSScriptRoot\..\.venv\Scripts\python.exe" "$PSScriptRoot\..\src\main.py" render-bootstrap --profile $Profile

