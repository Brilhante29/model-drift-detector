param(
  [switch]$SkipDocker,
  [switch]$AllowPendingEvidence
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
  param([string]$Message)
  $script:failures.Add($Message)
}

function Require-File {
  param([string]$RelativePath)
  $path = Join-Path $root $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    Add-Failure "Missing file: $RelativePath"
  }
}

function Invoke-Checked {
  param(
    [string]$Label,
    [scriptblock]$Command
  )
  & $Command
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    Add-Failure "$Label failed with exit code $exitCode"
  }
  $global:LASTEXITCODE = 0
}

$requiredFiles = @(
  "README.md",
  "project.yaml",
  "REFERENCES.md",
  "AGENTS.md",
  "openspec/config.yaml",
  "openspec/artifacts/intent.md",
  "openspec/artifacts/portfolio-impact.md",
  "openspec/artifacts/architecture-record.md",
  "openspec/artifacts/component-pack.md",
  "openspec/artifacts/reuse-delta.md",
  "openspec/artifacts/benchmark-proof.md",
  "openspec/artifacts/tasks.md",
  "openspec/artifacts/verification.md",
  "openspec/artifacts/article-draft.md",
  "openspec/artifacts/voice-check.md",
  "sdd/spec.md",
  "sdd/benchmark-plan.md",
  "sdd/architecture-decision.md",
  "sdd/technical-decision.md",
  "sdd/agent-handoff.md",
  "sdd/reuse-improvement-review.md"
)
foreach ($file in $requiredFiles) { Require-File $file }

$manifestPath = Join-Path $root "project.yaml"
$manifestPrimaryMetric = ""
$manifestResultPath = ""
$manifestEvidenceStatus = ""
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
  $manifestText = Get-Content -Raw -LiteralPath $manifestPath
  if ($manifestText.Contains("`t")) {
    Add-Failure "project.yaml must not contain tab indentation"
  }

  $requiredTopLevelKeys = @("id", "name", "program", "status", "stack", "benchmark", "release")
  foreach ($key in $requiredTopLevelKeys) {
    if ($manifestText -notmatch "(?m)^$([regex]::Escape($key)):\s*") {
      Add-Failure "project.yaml is missing top-level key: $key"
    }
  }

  foreach ($line in ($manifestText -split "`r?`n")) {
    if ($line -match "^( +)\S" -and ($Matches[1].Length % 2) -ne 0) {
      Add-Failure "project.yaml indentation must use multiples of two spaces"
      break
    }
  }

  $primaryMetricMatch = [regex]::Match($manifestText, "(?m)^\s+primary_metric:\s*([^\r\n#]+)")
  if ($primaryMetricMatch.Success) {
    $manifestPrimaryMetric = $primaryMetricMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
  } else {
    Add-Failure "project.yaml is missing benchmark.primary_metric"
  }

  $resultPathMatch = [regex]::Match($manifestText, "(?m)^\s+result_path:\s*([^\r\n#]+)")
  if ($resultPathMatch.Success) {
    $manifestResultPath = $resultPathMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
  } else {
    Add-Failure "project.yaml is missing benchmark.result_path"
  }
  $evidenceStatusMatch = [regex]::Match(
    $manifestText,
    "(?m)^\s+evidence_status:\s*([^\r\n#]+)"
  )
  if ($evidenceStatusMatch.Success) {
    $manifestEvidenceStatus = $evidenceStatusMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
    if ($manifestEvidenceStatus -ne "current" -and -not $AllowPendingEvidence) {
      Add-Failure "Benchmark evidence is not current: $manifestEvidenceStatus"
    }
  } else {
    Add-Failure "project.yaml is missing benchmark.evidence_status"
  }

  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    & python -c "import yaml" 2>$null
    $yamlAvailable = $LASTEXITCODE -eq 0
    $global:LASTEXITCODE = 0
    if ($yamlAvailable) {
      Invoke-Checked "project YAML parsing" { python -c "import pathlib, sys, yaml; data = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')); assert isinstance(data, dict)" $manifestPath }
    } else {
      Write-Host "yaml_parser=not_found; structural manifest validation applied"
    }
  }
}
$reuseReviewPath = Join-Path $root "sdd/reuse-improvement-review.md"
if (Test-Path -LiteralPath $reuseReviewPath -PathType Leaf) {
  $reuseReview = Get-Content -Raw -LiteralPath $reuseReviewPath
  if ($reuseReview -match "<id>|<project-name>") {
    Add-Failure "Reuse improvement review still contains template placeholders"
  }
  if ($reuseReview.Contains('|  | `patch_now|backlog|reject` |')) {
    Add-Failure "Reuse improvement review still contains the blank template finding row"
  }
  $requiredFinalGatePatterns = @(
    "(?m)^- \[x\] Reusable improvements were patched or recorded\.\r?$",
    "(?m)^- \[x\] Project-specific implementation was not moved into the kit\.\r?$",
    "(?m)^- \[x\] Validation reflects .+\.\r?$"
  )
  foreach ($pattern in $requiredFinalGatePatterns) {
    if ($reuseReview -notmatch $pattern) {
      Add-Failure "Reuse improvement review final gate is incomplete: $pattern"
    }
  }
}

$benchmarkFiles = @()
$benchmarkDir = Join-Path $root "benchmarks/results"
if (Test-Path -LiteralPath $benchmarkDir -PathType Container) {
  $benchmarkFiles = @(Get-ChildItem -LiteralPath $benchmarkDir -Filter *.json -File)
}
if ($benchmarkFiles.Count -eq 0 -and -not $AllowPendingEvidence) {
  Add-Failure "Missing benchmark JSON under benchmarks/results"
}

if ($manifestResultPath -ne "") {
  $primaryResultPath = $root
  foreach ($part in ($manifestResultPath -split "[/\\]")) {
    if ($part -ne "") {
      $primaryResultPath = Join-Path $primaryResultPath $part
    }
  }

  if (-not (Test-Path -LiteralPath $primaryResultPath -PathType Leaf)) {
    if (-not $AllowPendingEvidence) {
      Add-Failure "Manifest benchmark result does not exist: $manifestResultPath"
    }
  } else {
    try {
      $primaryResult = Get-Content -Raw -LiteralPath $primaryResultPath | ConvertFrom-Json
      $resultMetric = ""
      $resultValue = $null
      if ($primaryResult.PSObject.Properties.Name -contains "metric") {
        $resultMetric = [string]$primaryResult.metric
        $resultValue = $primaryResult.value
      } elseif ($primaryResult.PSObject.Properties.Name -contains "primary_metric") {
        $resultMetric = [string]$primaryResult.primary_metric
        $metricProperty = $primaryResult.PSObject.Properties[$resultMetric]
        if ($null -ne $metricProperty) {
          $resultValue = $metricProperty.Value
        }
      }

      if ($resultMetric -eq "" -or $null -eq $resultValue) {
        Add-Failure "Benchmark result must expose metric/value or primary_metric with its value"
      } else {
        if ($manifestPrimaryMetric -ne "" -and $resultMetric -ne $manifestPrimaryMetric) {
          Add-Failure "Benchmark metric mismatch: project.yaml=$manifestPrimaryMetric result=$resultMetric"
        }
        $readmePath = Join-Path $root "README.md"
        if (Test-Path -LiteralPath $readmePath -PathType Leaf) {
          $readmeOpening = ((Get-Content -LiteralPath $readmePath -TotalCount 8) -join "`n").Replace(",", "")
          $valueText = [Convert]::ToString($resultValue, [System.Globalization.CultureInfo]::InvariantCulture)
          if (-not $readmeOpening.Contains($valueText)) {
            Add-Failure "README opening does not include primary benchmark value: $valueText"
          }
        }
      }
    } catch {
      Add-Failure "Cannot read primary benchmark result: $($_.Exception.Message)"
    }
  }
}
Push-Location -LiteralPath $root
try {
  foreach ($file in $benchmarkFiles) {
    Invoke-Checked "benchmark JSON validation: $($file.Name)" { python -m json.tool $file.FullName | Out-Null }
  }

  $srcRoot = Join-Path $root "src"
  $pythonFiles = @()
  if (Test-Path -LiteralPath $srcRoot -PathType Container) {
    $pythonFiles = @(Get-ChildItem -Path $srcRoot -Recurse -Filter *.py -File)
  }
  if ($pythonFiles.Count -gt 0) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
      $previousPythonPath = $env:PYTHONPATH
      if ($previousPythonPath) {
        $env:PYTHONPATH = $srcRoot + [System.IO.Path]::PathSeparator + $previousPythonPath
      } else {
        $env:PYTHONPATH = $srcRoot
      }
      Invoke-Checked "python compile src" { python -m compileall -q $srcRoot }
      $testsRoot = Join-Path $root "tests"
      $pythonTests = @()
      if (Test-Path -LiteralPath $testsRoot -PathType Container) {
        $pythonTests = @(Get-ChildItem -Path $testsRoot -Recurse -Filter *.py -File)
      }
      if ($pythonTests.Count -gt 0) {
        Invoke-Checked "python compile tests" { python -m compileall -q $testsRoot }
        $dockerfile = Join-Path $root "Dockerfile"
        if (Test-Path -LiteralPath $dockerfile -PathType Leaf) {
          Write-Host "python_tests=deferred_to_project_container_workflow"
        } else {
          $pyprojectPath = Join-Path $root "pyproject.toml"
          $usesPytest = $false
          if (Test-Path -LiteralPath $pyprojectPath -PathType Leaf) {
            $pyprojectText = Get-Content -Raw -LiteralPath $pyprojectPath
            $usesPytest = $pyprojectText -match "(?im)pytest"
          }
          if ($usesPytest) {
            $pytestCommand = Get-Command pytest -ErrorAction SilentlyContinue
            if ($pytestCommand) {
              Invoke-Checked "python pytest" { python -m pytest -q $testsRoot }
            } else {
              Add-Failure "pytest is required for this non-Docker Python project"
            }
          } else {
            Invoke-Checked "python unittest" { python -m unittest discover -s $testsRoot -v }
          }
        }
      }
      $env:PYTHONPATH = $previousPythonPath
    } elseif ($SkipDocker) {
      Add-Failure "Python toolchain is required to validate Python source when Docker validation is skipped"
    } else {
      Write-Host "python_toolchain=not_found; relying on Docker build for Python validation"
    }
  }
  $goModPath = Join-Path $root "go.mod"
  if (Test-Path -LiteralPath $goModPath -PathType Leaf) {
    $goCommand = Get-Command go -ErrorAction SilentlyContinue
    if ($goCommand) {
      $goFiles = @(Get-ChildItem -Path $root -Recurse -Filter *.go -File | Where-Object {
        $normalized = $_.FullName -replace "\\", "/"
        $normalized -notmatch "/.git/" -and
        $normalized -notmatch "/.portfolio/" -and
        $normalized -notmatch "/vendor/"
      })
      if ($goFiles.Count -gt 0) {
        $unformatted = @(& gofmt -l $goFiles.FullName)
        if ($LASTEXITCODE -ne 0) {
          Add-Failure "gofmt failed with exit code $LASTEXITCODE"
          $global:LASTEXITCODE = 0
        } elseif ($unformatted.Count -gt 0) {
          Add-Failure "Go files require gofmt: $($unformatted -join ', ')"
        }
      }
      Invoke-Checked "go test" { go test ./... }
      Invoke-Checked "go vet" { go vet ./... }
    } elseif ($SkipDocker) {
      Add-Failure "Go toolchain is required to validate go.mod projects when Docker validation is skipped"
    } else {
      Write-Host "go_toolchain=not_found; relying on Docker build for Go validation"
    }
  }
  $gradleBuild = @(
    (Join-Path $root "build.gradle.kts"),
    (Join-Path $root "build.gradle")
  ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
  if ($gradleBuild.Count -gt 0) {
    $wrapperFiles = @(
      "gradlew",
      "gradlew.bat",
      "gradle/wrapper/gradle-wrapper.jar",
      "gradle/wrapper/gradle-wrapper.properties"
    )
    $missingWrapper = @($wrapperFiles | Where-Object {
      -not (Test-Path -LiteralPath (Join-Path $root $_) -PathType Leaf)
    })
    foreach ($missing in $missingWrapper) {
      Add-Failure "Gradle project is missing wrapper file: $missing"
    }

    if ($missingWrapper.Count -eq 0) {
      $javaCommand = Get-Command java -ErrorAction SilentlyContinue
      if ($javaCommand) {
        $isWindowsHost = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
        if ($isWindowsHost) {
          $gradleWrapper = Join-Path $root "gradlew.bat"
          Invoke-Checked "gradle check" { & $gradleWrapper check --no-daemon }
        } else {
          $gradleWrapper = Join-Path $root "gradlew"
          Invoke-Checked "gradle check" { & $gradleWrapper check --no-daemon }
        }
      } elseif ($SkipDocker) {
        Add-Failure "Java toolchain is required to validate Gradle projects when Docker validation is skipped"
      } else {
        Write-Host "java_toolchain=not_found; relying on Docker build for Gradle validation"
      }
    }
  }
} finally {
  Pop-Location
}

$legacy = ("ro" + "che" + "do")
$patterns = @($legacy, ($legacy.Substring(0,1).ToUpper() + $legacy.Substring(1)))
$searchFiles = Get-ChildItem -Path $root -Recurse -File | Where-Object {
  $normalized = $_.FullName -replace "\\", "/"
  $normalized -notmatch "/.git/" -and
  $normalized -notmatch "/data/runtime/" -and
  $_.Extension -in @(".md", ".yaml", ".yml", ".json", ".ps1", ".py", ".js", ".ts", ".tsx", ".go", ".kt", ".java")
}
foreach ($file in $searchFiles) {
  $content = [IO.File]::ReadAllText($file.FullName)
  if ($content -match '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]') {
    $relative = $file.FullName.Substring($root.Length).TrimStart([char]92, [char]47)
    Add-Failure "Invalid control character found in text file: $relative"
  }
}
$forbidden = Select-String -Path $searchFiles.FullName -Pattern $patterns -SimpleMatch -ErrorAction SilentlyContinue
if ($forbidden) {
  Add-Failure "Forbidden legacy project nickname found"
}

$mutableKumoPattern = "ghcr.io/sivchari/kumo:" + "latest"
$mutableKumo = Select-String -Path $searchFiles.FullName -Pattern $mutableKumoPattern -SimpleMatch -ErrorAction SilentlyContinue
if ($mutableKumo) {
  Add-Failure "Mutable Kumo image reference found; pin a reviewed tag and digest"
}

$dockerfilePath = Join-Path $root "Dockerfile"
if (Test-Path -LiteralPath $dockerfilePath -PathType Leaf) {
  $dockerfileText = Get-Content -Raw -LiteralPath $dockerfilePath
  $airflowBase = [regex]::Match($dockerfileText, "(?m)^FROM\s+apache/airflow:[^\s]+")
  if ($airflowBase.Success -and $airflowBase.Value -notmatch "@sha256:[a-f0-9]{64}$") {
    Add-Failure "Mutable Airflow base image found; pin a reviewed tag and OCI digest"
  }
  if ($airflowBase.Success -and $dockerfileText -notmatch 'apache-airflow==') {
    Add-Failure "Airflow image extension must retain the exact apache-airflow package version"
  }
}
$dependencyFiles = @("requirements.txt", "pyproject.toml") | ForEach-Object {
  Join-Path $root $_
} | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
$dependencyText = ($dependencyFiles | ForEach-Object {
  Get-Content -Raw -LiteralPath $_
}) -join [Environment]::NewLine
if ($dependencyText -match '(?im)\bultralytics(?:\[.*?\])?\s*==') {
  $licensePath = Join-Path $root "LICENSE"
  $referencesPath = Join-Path $root "REFERENCES.md"
  $licenseText = if (Test-Path -LiteralPath $licensePath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $licensePath
  } else {
    ""
  }
  $referencesText = if (Test-Path -LiteralPath $referencesPath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $referencesPath
  } else {
    ""
  }
  $licenseDecisionRecorded = (
    $licenseText -match "(?i)AGPL-3.0" -or
    $licenseText -match "(?i)Ultralytics Enterprise"
  )
  if (-not $licenseDecisionRecorded) {
    Add-Failure "Ultralytics projects must record AGPL-3.0 or an applicable Enterprise license in LICENSE"
  }
  if (
    $referencesText -notmatch "(?i)Ultralytics" -or
    $referencesText -notmatch "(?i)AGPL-3.0|Enterprise"
  ) {
    Add-Failure "Ultralytics projects must attribute the framework and license decision in REFERENCES.md"
  }
}
$modelArtifactMatch = [regex]::Match(
  $manifestText,
  '(?ms)^model_artifact:\s*\r?\n(?<body>.*?)(?=^\S|\z)'
)
if ($modelArtifactMatch.Success) {
  $modelArtifactBlock = $modelArtifactMatch.Groups["body"].Value
  $artifactValues = @{}
  $artifactFields = @(
    "role",
    "schema_version",
    "contract_path",
    "manifest_name",
    "checkpoint_name",
    "integrity",
    "evaluation_split",
    "latency_protocol",
    "runtime_network_required"
  )
  foreach ($field in $artifactFields) {
    $fieldMatch = [regex]::Match(
      $modelArtifactBlock,
      "(?m)^\s+$([regex]::Escape($field)):\s*([^\r\n#]+)"
    )
    if ($fieldMatch.Success) {
      $artifactValues[$field] = $fieldMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
    }
  }

  foreach ($requiredField in @(
    "role",
    "schema_version",
    "contract_path",
    "manifest_name",
    "checkpoint_name",
    "integrity",
    "runtime_network_required"
  )) {
    if (-not $artifactValues.ContainsKey($requiredField)) {
      Add-Failure "model_artifact is missing field: $requiredField"
    }
  }

  if ($artifactValues["schema_version"] -ne "1") {
    Add-Failure "model_artifact.schema_version must be 1"
  }
  if ($artifactValues["runtime_network_required"] -ne "false") {
    Add-Failure "The reusable model artifact path must not require runtime network access"
  }

  $contractRelativePath = $artifactValues["contract_path"]
  if ($contractRelativePath) {
    $contractPath = Join-Path $root $contractRelativePath
    if (-not (Test-Path -LiteralPath $contractPath -PathType Leaf)) {
      Add-Failure "Missing model artifact contract: $contractRelativePath"
    } else {
      try {
        Get-Content -Raw -LiteralPath $contractPath | ConvertFrom-Json | Out-Null
      } catch {
        Add-Failure "Cannot parse model artifact contract: $contractRelativePath"
      }
    }
  }

  $readmePath = Join-Path $root "README.md"
  $readmeText = if (Test-Path -LiteralPath $readmePath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $readmePath
  } else {
    ""
  }
  foreach ($artifactNameField in @("manifest_name", "checkpoint_name")) {
    $artifactName = $artifactValues[$artifactNameField]
    if ($artifactName -and -not $readmeText.Contains($artifactName)) {
      Add-Failure "README must document model_artifact.$artifactNameField=$artifactName"
    }
  }

  $srcPath = Join-Path $root "src"
  $implementationFiles = if (Test-Path -LiteralPath $srcPath -PathType Container) {
    @(Get-ChildItem -Path $srcPath -Recurse -File | Where-Object {
      $_.Extension -in @(".py", ".go", ".java", ".kt", ".ts", ".tsx")
    })
  } else {
    @()
  }
  $implementationText = ($implementationFiles | ForEach-Object {
    Get-Content -Raw -LiteralPath $_.FullName
  }) -join [Environment]::NewLine

  switch ($artifactValues["role"]) {
    "producer" {
      if ($artifactValues["integrity"] -ne "sha256-before-publication") {
        Add-Failure "Model producers must use integrity=sha256-before-publication"
      }
      if ($artifactValues["evaluation_split"] -ne "held-out") {
        Add-Failure "Model producers must use evaluation_split=held-out"
      }
      if ($artifactValues["latency_protocol"] -ne "reload-warmup-measure") {
        Add-Failure "Model producers must use latency_protocol=reload-warmup-measure"
      }
      foreach ($pattern in @("model-manifest\.json", "sha256", "validate_model_manifest")) {
        if ($implementationText -notmatch $pattern) {
          Add-Failure "Model producer implementation is missing evidence pattern: $pattern"
        }
      }
    }
    "consumer" {
      if ($artifactValues["integrity"] -ne "sha256-before-load") {
        Add-Failure "Model consumers must use integrity=sha256-before-load"
      }
      if ($artifactValues["latency_protocol"] -ne "load-warmup-measure") {
        Add-Failure "Model consumers must use latency_protocol=load-warmup-measure"
      }
      foreach ($pattern in @("model-manifest\.json", "sha256", "validat|verif")) {
        if ($implementationText -notmatch $pattern) {
          Add-Failure "Model consumer implementation is missing evidence pattern: $pattern"
        }
      }
    }
    default {
      Add-Failure "model_artifact.role must be producer or consumer"
    }
  }
}
$monitoringBatchMatch = [regex]::Match(
  $manifestText,
  '(?ms)^monitoring_batch:\s*\r?\n(?<body>.*?)(?=^\S|\z)'
)
if ($monitoringBatchMatch.Success) {
  $monitoringBlock = $monitoringBatchMatch.Groups["body"].Value
  $monitoringValues = @{}
  $monitoringFields = @(
    "role",
    "schema_version",
    "contract_path",
    "manifest_name",
    "supported_format",
    "integrity",
    "path_policy",
    "runtime_network_required"
  )
  foreach ($field in $monitoringFields) {
    $fieldMatch = [regex]::Match(
      $monitoringBlock,
      "(?m)^\s{2}$([regex]::Escape($field)):\s*(.+?)\s*$"
    )
    if ($fieldMatch.Success) {
      $monitoringValues[$field] = $fieldMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
    }
  }

  foreach ($requiredField in $monitoringFields) {
    if (-not $monitoringValues.ContainsKey($requiredField)) {
      Add-Failure "monitoring_batch is missing field: $requiredField"
    }
  }
  if ($monitoringValues["schema_version"] -ne "1") {
    Add-Failure "monitoring_batch.schema_version must be 1"
  }
  if ($monitoringValues["runtime_network_required"] -ne "false") {
    Add-Failure "The reusable monitoring batch path must not require runtime network access"
  }
  if ($monitoringValues["path_policy"] -ne "manifest-directory-only") {
    Add-Failure "monitoring_batch.path_policy must be manifest-directory-only"
  }
  if ($monitoringValues["supported_format"] -notin @("csv", "jsonl", "parquet")) {
    Add-Failure "monitoring_batch.supported_format must be csv, jsonl, or parquet"
  }

  $monitoringContractRelativePath = $monitoringValues["contract_path"]
  if ($monitoringContractRelativePath) {
    $monitoringContractPath = Join-Path $root $monitoringContractRelativePath
    if (-not (Test-Path -LiteralPath $monitoringContractPath -PathType Leaf)) {
      Add-Failure "Missing monitoring batch contract: $monitoringContractRelativePath"
    } else {
      try {
        Get-Content -Raw -LiteralPath $monitoringContractPath | ConvertFrom-Json | Out-Null
      } catch {
        Add-Failure "Cannot parse monitoring batch contract: $monitoringContractRelativePath"
      }
    }
  }

  $monitoringReadmePath = Join-Path $root "README.md"
  $monitoringReadme = if (Test-Path -LiteralPath $monitoringReadmePath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $monitoringReadmePath
  } else {
    ""
  }
  $monitoringManifestName = $monitoringValues["manifest_name"]
  if ($monitoringManifestName -and -not $monitoringReadme.Contains($monitoringManifestName)) {
    Add-Failure "README must document monitoring_batch.manifest_name=$monitoringManifestName"
  }

  $monitoringSource = Join-Path $root "src"
  $monitoringImplementationFiles = if (
    Test-Path -LiteralPath $monitoringSource -PathType Container
  ) {
    @(Get-ChildItem -Path $monitoringSource -Recurse -File | Where-Object {
      $_.Extension -in @(".py", ".go", ".java", ".kt", ".ts", ".tsx")
    })
  } else {
    @()
  }
  $monitoringImplementation = ($monitoringImplementationFiles | ForEach-Object {
    Get-Content -Raw -LiteralPath $_.FullName
  }) -join [Environment]::NewLine

  switch ($monitoringValues["role"]) {
    "producer" {
      if ($monitoringValues["integrity"] -ne "sha256-before-publication") {
        Add-Failure "Monitoring batch producers must use integrity=sha256-before-publication"
      }
      foreach ($pattern in @("sha256", "manifest", "write|publish")) {
        if ($monitoringImplementation -notmatch $pattern) {
          Add-Failure "Monitoring batch producer is missing evidence pattern: $pattern"
        }
      }
    }
    "consumer" {
      if ($monitoringValues["integrity"] -ne "sha256-before-parse") {
        Add-Failure "Monitoring batch consumers must use integrity=sha256-before-parse"
      }
      foreach ($pattern in @("sha256", "resolve", "read_bytes", "parse|DictReader")) {
        if ($monitoringImplementation -notmatch $pattern) {
          Add-Failure "Monitoring batch consumer is missing evidence pattern: $pattern"
        }
      }
    }
    default {
      Add-Failure "monitoring_batch.role must be producer or consumer"
    }
  }
}
if (-not $SkipDocker -and (Test-Path -LiteralPath (Join-Path $root "Dockerfile") -PathType Leaf)) {
  $imageName = (Split-Path -Leaf $root).ToLowerInvariant()
  Invoke-Checked "docker build" { docker build -t $imageName $root | Out-Null }
}

if ($failures.Count -gt 0) {
  $failures | ForEach-Object { [Console]::Error.WriteLine("ERROR: {0}", $_) }
  exit 1
}

Write-Host "portfolio project validation passed"
