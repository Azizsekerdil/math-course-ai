<#
Build a PyMuPDF-free Windows release package.

Usage:
  .\build_windows.ps1 -Version v1.0.1

The generated onedir application stays in dist\windows\Math Course AI and the
ZIP/checksum are intended for a GitHub Release asset, never for a source commit.
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "",
    [ValidatePattern('^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$')]
    [string]$Version = "v1.0.1"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSCommandPath
Set-Location $projectRoot

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = (& py -3.11 -c "import sys; print(sys.executable)").Trim()
}
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Python 3.11 was not found. Pass -PythonExe with its full python.exe path."
}
$pythonVersion = (& $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($pythonVersion -ne "3.11") {
    throw "This release build requires Python 3.11, not Python $pythonVersion."
}

$venvPath = Join-Path $projectRoot ".build-venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$distPath = Join-Path $projectRoot "dist\windows"
$workPath = Join-Path $projectRoot "build\windows\pyinstaller"
$specPath = Join-Path $projectRoot "build\windows\spec"
$appName = "Math Course AI"
$appPath = Join-Path $distPath $appName
$exePath = Join-Path $appPath "$appName.exe"
$assetBaseName = "Math.Course.AI-Windows-$Version"
$zipPath = Join-Path $distPath "$assetBaseName.zip"
$checksumPath = "$zipPath.sha256"

# A clean venv is part of the licensing boundary: never let an installed
# PyMuPDF/fitz leak from a developer environment into a distributed bundle.
& $PythonExe -m venv --clear $venvPath
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
& $venvPython -m pip install `
    "opencv-python==4.13.0.92" `
    "pytesseract==0.3.13" `
    "python-docx==1.2.0" `
    "python-pptx==1.0.2" `
    "pyinstaller==6.22.3"

$forbiddenPackageCheck = @'
import importlib.util
import sys

names = ("fitz", "pymupdf", "mupdf")
found = [name for name in names if importlib.util.find_spec(name) is not None]
if found:
    print("Forbidden PyMuPDF/MuPDF modules found: " + ", ".join(found))
    raise SystemExit(1)
'@
& $venvPython -c $forbiddenPackageCheck

$addData = @(
    "$(Join-Path $projectRoot 'math_course_ai_icon.ico');.",
    "$(Join-Path $projectRoot 'LICENSE');.",
    "$(Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md');."
)
$hiddenImports = @(
    "PIL", "PIL.Image", "PIL.ImageTk", "PIL.ImageDraw", "docx", "pptx",
    "pytesseract", "numpy", "cv2", "sympy", "matplotlib", "requests",
    "app_paths", "education", "token_ledger", "ai_terminal", "terminal_tutanak",
    "nvidia_provider", "mca_common", "lm_studio_client", "science_labs",
    "whiteboard", "pdf_viewer", "calculator", "classic_dictionary",
    "topic_knowledge", "topic_knowledge_round2", "student_tracker", "question_packs",
    "language_dictionary", "visual_math_lab", "visual_lesson_card",
    "workspace_docking_manager", "command_registry", "ui_preferences",
    "embedded_course_simulations", "embedded_formula_library",
    "course_simulation_library", "ai_code_guard", "cloud_consent"
)
$pyInstallerArgs = @(
    "--noconfirm", "--clean", "--onedir", "--windowed",
    "--name", $appName,
    "--distpath", $distPath,
    "--workpath", $workPath,
    "--specpath", $specPath,
    "--icon", (Join-Path $projectRoot "math_course_ai_icon.ico"),
    "--exclude-module", "fitz",
    "--exclude-module", "pymupdf",
    "--exclude-module", "mupdf",
    "--collect-all", "PIL"
)
foreach ($item in $addData) {
    $pyInstallerArgs += @("--add-data", $item)
}
foreach ($item in $hiddenImports) {
    $pyInstallerArgs += @("--hidden-import", $item)
}
$pyInstallerArgs += (Join-Path $projectRoot "Math_Course_AI.pyw")
& $venvPython -m PyInstaller @pyInstallerArgs

if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
    throw "PyInstaller did not create $exePath"
}
$forbiddenPath = "pymupdf|mupdf|fitz"
$forbiddenFiles = Get-ChildItem -LiteralPath $appPath -Recurse -Force |
    Where-Object { $_.FullName -match $forbiddenPath }
if ($forbiddenFiles) {
    throw "Forbidden PyMuPDF/MuPDF bundle components: $($forbiddenFiles.FullName -join ', ')"
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -Path $appPath -DestinationPath $zipPath -CompressionLevel Optimal
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $forbiddenEntries = @($archive.Entries | Where-Object { $_.FullName -match $forbiddenPath })
    if ($forbiddenEntries) {
        throw "Forbidden PyMuPDF/MuPDF ZIP entries: $($forbiddenEntries.FullName -join ', ')"
    }
}
finally {
    $archive.Dispose()
}

$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksumPath -Value "$hash  $(Split-Path -Leaf $zipPath)" -Encoding ascii -NoNewline

Write-Host "EXE: $exePath"
Write-Host "Release ZIP: $zipPath"
Write-Host "SHA-256: $checksumPath"
