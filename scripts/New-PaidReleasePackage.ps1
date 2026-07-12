param(
  [string]$Version = "0.1.0",
  [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path -LiteralPath (Join-Path $ScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $OutputRoot = Join-Path (Split-Path -Parent $RepoRoot) "Academic_Research_Workflow_Agents_Releases"
}

$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
$PackageName = "Academic_Research_Workflow_Agents_v$Version"
$StageRoot = Join-Path $env:TEMP "$PackageName-stage"
$StageDir = Join-Path $StageRoot $PackageName
$ZipPath = Join-Path $OutputRoot "$PackageName.zip"
$HashPath = "$ZipPath.sha256.txt"

function Test-ExcludedPath {
  param([string]$Path)
  $normalized = $Path -replace "\\", "/"
  $fileName = [System.IO.Path]::GetFileName($normalized)

  if ($normalized -match "(^|/)(outputs|node_modules|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.venv|venv|env|build|dist|coverage|archive|archives|archived_runs|private|real_data)(/|$)") {
    return $true
  }
  if ($fileName -match "^\.env(\..*)?$") {
    return $true
  }
  if ($fileName -match "\.(pem|key|p12|pfx|log|pdf|docx|xlsx|xls|dta|sav|rds|zip|7z|rar)$") {
    return $true
  }
  return $false
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
if (Test-Path -LiteralPath $StageRoot) {
  Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

Push-Location $RepoRoot
try {
  $trackedFiles = git ls-files
  foreach ($relativePath in $trackedFiles) {
    if (Test-ExcludedPath -Path $relativePath) {
      continue
    }
    $source = Join-Path $RepoRoot $relativePath
    $target = Join-Path $StageDir $relativePath
    $targetParent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
  }

  Set-Content -LiteralPath (Join-Path $StageDir "VERSION.txt") -Value $Version -Encoding UTF8

  if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
  }
  if (Test-Path -LiteralPath $HashPath) {
    Remove-Item -LiteralPath $HashPath -Force
  }

  Compress-Archive -LiteralPath $StageDir -DestinationPath $ZipPath -CompressionLevel Optimal
  $hash = Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256
  Set-Content -LiteralPath $HashPath -Value "$($hash.Hash)  $([System.IO.Path]::GetFileName($ZipPath))" -Encoding ASCII

  [pscustomobject]@{
    Version = $Version
    ZipPath = $ZipPath
    Sha256 = $hash.Hash
    HashPath = $HashPath
  } | ConvertTo-Json
}
finally {
  Pop-Location
  if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
  }
}
