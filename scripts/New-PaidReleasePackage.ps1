param(
  [string]$Version = "0.2.0",
  [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $ScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $OutputRoot = Join-Path (Split-Path -Parent $RepoRoot) "Academic_Research_Workflow_Agents_Releases"
}
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
$ArchiveBaseName = "Academic_Research_Assistant_AI_Agents_v$Version"
$StageRoot = Join-Path ([System.IO.Path]::GetTempPath()) "$ArchiveBaseName-stage"
$StageDir = Join-Path $StageRoot $ArchiveBaseName
$ZipPath = Join-Path $OutputRoot "$ArchiveBaseName.zip"
$HashPath = "$ZipPath.sha256.txt"

function Assert-SafeStagePath {
  param([string]$Path)
  $resolved = [System.IO.Path]::GetFullPath($Path)
  $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
  if (-not $resolved.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing stage path outside the system temp directory: $resolved"
  }
}

function Test-ExcludedPath {
  param([string]$Path)
  $normalized = $Path -replace "\\", "/"
  $fileName = [System.IO.Path]::GetFileName($normalized)

  if ($normalized -match "^distribution/public-preview(/|$)") {
    return $true
  }
  if ($normalized -match "^scripts/(sync-public-preview|public-preview-lib)\.mjs$") {
    return $true
  }
  if ($normalized -eq "tests/test_public_preview.mjs") {
    return $true
  }

  if ($normalized -match "(^|/)(outputs|node_modules|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.venv|venv|env|build|dist|coverage|archive|archives|archived_runs|private|real_data)(/|$)") {
    return $true
  }
  if ($normalized -match "(^|/)\.git") {
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

Assert-SafeStagePath -Path $StageRoot
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Push-Location $RepoRoot
try {
  & npm run check:terminology
  if ($LASTEXITCODE -ne 0) {
    throw "Terminology check failed."
  }

  $SavedGitIndexFile = $env:GIT_INDEX_FILE
  try {
    Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue
    & node scripts/sync-public-preview.mjs --check
    if ($LASTEXITCODE -ne 0) {
      throw "Public preview drift check failed. Sync the preview repository before packaging."
    }
  }
  finally {
    if ([string]::IsNullOrWhiteSpace($SavedGitIndexFile)) {
      Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue
    }
    else {
      $env:GIT_INDEX_FILE = $SavedGitIndexFile
    }
  }

  $TrackedFiles = @(git ls-files)
  $RequiredTrackedFiles = @(
    "README.md",
    "TERMS.md",
    "VERSION.txt",
    "package.json",
    "Subagent_check/AGENTS.md",
    "Subagent_evidence/AGENTS.md",
    "Subagent_format_latex/AGENTS.md",
    "Subagent_integrate/AGENTS.md",
    "Subagent_presentation/AGENTS.md",
    "Subagent_process_data/AGENTS.md",
    "Subagent_regress_stata/AGENTS.md"
  )
  foreach ($RequiredPath in $RequiredTrackedFiles) {
    if ($TrackedFiles -notcontains $RequiredPath) {
      throw "Required release file is not tracked: $RequiredPath"
    }
  }
  $UntrackedProductFiles = @(git ls-files --others --exclude-standard -- "Subagent_*" "package.json" "README.md" "TERMS.md" "VERSION.txt")
  if ($UntrackedProductFiles.Count -gt 0) {
    throw "Refusing release with untracked product files: $($UntrackedProductFiles -join ', ')"
  }
  $RepositoryVersion = (Get-Content -LiteralPath (Join-Path $RepoRoot "VERSION.txt") -Raw).Trim()
  if ($Version -ne $RepositoryVersion) {
    throw "Requested version $Version does not match VERSION.txt ($RepositoryVersion)."
  }
  if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

  foreach ($RelativePath in $TrackedFiles) {
    if (Test-ExcludedPath -Path $RelativePath) {
      continue
    }
    $Source = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
      continue
    }
    $Target = Join-Path $StageDir $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Target -Force
  }

  $PackageJsonPath = Join-Path $StageDir "package.json"
  if (Test-Path -LiteralPath $PackageJsonPath) {
    $PackageJson = Get-Content -LiteralPath $PackageJsonPath -Raw | ConvertFrom-Json
    $FilteredScripts = [ordered]@{}
    foreach ($Property in $PackageJson.scripts.PSObject.Properties) {
      if ($Property.Name -notin @("preview:check", "preview:sync", "release:private", "test:preview")) {
        $FilteredScripts[$Property.Name] = $Property.Value
      }
    }
    $PackageJson.scripts = $FilteredScripts
    $PackageJson | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $PackageJsonPath -Encoding UTF8
  }

  Set-Content -LiteralPath (Join-Path $StageDir "VERSION.txt") -Value $Version -Encoding UTF8
  if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
  }
  if (Test-Path -LiteralPath $HashPath) {
    Remove-Item -LiteralPath $HashPath -Force
  }

  Compress-Archive -LiteralPath $StageDir -DestinationPath $ZipPath -CompressionLevel Optimal
  $Hash = Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256
  Set-Content -LiteralPath $HashPath -Value "$($Hash.Hash)  $([System.IO.Path]::GetFileName($ZipPath))" -Encoding ASCII

  [pscustomobject]@{
    Product = "Academic Research Assistant AI Agents"
    Version = $Version
    ZipPath = $ZipPath
    Sha256 = $Hash.Hash
    HashPath = $HashPath
  } | ConvertTo-Json
}
finally {
  Pop-Location
  Assert-SafeStagePath -Path $StageRoot
  if (Test-Path -LiteralPath $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
  }
}
