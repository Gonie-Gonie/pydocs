[CmdletBinding()]
param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Test-Python314 {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    try {
        & $Command @Arguments -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 14) else 1)" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Invoke-External {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [Parameter(Mandatory)]
        [string]$FailureMessage
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code: $LASTEXITCODE)"
    }
}

function Test-CommandSuccess {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    try {
        & $Command @Arguments *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Invoke-PythonModuleWithTemp {
    param(
        [Parameter(Mandatory)]
        [string]$PythonPath,

        [Parameter(Mandatory)]
        [string]$ModuleName,

        [string[]]$ModuleArguments = @(),

        [Parameter(Mandatory)]
        [string]$FailureMessage
    )

    $runner = "import runpy, sys, tempfile; module_name = sys.argv[1]; tempfile.tempdir = sys.argv[2]; sys.argv = [sys.argv[0]] + sys.argv[3:]; runpy.run_module(module_name, run_name='__main__')"
    Invoke-External -Command $PythonPath -Arguments (@("-c", $runner, $ModuleName, $tempRoot) + $ModuleArguments) -FailureMessage $FailureMessage
}

$repoRoot = $PSScriptRoot
$resolvedVenvPath = if ([System.IO.Path]::IsPathRooted($VenvPath)) {
    $VenvPath
} else {
    Join-Path $repoRoot $VenvPath
}

$tempRoot = Join-Path $repoRoot ".setup-temp"
$venvPython = Join-Path $resolvedVenvPath "Scripts\python.exe"
$pythonCommand = $null
$pythonArguments = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-Python314 -Command "py" -Arguments @("-3.14")) {
        $pythonCommand = "py"
        $pythonArguments = @("-3.14")
    }
}

if (-not $pythonCommand -and (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Test-Python314 -Command "python") {
        $pythonCommand = "python"
        $pythonArguments = @()
    }
}

if (-not $pythonCommand) {
    throw "Python 3.14 was not found. Install Python 3.14 and rerun this script."
}

$pythonDisplay = ($pythonCommand + " " + ($pythonArguments -join " ")).Trim()
Write-Host "Using Python launcher: $pythonDisplay"

$originalTemp = $env:TEMP
$originalTmp = $env:TMP

try {
    if (-not (Test-Path -LiteralPath $tempRoot)) {
        New-Item -ItemType Directory -Path $tempRoot | Out-Null
    }

    $env:TEMP = $tempRoot
    $env:TMP = $tempRoot

    if (Test-Path -LiteralPath $venvPython) {
        if (-not (Test-Python314 -Command $venvPython)) {
            throw "Existing virtual environment at '$resolvedVenvPath' is not using Python 3.14. Remove it and rerun the script."
        }

        Write-Host "Reusing existing virtual environment: $resolvedVenvPath"
    } else {
        Write-Host "Creating virtual environment: $resolvedVenvPath"
        Invoke-External -Command $pythonCommand -Arguments ($pythonArguments + @("-m", "venv", "--without-pip", $resolvedVenvPath)) -FailureMessage "Failed to create the virtual environment."
    }

    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "Virtual environment was not created correctly. Expected interpreter: $venvPython"
    }

    if (-not (Test-CommandSuccess -Command $venvPython -Arguments @("-m", "pip", "--version"))) {
        Write-Host "Bootstrapping pip inside the virtual environment"
        Invoke-PythonModuleWithTemp -PythonPath $venvPython -ModuleName "ensurepip" -ModuleArguments @("--upgrade", "--default-pip") -FailureMessage "Failed to bootstrap pip inside the virtual environment."
    }

    Write-Host "Upgrading pip"
    Invoke-PythonModuleWithTemp -PythonPath $venvPython -ModuleName "pip" -ModuleArguments @("install", "--upgrade", "pip") -FailureMessage "Failed to upgrade pip."

    Write-Host "Installing project and development dependencies"
    Invoke-PythonModuleWithTemp -PythonPath $venvPython -ModuleName "pip" -ModuleArguments @("install", "-e", ".[dev]") -FailureMessage "Failed to install project dependencies."
}
finally {
    $env:TEMP = $originalTemp
    $env:TMP = $originalTmp

    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Activate the environment with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
