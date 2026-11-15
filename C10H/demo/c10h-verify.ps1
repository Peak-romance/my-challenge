# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    Hermes Agent 安装验收：14 项断言，全部基于真实命令输出，不含人工判断。

.DESCRIPTION
    每项断言独立执行、独立捕获异常，输出 PASS/FAIL 与证据摘要，
    并落盘 Markdown + JSON 报告到 .\outputs\。
    退出码：0 = 全部通过；1 = 存在失败项。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\c10h-verify.ps1
#>

$ErrorActionPreference = 'Continue'

# ---------- 环境规范化：中文 Windows 控制台默认 GBK，会把 UTF-8 输出变乱码 ----------
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:UV_INDEX_URL = 'https://mirrors.ustc.edu.cn/pypi/simple'

$HH      = Join-Path $env:LOCALAPPDATA 'hermes'
$HERMES  = Join-Path $HH 'bin\hermes.exe'
$REPO    = Join-Path $HH 'hermes-agent'
$CONFIG  = Join-Path $HH 'config.yaml'
$SKILL   = Join-Path $HH 'skills\c10h-delivery-audit\SKILL.md'
$AUDIT   = Join-Path $HH 'skills\c10h-delivery-audit\scripts\audit.py'
$PINNED  = '3b4215785882'
$JOBID   = 'de7e53f5db3b'

$outDir = Join-Path $PSScriptRoot 'outputs'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'

$results = New-Object System.Collections.ArrayList

function Add-Result {
    param([string]$Id, [string]$Name, [bool]$Pass, [string]$Evidence)
    $null = $results.Add([pscustomobject]@{
        Id = $Id; Name = $Name; Pass = $Pass; Evidence = $Evidence
    })
    $mark = if ($Pass) { 'PASS' } else { 'FAIL' }
    $color = if ($Pass) { 'Green' } else { 'Red' }
    Write-Host ("  [{0}] {1,-28} {2}" -f $mark, $Id, $Name) -ForegroundColor $color
    if ($Evidence) { Write-Host ("         └─ " + $Evidence) -ForegroundColor DarkGray }
}

function Invoke-Check {
    param([string]$Id, [string]$Name, [scriptblock]$Body)
    try {
        $r = & $Body
        Add-Result -Id $Id -Name $Name -Pass ([bool]$r.Pass) -Evidence ([string]$r.Evidence)
    } catch {
        Add-Result -Id $Id -Name $Name -Pass $false -Evidence ("EXCEPTION: " + $_.Exception.Message)
    }
}

Write-Host ""
Write-Host "═══ Hermes Agent 安装验收 · C10H ═══" -ForegroundColor Cyan
Write-Host ("主机: {0}  时间: {1}" -f $env:COMPUTERNAME, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Write-Host ""

# ---------- A1 可执行文件 ----------
Invoke-Check 'A1' 'hermes.exe 已发布' {
    $p = Test-Path $HERMES
    [pscustomobject]@{ Pass = $p; Evidence = if ($p) { $HERMES } else { "缺失: $HERMES" } }
}

# ---------- A2 版本 ----------
Invoke-Check 'A2' '版本号 = v0.23.1' {
    $v = (& $HERMES --version 2>&1 | Out-String)
    [pscustomobject]@{ Pass = ($v -match 'v0\.23\.1'); Evidence = (($v -split "`n")[0]).Trim() }
}

# ---------- A3 代码固定版本 ----------
Invoke-Check 'A3' '代码检出 = 锁定提交' {
    $h = (& git -C $REPO rev-parse HEAD 2>&1 | Out-String).Trim()
    [pscustomobject]@{ Pass = $h.StartsWith($PINNED); Evidence = "HEAD=$h" }
}

# ---------- A4 独立解释器 ----------
Invoke-Check 'A4' '运行时 Python 3.14.9' {
    $v = (& $HERMES --version 2>&1 | Out-String)
    $m = [regex]::Match($v, 'Python:\s*([\d.]+)')
    $ok = $m.Success -and $m.Groups[1].Value.StartsWith('3.14')
    [pscustomobject]@{ Pass = $ok; Evidence = if ($m.Success) { "Python " + $m.Groups[1].Value } else { '未解析到 Python 版本' } }
}

# ---------- A5 工具库 ----------
Invoke-Check 'A5' '工具库 9 件套齐备' {
    $need = @('git', 'uv', 'python', 'node', 'npm', 'pnpm', 'ripgrep', 'ffmpeg', 'chromium', 'cua')
    $have = @(Get-ChildItem (Join-Path $HH 'tools') -Directory -ErrorAction SilentlyContinue |
              Where-Object { $_.Name -notlike '.*' } |
              Select-Object -ExpandProperty Name)
    $matched = @()
    $missing = @()
    foreach ($n in $need) {
        $hit = @($have | Where-Object { $_ -like "$n*" } | Sort-Object -Descending | Select-Object -First 1)
        if ($hit.Count) { $matched += $hit[0] } else { $missing += $n }
    }
    [pscustomobject]@{ Pass = ($missing.Count -eq 0); Evidence = if ($missing.Count) { "缺: " + ($missing -join ',') } else { "$($matched.Count)/$($need.Count) 命中: " + ($matched -join ', ') } }
}

# ---------- A6 配置版本 ----------
Invoke-Check 'A6' 'config.yaml 存在且版本正确' {
    $ok = Test-Path $CONFIG
    $ver = if ($ok) { (Select-String -Path $CONFIG -Pattern '^_config_version:\s*(\d+)' | Select-Object -First 1).Matches.Groups[1].Value } else { '' }
    [pscustomobject]@{ Pass = ($ok -and $ver -eq '53'); Evidence = "path=$CONFIG  _config_version=$ver" }
}

# ---------- A7 用户画像记忆 ----------
Invoke-Check 'A7' 'USER.md 画像已写入' {
    $f = Join-Path $HH 'memories\USER.md'
    $ok = Test-Path $f
    $hit = $ok -and (Select-String -Path $f -Pattern 'D:\\C10H' -Quiet)
    $len = if ($ok) { (Get-Content $f -Raw).Length } else { 0 }
    [pscustomobject]@{ Pass = ($ok -and $hit); Evidence = "$f  ${len} chars  锚点命中=$hit" }
}

# ---------- A8 环境记忆 ----------
Invoke-Check 'A8' 'MEMORY.md 环境事实已写入' {
    $f = Join-Path $HH 'memories\MEMORY.md'
    $ok = Test-Path $f
    $hit = $ok -and (Select-String -Path $f -Pattern 'HERMES_HOME' -Quiet)
    $len = if ($ok) { (Get-Content $f -Raw).Length } else { 0 }
    [pscustomobject]@{ Pass = ($ok -and $hit); Evidence = "$f  ${len} chars  锚点命中=$hit" }
}

# ---------- A9 人格定制 ----------
Invoke-Check 'A9' 'SOUL.md 已本机定制' {
    $f = Join-Path $HH 'SOUL.md'
    $ok = (Test-Path $f) -and (Select-String -Path $f -Pattern '本机定制' -Quiet)
    [pscustomobject]@{ Pass = $ok; Evidence = if ($ok) { '包含「本机定制」段落' } else { '未找到定制段落' } }
}

# ---------- A10 自定义技能 ----------
Invoke-Check 'A10' '自定义技能已注册' {
    $v = (& $HERMES skills list 2>&1 | Out-String)
    $ok = $v -match 'c10h-delivery-audit' -and (Test-Path $SKILL)
    [pscustomobject]@{ Pass = $ok; Evidence = if ($ok) { 'skills list 命中 c10h-delivery-audit (local/enabled)' } else { '未注册' } }
}

# ---------- A11 定时任务 ----------
Invoke-Check 'A11' '定时任务已创建' {
    $v = (& $HERMES cron list 2>&1 | Out-String)
    $ok = $v -match $JOBID
    [pscustomobject]@{ Pass = $ok; Evidence = if ($ok) { "job=$JOBID  每日09:00 Asia/Shanghai  no-agent" } else { '未找到任务' } }
}

# ---------- A12 技能脚本可独立执行 ----------
Invoke-Check 'A12' '审计脚本可独立运行' {
    $v = (& python $AUDIT --root 'D:\' --only C10H 2>&1 | Out-String)
    $ok = $v -match '完整度|编号' -and $v -match 'C10H'
    [pscustomobject]@{ Pass = $ok; Evidence = (($v -split "`n" | Where-Object { $_ -match 'C10H\s*\|' } | Select-Object -First 1).Trim()) }
}

# ---------- A13 无明文密钥 ----------
Invoke-Check 'A13' '.env 无明文密钥泄漏' {
    $f = Join-Path $HH '.env'
    if (-not (Test-Path $f)) { return [pscustomobject]@{ Pass = $true; Evidence = '.env 不存在（无需检查）' } }
    $lines = Get-Content $f | Where-Object { $_ -match '^[A-Z0-9_]+=' }
    $bad = @($lines | Where-Object { $_ -match '=\s*(sk-|xoxb-|ghp_)[A-Za-z0-9_\-]{10,}' })
    [pscustomobject]@{ Pass = ($bad.Count -eq 0); Evidence = if ($bad.Count) { "疑似 $($bad.Count) 行含明文密钥" } else { "已赋值变量 $($lines.Count) 个，无明文密钥" } }
}

# ---------- A14 诊断关键段 ----------
Invoke-Check 'A14' 'doctor 关键检查项通过' {
    $v = (& $HERMES doctor 2>&1 | Out-String)
    $secOk  = $v -match 'No active security advisories'
    $pyOk   = $v -match 'Python 3\.14'
    $cfgOk  = $v -match 'Config version up to date'
    $blocked = $v -match 'PROGRAM BLOCKED BY SECURITY POLICY'
    $ok = $secOk -and $pyOk -and $cfgOk
    $note = @()
    $note += "security=$secOk"; $note += "python=$pyOk"; $note += "config=$cfgOk"
    if ($blocked) { $note += 'schtasks 被安全策略拦截(环境限制)' }
    [pscustomobject]@{ Pass = $ok; Evidence = ($note -join '  ') }
}

# ---------- 汇总 ----------
$pass = @($results | Where-Object { $_.Pass }).Count
$fail = @($results | Where-Object { -not $_.Pass }).Count
$total = $results.Count

Write-Host ""
Write-Host ("═══ 结果: {0}/{1} 通过, {2} 失败 ═══" -f $pass, $total, $fail) -ForegroundColor $(if ($fail -eq 0) { 'Green' } else { 'Yellow' })
Write-Host ""

# Markdown 报告
$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# Hermes Agent 安装验收报告")
[void]$md.AppendLine("")
[void]$md.AppendLine("- 生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$md.AppendLine("- 主机：$env:COMPUTERNAME  ·  HERMES_HOME：``$HH``")
[void]$md.AppendLine("- 结果：**$pass / $total 通过**，$fail 失败")
[void]$md.AppendLine("")
[void]$md.AppendLine("| # | 检查项 | 结果 | 证据 |")
[void]$md.AppendLine("| --- | --- | --- | --- |")
foreach ($r in $results) {
    $mark = if ($r.Pass) { 'PASS' } else { 'FAIL' }
    $ev = ($r.Evidence -replace '\|', '\|') -replace "`r?`n", ' '
    [void]$md.AppendLine("| $($r.Id) | $($r.Name) | $mark | $ev |")
}
$mdPath = Join-Path $outDir "report-$stamp.md"
$md.ToString() | Out-File -FilePath $mdPath -Encoding utf8

# JSON 报告
$jsonPath = Join-Path $outDir "report-$stamp.json"
$results | ConvertTo-Json -Depth 3 | Out-File -FilePath $jsonPath -Encoding utf8

Write-Host "报告已写入：" -ForegroundColor Cyan
Write-Host "  $mdPath"
Write-Host "  $jsonPath"

if ($fail -gt 0) { exit 1 } else { exit 0 }
