param(
    [switch]$Clean,
    [switch]$NoUPX,
    [string]$Spec = "onefile-gui-external.spec",  # ok to keep; we patch it to embed assets
    [string]$PyInstallerVersion = ""
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err ($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

$ProjectDir = Split-Path -LiteralPath $PSCommandPath
Set-Location -LiteralPath $ProjectDir

if (-not (Test-Path $Spec)) {
    Write-Err "Spec file '$Spec' not found. Expected in: $ProjectDir"
    exit 2
}

# Assets we want INSIDE the EXE (MEIPASS) via -- datas in the spec
$EmbedAssets    = @("plotly.json","weather-codes.json")
# Assets we still want to ship next to the EXE
$ExternalAssets = @("config.py")

# --- Python/venv bootstrap ---
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue)       { $pythonCmd = 'py -3' }
elseif (Get-Command python -ErrorAction SilentlyContinue){ $pythonCmd = 'python' }
else {
    Write-Err "Neither 'py' nor 'python' found on PATH. Install Python 3.x and/or the Python Launcher."
    exit 3
}

$venvPy = '.venv\Scripts\python.exe'
$venvPip = '.venv\Scripts\pip.exe'

if (-not (Test-Path $venvPy)) {
    Write-Info "Creating virtual environment in .venv ..."
    & $pythonCmd -m venv .venv
}

Write-Info "Upgrading pip ..."
& $venvPip install --upgrade pip

if (Test-Path 'requirements.txt') {
    Write-Info "Installing requirements from requirements.txt ..."
    & $venvPip install -r requirements.txt
} else {
    Write-Warn "requirements.txt not found. Installing PyInstaller only."
}

if ($PyInstallerVersion) {
    Write-Info "Installing PyInstaller==$PyInstallerVersion ..."
    & $venvPip install "pyinstaller==$PyInstallerVersion"
} else {
    Write-Info "Ensuring PyInstaller is installed ..."
    & $venvPip install pyinstaller
}

# --- Clean build dirs if requested ---
if ($Clean) {
    if (Test-Path 'build') { Write-Info "Removing .\build ..."; Remove-Item -Recurse -Force 'build' }
    if (Test-Path 'dist')  { Write-Info "Removing .\dist  ..."; Remove-Item -Recurse -Force 'dist'  }
}

# --- Load and patch the spec text ---
$specText = Get-Content -Raw -LiteralPath $Spec

# Normalize pathex to the current project dir
$projEsc = ($ProjectDir -replace '\\','\\\\')
$specText = $specText -replace "pathex=\['\.']", ("pathex=[r'" + $projEsc + "']")

# Optionally disable UPX
if ($NoUPX) {
    Write-Info "Disabling UPX for this build (NoUPX) ..."
    $specText = $specText -replace 'upx=True', 'upx=False'
}

# --- Embed plotly.json and weather-codes.json into the EXE ---
# Build a Python tuple list text for datas
$embedPairs = $EmbedAssets | ForEach-Object { "('$_','.')" }
$embedList  = ($embedPairs -join ', ')
# 1) If the spec already has a datas=[...], append our entries (with a comma if needed)
if ($specText -match "datas\s*=\s*\[([^\]]*)\]") {
    # Append only if not already present
    $existing = $Matches[1]
    foreach ($a in $EmbedAssets) {
        if ($existing -notmatch [regex]::Escape($a)) {
            $existing = $existing.Trim()
            if ($existing -ne '' -and $existing[-1] -ne ',') { $existing = $existing + ', ' }
            $existing = $existing + "('$a','.')"
        }
    }
    $specText = [regex]::Replace($specText, "datas\s*=\s*\[([^\]]*)\]", "datas=[$existing]", 1)
}
else {
    # 2) Otherwise, inject datas=[...] into the Analysis(...) call
    # Insert right after 'Analysis(' (only the first occurrence)
    $specText = [regex]::Replace($specText, "Analysis\s*\(", "Analysis(datas=[$embedList], ", 1)
}

# Write the temp spec and build
$tempSpec = Join-Path $ProjectDir ("_tmp_" + [System.Guid]::NewGuid().ToString() + ".spec")
$specText | Set-Content -LiteralPath $tempSpec -Encoding UTF8

try {
    Write-Info "Running PyInstaller with spec: $tempSpec"
    & $venvPy -m PyInstaller $tempSpec
}
finally {
    if (Test-Path $tempSpec) { Remove-Item -Force $tempSpec }
}

# PyInstaller puts the one-file exe directly into .\dist
$distDir = Join-Path $ProjectDir 'dist'
$exePath = Join-Path $distDir 'lpd-suite.exe'

if (-not (Test-Path $exePath)) {
    Write-Err "Build completed but 'lpd-suite.exe' not found in $distDir"
    exit 4
}

# Copy ONLY the assets that should remain external (config.py)
Write-Info "Copying external assets next to the EXE (only those meant to remain outside) ..."
foreach ($asset in $ExternalAssets) {
    if (Test-Path $asset) {
        Copy-Item -LiteralPath $asset -Destination $distDir -Force
    } else {
        Write-Warn "External asset not found: $asset (skipping)"
    }
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "[SUCCESS] One-file build complete" -ForegroundColor Green
Write-Host "Output:" -ForegroundColor Green
Write-Host "  $exePath" -ForegroundColor Green
Write-Host ""
Write-Host "Ship this folder to users:" -ForegroundColor Green
Write-Host "  $distDir" -ForegroundColor Green
Write-Host "Which should contain:" -ForegroundColor Green
Write-Host "  - lpd-suite.exe (contains: plotly.json, weather-codes.json)" -ForegroundColor Green
Write-Host "  - config.py (external; holds OPENWEATHER_API_KEY)" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
