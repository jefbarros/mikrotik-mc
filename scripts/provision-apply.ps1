$ErrorActionPreference = "Stop"
param(
    [Parameter(Mandatory = $true)]
    [string]$Profile
)
& "$PSScriptRoot\..\.venv\Scripts\python.exe" "$PSScriptRoot\..\src\main.py" provision --profile $Profile --execute --i-understand-this-changes-router

