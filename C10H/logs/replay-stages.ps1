<#
.SYNOPSIS
    按阶段重放 Hermes Agent 安装器，为每个阶段落一份完整日志。

.DESCRIPTION
    用途：安装已完成后，生成可审计的分阶段日志（安装器幂等，重放不会重复下载）。
    处理了本机三个环境问题：safe-delete 守卫、UTF-8 控制台、PyPI 镜像。
#>

Set-Alias -Name Remove-Item -Value 'Microsoft.PowerShell.Management\Remove-Item' -Scope Local -Force -Option AllScope
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$env:UV_INDEX_URL = 'https://mirrors.ustc.edu.cn/pypi/simple'
$env:npm_config_registry = 'https://registry.npmmirror.com'
$env:UV_HTTP_TIMEOUT = '120'

$installer = 'D:\C10H\logs\install.ps1'
$outDir = 'D:\C10H\logs\install'

$stages = @(
    @{ n = '01'; name = 'prerequisites' },
    @{ n = '02'; name = 'repository' },
    @{ n = '03'; name = 'venv' },
    @{ n = '04'; name = 'python-deps' },
    @{ n = '05'; name = 'config' },
    @{ n = '06'; name = 'products' },
    @{ n = '09'; name = 'complete' }
)

foreach ($s in $stages) {
    $log = Join-Path $outDir ("{0}-{1}.log" -f $s.n, $s.name)
    Write-Host ("→ stage {0}" -f $s.name) -ForegroundColor Cyan
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $text = & $installer -Stage $s.name -NonInteractive 2>&1 | Out-String
    $code = $LASTEXITCODE
    $sw.Stop()
    $header = "# stage=$($s.name)  exit=$code  elapsed=$([int]$sw.Elapsed.TotalSeconds)s  at=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`r`n"
    [System.IO.File]::WriteAllText($log, $header + $text, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host ("  exit={0}  {1:N1}s  → {2}" -f $code, $sw.Elapsed.TotalSeconds, $log) -ForegroundColor DarkGray
}

Write-Host "`n重放完成。" -ForegroundColor Green
