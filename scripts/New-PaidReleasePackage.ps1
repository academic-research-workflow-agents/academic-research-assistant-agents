param(
  [string]$Version = "0.1.0",
  [ValidateSet("thesis", "slides", "bundle", "all")]
  [string]$Package = "bundle",
  [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path -LiteralPath (Join-Path $ScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $OutputRoot = Join-Path (Split-Path -Parent $RepoRoot) "Academic_Research_Workflow_Agents_Releases"
}

$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)

function Get-PackageDefinition {
  param([string]$PackageName, [string]$Version)

  switch ($PackageName) {
    "thesis" {
      return [pscustomobject]@{
        Package = "thesis"
        ArchiveBaseName = "Academic_Thesis_Agent_v$Version"
        IncludedRoots = @("Thesis_Agent")
      }
    }
    "slides" {
      return [pscustomobject]@{
        Package = "slides"
        ArchiveBaseName = "Academic_Slides_Agent_Tex_v$Version"
        IncludedRoots = @("Slides_Agent_Tex")
      }
    }
    "bundle" {
      return [pscustomobject]@{
        Package = "bundle"
        ArchiveBaseName = "Academic_Research_Workflow_Agents_Bundle_v$Version"
        IncludedRoots = @("Thesis_Agent", "Slides_Agent_Tex")
      }
    }
    default {
      throw "Unsupported package: $PackageName"
    }
  }
}

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

function Test-IncludedPath {
  param(
    [string]$Path,
    [string[]]$IncludedRoots
  )

  $normalized = $Path -replace "\\", "/"
  $rootFiles = @("README.md", "TERMS.md", "VERSION.txt")
  if ($rootFiles -contains $normalized) {
    return $true
  }

  foreach ($root in $IncludedRoots) {
    if ($normalized -eq $root -or $normalized.StartsWith("$root/")) {
      return $true
    }
  }
  return $false
}

function New-OnePackage {
  param(
    [object]$Definition,
    [string[]]$TrackedFiles
  )

  $stageRoot = Join-Path $env:TEMP "$($Definition.ArchiveBaseName)-stage"
  $stageDir = Join-Path $stageRoot $Definition.ArchiveBaseName
  $zipPath = Join-Path $OutputRoot "$($Definition.ArchiveBaseName).zip"
  $hashPath = "$zipPath.sha256.txt"

  if (Test-Path -LiteralPath $stageRoot) {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Force -Path $stageDir | Out-Null

  try {
    foreach ($relativePath in $TrackedFiles) {
      if (Test-ExcludedPath -Path $relativePath) {
        continue
      }
      if (-not (Test-IncludedPath -Path $relativePath -IncludedRoots $Definition.IncludedRoots)) {
        continue
      }

      $source = Join-Path $RepoRoot $relativePath
      $target = Join-Path $stageDir $relativePath
      $targetParent = Split-Path -Parent $target
      New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
      Copy-Item -LiteralPath $source -Destination $target -Force
    }

    Set-Content -LiteralPath (Join-Path $stageDir "VERSION.txt") -Value $Version -Encoding UTF8

    if (Test-Path -LiteralPath $zipPath) {
      Remove-Item -LiteralPath $zipPath -Force
    }
    if (Test-Path -LiteralPath $hashPath) {
      Remove-Item -LiteralPath $hashPath -Force
    }

    Compress-Archive -LiteralPath $stageDir -DestinationPath $zipPath -CompressionLevel Optimal
    $hash = Get-FileHash -LiteralPath $zipPath -Algorithm SHA256
    Set-Content -LiteralPath $hashPath -Value "$($hash.Hash)  $([System.IO.Path]::GetFileName($zipPath))" -Encoding ASCII

    return [pscustomobject]@{
      Package = $Definition.Package
      Version = $Version
      ZipPath = $zipPath
      Sha256 = $hash.Hash
      HashPath = $hashPath
    }
  }
  finally {
    if (Test-Path -LiteralPath $stageRoot) {
      Remove-Item -LiteralPath $stageRoot -Recurse -Force
    }
  }
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Push-Location $RepoRoot
try {
  $trackedFiles = @(git ls-files)
  $packages = if ($Package -eq "all") { @("thesis", "slides", "bundle") } else { @($Package) }
  $results = foreach ($packageName in $packages) {
    $definition = Get-PackageDefinition -PackageName $packageName -Version $Version
    New-OnePackage -Definition $definition -TrackedFiles $trackedFiles
  }

  $results | ConvertTo-Json
}
finally {
  Pop-Location
}
