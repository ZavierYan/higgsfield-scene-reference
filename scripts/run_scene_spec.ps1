$ErrorActionPreference = "Stop"
$SceneSpecArgs = @($args)
$scriptPath = Join-Path $PSScriptRoot "scene_spec.py"
$candidates = [System.Collections.Generic.List[string]]::new()

if ($env:SCENE_SPEC_PYTHON) {
    $candidates.Add($env:SCENE_SPEC_PYTHON)
}

foreach ($commandName in @("python3.exe", "python.exe")) {
    Get-Command $commandName -All -ErrorAction SilentlyContinue |
        ForEach-Object { $candidates.Add($_.Source) }
}

$localPythonRoot = Join-Path $env:LOCALAPPDATA "Python"
if (Test-Path -LiteralPath $localPythonRoot) {
    Get-ChildItem -LiteralPath $localPythonRoot -Directory -Filter "pythoncore-*" |
        ForEach-Object {
            $candidate = Join-Path $_.FullName "python.exe"
            if (Test-Path -LiteralPath $candidate) {
                $candidates.Add($candidate)
            }
        }
}

$msysPython = "C:\msys64\clang64\bin\python.exe"
if (Test-Path -LiteralPath $msysPython) {
    $candidates.Add($msysPython)
}

$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($python in $candidates) {
    if (-not $seen.Add($python)) {
        continue
    }
    try {
        & $python -c "import yaml" 2>$null
        if ($LASTEXITCODE -ne 0) {
            continue
        }
        & $python $scriptPath @SceneSpecArgs
        exit $LASTEXITCODE
    }
    catch {
        continue
    }
}

Write-Error "No working Python with PyYAML was found. Set SCENE_SPEC_PYTHON to a compatible interpreter."
exit 1
