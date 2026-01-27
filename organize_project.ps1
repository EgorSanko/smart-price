# Smart Price - Project Structure Organizer
# Запусти этот скрипт из папки smart-price:
# powershell -ExecutionPolicy Bypass -File organize_project.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Smart Price Structure Organizer ===" -ForegroundColor Cyan
Write-Host ""

# Базовая директория
$baseDir = Get-Location

# Создаём структуру папок
Write-Host "Creating folder structure..." -ForegroundColor Yellow

$folders = @(
    "backend/app/api/v1/endpoints",
    "backend/app/core",
    "backend/app/db/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/scrapers",
    "backend/app/ml/embeddings",
    "backend/app/ml/matching",
    "backend/app/ml/forecasting",
    "backend/app/ml/anomaly",
    "backend/app/agents/tools",
    "backend/tests/test_api",
    "backend/tests/test_services",
    "backend/alembic/versions",
    "docker/postgres",
    "docker/clickhouse",
    "docker/nginx",
    "frontend/src/app",
    "frontend/src/components",
    "frontend/src/hooks",
    "frontend/src/lib",
    "frontend/src/types",
    "docs",
    "ml-experiments/notebooks",
    ".github/workflows"
)

foreach ($folder in $folders) {
    $path = Join-Path $baseDir $folder
    if (!(Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  Created: $folder" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Moving files from folder 1 (Setup & Config)..." -ForegroundColor Yellow

# Из папки 1 (Setup & Config)
$folder1 = Join-Path $baseDir "1"
if (Test-Path $folder1) {
    # config.py -> backend/app/
    if (Test-Path "$folder1/config.py") {
        Move-Item "$folder1/config.py" "backend/app/config.py" -Force
        Write-Host "  Moved: config.py -> backend/app/" -ForegroundColor Green
    }

    # pyproject.toml -> backend/
    if (Test-Path "$folder1/pyproject.toml") {
        Move-Item "$folder1/pyproject.toml" "backend/pyproject.toml" -Force
        Write-Host "  Moved: pyproject.toml -> backend/" -ForegroundColor Green
    }

    # Dockerfile -> backend/
    if (Test-Path "$folder1/Dockerfile") {
        Move-Item "$folder1/Dockerfile" "backend/Dockerfile" -Force
        Write-Host "  Moved: Dockerfile -> backend/" -ForegroundColor Green
    }

    # docker-compose.dev.yml -> docker/
    if (Test-Path "$folder1/docker-compose.dev.yml") {
        Move-Item "$folder1/docker-compose.dev.yml" "docker/docker-compose.dev.yml" -Force
        Write-Host "  Moved: docker-compose.dev.yml -> docker/" -ForegroundColor Green
    }

    # README.md -> root
    if (Test-Path "$folder1/README.md") {
        Move-Item "$folder1/README.md" "README.md" -Force
        Write-Host "  Moved: README.md -> root" -ForegroundColor Green
    }

    # CURRENT_STRUCTURE.md -> docs/
    if (Test-Path "$folder1/CURRENT_STRUCTURE.md") {
        Move-Item "$folder1/CURRENT_STRUCTURE.md" "docs/CURRENT_STRUCTURE.md" -Force
        Write-Host "  Moved: CURRENT_STRUCTURE.md -> docs/" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Moving files from folder 2 (Database Models)..." -ForegroundColor Yellow

# Из папки 2 (Database Models)
$folder2 = Join-Path $baseDir "2"
if (Test-Path $folder2) {
    # base.py -> backend/app/db/
    if (Test-Path "$folder2/base.py") {
        Move-Item "$folder2/base.py" "backend/app/db/base.py" -Force
        Write-Host "  Moved: base.py -> backend/app/db/" -ForegroundColor Green
    }

    # session.py -> backend/app/db/
    if (Test-Path "$folder2/session.py") {
        Move-Item "$folder2/session.py" "backend/app/db/session.py" -Force
        Write-Host "  Moved: session.py -> backend/app/db/" -ForegroundColor Green
    }

    # __init__.py -> backend/app/db/models/
    if (Test-Path "$folder2/__init__.py") {
        Move-Item "$folder2/__init__.py" "backend/app/db/models/__init__.py" -Force
        Write-Host "  Moved: __init__.py -> backend/app/db/models/" -ForegroundColor Green
    }

    # Models -> backend/app/db/models/
    $models = @("marketplace.py", "category.py", "product.py", "price_history.py", "product_match.py", "user.py", "alert.py")
    foreach ($model in $models) {
        if (Test-Path "$folder2/$model") {
            Move-Item "$folder2/$model" "backend/app/db/models/$model" -Force
            Write-Host "  Moved: $model -> backend/app/db/models/" -ForegroundColor Green
        }
    }

    # env.py -> backend/alembic/
    if (Test-Path "$folder2/env.py") {
        Move-Item "$folder2/env.py" "backend/alembic/env.py" -Force
        Write-Host "  Moved: env.py -> backend/alembic/" -ForegroundColor Green
    }

    # 001_initial_schema.py -> backend/alembic/versions/
    if (Test-Path "$folder2/001_initial_schema.py") {
        Move-Item "$folder2/001_initial_schema.py" "backend/alembic/versions/001_initial_schema.py" -Force
        Write-Host "  Moved: 001_initial_schema.py -> backend/alembic/versions/" -ForegroundColor Green
    }

    # CURRENT_STRUCTURE.md (обновлённый) -> docs/
    if (Test-Path "$folder2/CURRENT_STRUCTURE.md") {
        Move-Item "$folder2/CURRENT_STRUCTURE.md" "docs/CURRENT_STRUCTURE.md" -Force
        Write-Host "  Moved: CURRENT_STRUCTURE.md -> docs/ (updated)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Creating __init__.py files..." -ForegroundColor Yellow

# Создаём пустые __init__.py
$initFiles = @(
    "backend/app/__init__.py",
    "backend/app/api/__init__.py",
    "backend/app/api/v1/__init__.py",
    "backend/app/api/v1/endpoints/__init__.py",
    "backend/app/core/__init__.py",
    "backend/app/db/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/__init__.py",
    "backend/app/scrapers/__init__.py",
    "backend/app/ml/__init__.py",
    "backend/app/ml/embeddings/__init__.py",
    "backend/app/ml/matching/__init__.py",
    "backend/app/ml/forecasting/__init__.py",
    "backend/app/ml/anomaly/__init__.py",
    "backend/app/agents/__init__.py",
    "backend/app/agents/tools/__init__.py",
    "backend/tests/__init__.py",
    "backend/tests/test_api/__init__.py",
    "backend/tests/test_services/__init__.py"
)

foreach ($initFile in $initFiles) {
    $path = Join-Path $baseDir $initFile
    if (!(Test-Path $path)) {
        New-Item -ItemType File -Path $path -Force | Out-Null
        Write-Host "  Created: $initFile" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Creating .gitignore..." -ForegroundColor Yellow

# Создаём .gitignore
$gitignore = @"
# Python
__pycache__/
*.py[cod]
*`$py.class
.venv/
venv/
.env

# IDE
.idea/
.vscode/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/

# Node
node_modules/
.next/
out/

# Docker
docker/volumes/

# ML
*.pt
*.pth
*.onnx
models/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
"@

Set-Content -Path ".gitignore" -Value $gitignore
Write-Host "  Created: .gitignore" -ForegroundColor Green

Write-Host ""
Write-Host "Creating backend/.env.example..." -ForegroundColor Yellow

# Создаём .env.example
$envExample = @"
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=smartprice
POSTGRES_PASSWORD=smartprice_secret
POSTGRES_DB=smartprice

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123

# Security
SECRET_KEY=change-me-in-production

# AI
ANTHROPIC_API_KEY=your-key-here

# App
DEBUG=true
ENVIRONMENT=development
"@

Set-Content -Path "backend/.env.example" -Value $envExample
Write-Host "  Created: backend/.env.example" -ForegroundColor Green

Write-Host ""
Write-Host "Creating alembic.ini..." -ForegroundColor Yellow

# Создаём alembic.ini
$alembicIni = @"
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"@

Set-Content -Path "backend/alembic.ini" -Value $alembicIni
Write-Host "  Created: backend/alembic.ini" -ForegroundColor Green

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project structure created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now delete empty folders 1-10:" -ForegroundColor Yellow
Write-Host "  Remove-Item -Recurse -Force 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. cd backend"
Write-Host "  2. Copy .env.example to .env and edit it"
Write-Host "  3. Run: docker-compose -f ../docker/docker-compose.dev.yml up -d"
