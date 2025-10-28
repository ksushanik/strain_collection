<#
  Mass import GitHub Actions secrets from an env file (Windows PowerShell).

  Usage examples:
    # Dry run preview
    .\scripts\import_github_secrets.ps1 -Repo "ksushanik/strain_collection" -DryRun

    # Import from default env path and set SSH key from file
    .\scripts\import_github_secrets.ps1 -Repo "ksushanik/strain_collection" -EnvPath ".github\prod.secrets.env" -SshKeyPath "C:\Users\you\.ssh\id_ed25519"

  Notes:
    - Expects lines in the form KEY=VALUE; ignores comments and empty lines.
    - Skips PROD_SSH_KEY in the env file; it must be provided via -SshKeyPath to preserve multiline content.
    - Requires GitHub CLI: https://cli.github.com/ (gh auth login before running).
#>

param(
  [Parameter(Mandatory = $true)] [string] $Repo,
  [string] $EnvPath = ".github\prod.secrets.env",
  [string] $SshKeyPath,
  [switch] $DryRun
)

function Require-Command {
  param([string] $Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    Write-Error "Required command '$Name' not found. Install it and retry." -ErrorAction Stop
  }
}

try {
  Require-Command "gh"
} catch {
  exit 1
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
  Write-Error "Env file not found: $EnvPath" -ErrorAction Stop
}

try {
  $raw = Get-Content -LiteralPath $EnvPath -Raw -Encoding UTF8
} catch {
  Write-Error "Failed to read env file '$EnvPath': $_" -ErrorAction Stop
}

$lines = $raw -split "`r`n|`n|`r"
$pairs = @()

foreach ($line in $lines) {
  $trim = $line.Trim()
  if ($trim -eq "" -or $trim.StartsWith('#')) { continue }
  $idx = $trim.IndexOf('=')
  if ($idx -lt 1) {
    Write-Warning "Skipping malformed line: $line"
    continue
  }
  $key = $trim.Substring(0, $idx).Trim()
  $val = $trim.Substring($idx + 1)
  if ($key -eq 'PROD_SSH_KEY') { continue }
  $pairs += [pscustomobject]@{ Key = $key; Value = $val }
}

Write-Host "Importing $($pairs.Count) secrets to repo '$Repo'" -ForegroundColor Cyan

foreach ($p in $pairs) {
  if ($DryRun) {
    Write-Host ("DRY RUN: gh secret set {0} -b <redacted> -R {1}" -f $p.Key, $Repo)
    continue
  }

  $result = gh secret set $p.Key -b $p.Value -R $Repo 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set '$($p.Key)': $result"
    exit 1
  } else {
    Write-Host ("Set {0}" -f $p.Key) -ForegroundColor Green
  }
}

if ($SshKeyPath) {
  if (-not (Test-Path -LiteralPath $SshKeyPath)) {
    Write-Error "SSH key file not found: $SshKeyPath" -ErrorAction Stop
  }
  try {
    $sshContent = Get-Content -LiteralPath $SshKeyPath -Raw -Encoding UTF8
  } catch {
    Write-Error "Failed to read SSH key file '$SshKeyPath': $_" -ErrorAction Stop
  }

  if ($DryRun) {
    Write-Host ("DRY RUN: gh secret set PROD_SSH_KEY -b <content from {0}> -R {1}" -f $SshKeyPath, $Repo)
  } else {
    $result = gh secret set PROD_SSH_KEY -b $sshContent -R $Repo 2>&1
    if ($LASTEXITCODE -ne 0) {
      Write-Error "Failed to set 'PROD_SSH_KEY': $result"
      exit 1
    } else {
      Write-Host "Set PROD_SSH_KEY" -ForegroundColor Green
    }
  }
} else {
  Write-Host "Note: Provide -SshKeyPath to set the multiline secret 'PROD_SSH_KEY'." -ForegroundColor Yellow
}

Write-Host "All done." -ForegroundColor Cyan