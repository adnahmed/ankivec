param(
    [Parameter(Position=0)]
    [string]$Command
)

function Install {
    Write-Host "Installing runtime dependencies to vendor directory..."
    if (Test-Path "vendor") {
        Remove-Item -Recurse -Force vendor
    }
    pip install -r requirements-runtime.txt -t vendor
    Write-Host "Dependencies installed to vendor/"
}

function Clean {
    Write-Host "Cleaning..."
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force dist
    }
    
    $addonPath = "$env:APPDATA\Anki2\addons21\ankivec"
    if (Test-Path $addonPath) {
        Remove-Item -Recurse -Force $addonPath
    }
}

function Build {
    Write-Host "Building..."
    
    # Clean dist first
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force dist
    }
    
    # Create dist directory
    New-Item -ItemType Directory -Path "dist" | Out-Null
    
    # Copy Python files
    Copy-Item "*.py" dist/ -Exclude "test_*.py"
    Copy-Item "manifest.json" dist/
    Copy-Item "config.json" dist/
    Copy-Item -Recurse src dist/
    
    # Remove pycache
    if (Test-Path "dist/__pycache__") {
        Remove-Item -Recurse -Force dist/__pycache__
    }
    
    # Ensure vendor directory exists
    if (-not (Test-Path "vendor")) {
        Write-Host "Vendor directory not found. Running install..."
        Install
    }
    
    # Copy vendor directory
    Copy-Item -Recurse vendor dist/
    
    # Create zip file (ankiaddon)
    Push-Location dist
    if (Test-Path "ankivec.ankiaddon") {
        Remove-Item ankivec.ankiaddon
    }
    Compress-Archive -Path * -DestinationPath ankivec.ankiaddon -CompressionLevel Optimal
    Pop-Location
    
    Write-Host "Build complete: dist/ankivec.ankiaddon"
}

function Link-Dev {
    Write-Host "Linking development environment..."
    $addonPath = "$env:APPDATA\Anki2\addons21\ankivec"
    
    # Remove if exists
    if (Test-Path $addonPath) {
        Remove-Item -Recurse -Force $addonPath
    }
    
    # Create symbolic link (requires admin or Developer Mode)
    $sourcePath = Get-Location
    New-Item -ItemType SymbolicLink -Path $addonPath -Target $sourcePath | Out-Null
    
    Write-Host "Development link created at: $addonPath"
}

function Link-Dist {
    Write-Host "Linking dist build..."
    $addonPath = "$env:APPDATA\Anki2\addons21\ankivec"
    
    # Remove if exists
    if (Test-Path $addonPath) {
        Remove-Item -Recurse -Force $addonPath
    }
    
    # Create symbolic link to dist
    $distPath = Join-Path (Get-Location) "dist"
    New-Item -ItemType SymbolicLink -Path $addonPath -Target $distPath | Out-Null
    
    Write-Host "Dist link created at: $addonPath"
}

# Main command dispatcher
switch ($Command) {
    "install" { Install }
    "clean" { Clean }
    "build" { 
        Clean
        Build 
    }
    "link-dev" { Link-Dev }
    "link-dist" { Link-Dist }
    default {
        Write-Host "Invalid command: $Command"
        Write-Host ""
        Write-Host "Available commands:"
        Write-Host "  install     - Install runtime dependencies to vendor/"
        Write-Host "  build       - Create production build (ankivec.ankiaddon)"
        Write-Host "  clean       - Remove dist/ and Anki addon symlink"
        Write-Host "  link-dev    - Symlink current directory to Anki addons21"
        Write-Host "  link-dist   - Symlink dist/ to Anki addons21 for testing builds"
        exit 1
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Done"
}
