<#
.SYNOPSIS
    猪周期监控系统 - 一键部署脚本
.DESCRIPTION
    构建前端 → 提交GitHub → 部署Vercel(前端) → 部署Railway(后端)
.NOTES
    需要 PowerShell 5.1+ 或 PowerShell Core 7+
    需要安装: Node.js, Python, Git, Vercel CLI, Railway CLI
#>

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "web-dashboard"

# ===== 颜色输出辅助函数 =====
function Write-Step {
    param([string]$Msg)
    Write-Host "`n━━━ $Msg ━━━" -ForegroundColor Cyan
}
function Write-OK {
    param([string]$Msg)
    Write-Host "  ✅ $Msg" -ForegroundColor Green
}
function Write-Warn {
    param([string]$Msg)
    Write-Host "  ⚠️  $Msg" -ForegroundColor Yellow
}
function Write-Error {
    param([string]$Msg)
    Write-Host "  ❌ $Msg" -ForegroundColor Red
}
function Write-Info {
    param([string]$Msg)
    Write-Host "  📋 $Msg" -ForegroundColor Gray
}

Write-Host @"
┌─────────────────────────────────────────────┐
│    猪周期监控系统 - 一键部署脚本             │
│    Pig Cycle Bot Deploy Script              │
└─────────────────────────────────────────────┘
"@ -ForegroundColor Magenta

# ===== Step 1: 检查环境 =====
Write-Step "Step 1/7: 检查环境依赖"

$envOK = $true

# Node.js
try {
    $nodeVer = & node --version 2>&1
    Write-OK "Node.js: $nodeVer"
} catch {
    Write-Error "Node.js 未安装！请从 https://nodejs.org 下载安装"
    $envOK = $false
}

# npm
try {
    $npmVer = & npm --version 2>&1
    Write-OK "npm: v$npmVer"
} catch {
    Write-Warn "npm 未找到，将尝试用 yarn 替代"
}

# Python
try {
    $pyVer = & python --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-Error "Python 未安装！请从 https://python.org 下载安装"
    $envOK = $false
}

# Git
$hasGit = $false
try {
    $gitVer = & git --version 2>&1
    Write-OK "Git: $gitVer"
    $hasGit = $true
} catch {
    Write-Warn "Git 未安装，跳过 Git 提交步骤"
}

# Vercel CLI
$hasVercel = $false
try {
    $vcVer = & vercel --version 2>&1
    Write-OK "Vercel CLI: v$vcVer"
    $hasVercel = $true
} catch {
    Write-Warn "Vercel CLI 未安装，跳过 Vercel 部署。"
    Write-Info "安装命令: npm i -g vercel"
}

# Railway CLI
$hasRailway = $false
try {
    $rwVer = & railway --version 2>&1
    Write-OK "Railway CLI: $rwVer"
    $hasRailway = $true
} catch {
    Write-Warn "Railway CLI 未安装，跳过 Railway 部署。"
    Write-Info "安装命令: npm i -g @railway/cli"
}

if (-not $envOK) {
    Write-Error "环境检查未通过，请安装缺失依赖后重试。"
    exit 1
}
Write-OK "环境检查完成"

# ===== Step 2: 构建前端 =====
Write-Step "Step 2/7: 构建前端"
Push-Location $FRONTEND_DIR

try {
    Write-Info "执行 npm run build..."
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "构建失败" }
    Write-OK "前端构建成功 (输出到 dist/)"
} catch {
    Write-Error "前端构建失败: $_"
    Write-Warn "尝试 npm install 后重试..."
    & npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install 失败" }
    & npm run build
    Write-OK "前端构建成功（重试后）"
}
finally {
    Pop-Location
}

# ===== Step 3: 提交代码到 GitHub =====
Write-Step "Step 3/7: 提交代码到 GitHub"

if ($hasGit) {
    Push-Location $PROJECT_ROOT
    try {
        # 检查是否有 .git
        if (-not (Test-Path ".git")) {
            Write-Info "本地 Git 仓库不存在，正在初始化..."
            & git init
            # 检查是否有远程仓库配置
            $remoteUrl = & git remote get-url origin 2>&1
            if ($LASTEXITCODE -ne 0) {
                $remoteUrl = Read-Host "请输入 GitHub 仓库地址 (例如: https://github.com/你的用户名/pig-cycle-bot.git)"
                & git remote add origin $remoteUrl
            }
        }

        $today = Get-Date -Format "yyyy-MM-dd"
        & git add .
        & git commit -m "deploy: 自动部署 $today"
        Write-OK "代码已提交"

        # 推送到 GitHub
        try {
            & git push -u origin main 2>&1
            if ($LASTEXITCODE -ne 0) {
                & git push -u origin master 2>&1
            }
            Write-OK "代码已推送到 GitHub"
        } catch {
            Write-Warn "Git push 失败，请手动推送。"
            Write-Info "推送命令: git push -u origin main"
        }
    } catch {
        Write-Warn "Git 操作异常: $_"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Info "跳过 Git 提交步骤"
}

# ===== Step 4: 部署前端到 Vercel =====
Write-Step "Step 4/7: 部署前端到 Vercel"

if ($hasVercel) {
    Push-Location $FRONTEND_DIR
    try {
        Write-Info "执行 vercel --prod..."
        & vercel --prod
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Vercel 部署成功！"
        } else {
            throw "Vercel 部署失败"
        }
    } catch {
        Write-Error "Vercel 部署失败: $_"
        Write-Info "请手动部署: cd web-dashboard && vercel --prod"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Info "跳过 Vercel 部署（未安装 Vercel CLI）"
    Write-Info "手动部署步骤:"
    Write-Info "  1. cd web-dashboard"
    Write-Info "  2. npx vercel --prod"
}

# ===== Step 5: 部署后端到 Railway =====
Write-Step "Step 5/7: 部署后端到 Railway"

if ($hasRailway) {
    Push-Location $PROJECT_ROOT
    try {
        # 检查是否已登录
        $rwWhoami = & railway whoami 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Info "Railway 未登录，打开浏览器登录..."
            & railway login
        }

        Write-Info "执行 railway up..."
        & railway up
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Railway 部署成功！"
        } else {
            throw "Railway 部署失败"
        }
    } catch {
        Write-Error "Railway 部署失败: $_"
        Write-Info "请手动部署: railway up"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Info "跳过 Railway 部署（未安装 Railway CLI）"
    Write-Info "手动部署步骤:"
    Write-Info "  1. 打开 https://railway.app"
    Write-Info "  2. 连接 GitHub 仓库"
    Write-Info "  3. 添加 Volume data 挂载到 /app/data"
    Write-Info "  4. 设置 Start Command: uvicorn web-dashboard.backend:app --host 0.0.0.0 --port \$PORT"
}

# ===== Step 6: 上传数据库 =====
Write-Step "Step 6/7: 数据库上传提示"

$dbPath = Join-Path $PROJECT_ROOT "data" "hog_data.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1MB
    Write-Info "数据库文件: data/hog_data.db ($([math]::Round($dbSize,2)) MB)"

    Write-Host @"

    📋 请手动上传数据库到部署环境:

    === Railway ===
    1. 打开 Railway Dashboard
    2. 进入项目 → Volumes
    3. 点击 data volume 的 Upload 按钮
    4. 选择 data/hog_data.db 上传

    === 其他方式 ===
    将 data/hog_data.db 上传到对象存储或 S3，
    并在环境变量中设置 DB_PATH 指向远程地址。

"@ -ForegroundColor Yellow
} else {
    Write-Warn "数据库文件 data/hog_data.db 不存在"
    Write-Info "请先在本地运行 scheduler.py 拉取数据后再部署"
}

# ===== Step 7: 验证部署 =====
Write-Step "Step 7/7: 验证部署"

if ($hasVercel) {
    try {
        $vcDomains = & vercel list 2>&1
        Write-OK "Vercel 项目列表已获取"
    } catch {
        Write-Warn "无法获取 Vercel 项目列表"
    }
}

if ($hasRailway) {
    try {
        & railway status 2>&1
        Write-OK "Railway 状态已获取"
    } catch {
        Write-Warn "无法获取 Railway 状态"
    }
}

# ===== 输出访问地址 =====
Write-Step "🎉 部署完成！访问地址"

# 尝试获取 Vercel 部署 URL
$frontendUrl = "未知"
if ($hasVercel) {
    try {
        $vcInfo = & vercel --prod --scope 2>&1 | Select-String -Pattern "https://" | Select-Object -First 1
        if ($vcInfo) {
            $frontendUrl = $vcInfo.ToString().Trim()
        }
    } catch {}
}

$backendUrl = "未知"
if ($hasRailway) {
    try {
        $railwayInfo = & railway status 2>&1
        $urlMatch = [regex]::Match($railwayInfo, "https://[^\s]+")
        if ($urlMatch.Success) {
            $backendUrl = $urlMatch.Value
        }
    } catch {}
}

Write-Host @"

┌─────────────────────────────────────────────┐
│              部署信息汇总                     │
├─────────────────────────────────────────────┤
│  前端 (Vercel):  $($frontendUrl)             │
│  后端 (Railway): $($backendUrl)              │
│  数据库:         data/hog_data.db            │
│  部署时间:       $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")       │
└─────────────────────────────────────────────┘

后续维护:
  - 每日数据抓取: python scheduler.py
  - 更新部署: 重新运行本脚本
  - 查看日志: railway logs
  - 更新前端: cd web-dashboard && vercel --prod

"@ -ForegroundColor Green
