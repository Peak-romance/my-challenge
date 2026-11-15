<#
.SYNOPSIS
    在当前 PowerShell 会话中准备 Hermes Agent 运行环境（dot-source 使用）。

.DESCRIPTION
    本机实测有三个反复出现的环境问题，每次手动处理很烦，这里一次性收敛：

    1. 中文乱码：Windows 控制台默认代码页 936(GBK)，Hermes 输出 UTF-8，
       中文与边框符号会变成乱码 → 强制 Console 输出编码为 UTF-8。
    2. PATH 未生效：安装器写的是「用户级 PATH」，已打开的窗口读不到 →
       本会话内直接前置 %LOCALAPPDATA%\hermes\bin。
    3. 依赖下载极慢：PyPI 直连约 90 KB/s → 指向国内镜像（仅影响后续
       pip/uv/npm 安装，不影响 hermes 运行时）。

.EXAMPLE
    . .\hermes-env.ps1          # 点号引入，变量才会留在当前会话
    . .\hermes-env.ps1 -Quiet   # 不打印横幅
#>

[CmdletBinding()]
param(
    [switch]$Quiet
)

# 1) 编码
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

# 2) PATH
$hermesHome = Join-Path $env:LOCALAPPDATA 'hermes'
$hermesBin  = Join-Path $hermesHome 'bin'
if (Test-Path $hermesBin) {
    $parts = $env:PATH -split ';'
    if ($parts -notcontains $hermesBin) {
        $env:PATH = $hermesBin + ';' + $env:PATH
    }
}

# 3) 镜像（只对后续包安装生效）
if (-not $env:UV_INDEX_URL)          { $env:UV_INDEX_URL = 'https://mirrors.ustc.edu.cn/pypi/simple' }
if (-not $env:npm_config_registry)   { $env:npm_config_registry = 'https://registry.npmmirror.com' }
if (-not $env:UV_HTTP_TIMEOUT)       { $env:UV_HTTP_TIMEOUT = '120' }

# 便捷函数
function Get-HermesVersion {
    $exe = Join-Path $hermesBin 'hermes.exe'
    if (Test-Path $exe) { & $exe --version } else { Write-Warning "未找到 $exe" }
}
function Invoke-HermesDoctor {
    $exe = Join-Path $hermesBin 'hermes.exe'
    # 注意：本机沙箱的程序黑名单会拦截 schtasks.exe，
    # doctor 的 Gateway Service 段可能因此中断，属环境限制（详见交付文档）。
    & $exe doctor
}
function Invoke-DeliveryAudit {
    param([string]$Root = 'D:\')
    $script = Join-Path $hermesHome 'skills\c10h-delivery-audit\scripts\audit.py'
    & python $script --root $Root
}

Set-Alias -Name hermes -Value (Join-Path $hermesBin 'hermes.exe') -Scope Global -Force -ErrorAction SilentlyContinue

if (-not $Quiet) {
    $exe = Join-Path $hermesBin 'hermes.exe'
    if (Test-Path $exe) {
        $v = (& $exe --version 2>&1 | Select-Object -First 1)
        Write-Host "[env] Hermes 环境就绪 · UTF-8 控制台 · PATH 已前置" -ForegroundColor Green
        Write-Host "[env] $v" -ForegroundColor DarkGray
        Write-Host "[env] 可用命令: hermes / Get-HermesVersion / Invoke-HermesDoctor / Invoke-DeliveryAudit" -ForegroundColor DarkGray
    } else {
        Write-Warning "[env] 未找到 $exe，请先完成安装"
    }
}
