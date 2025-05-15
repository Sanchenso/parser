# Установка Chocolatey
if (-Not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Install Chocolatey..."

    Set-ExecutionPolicy Bypass -Scope Process -Force;
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'));
} else {
    Write-Host "Chocolatey has already been installed."
}

# Установка ripgrep
Write-Host "Install ripgrep (rg)..."
choco install ripgrep -y

# Установка Python
$pythonVersion = python --version 2>$null
if ($pythonVersion -Match "Python (\d+)\.(\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    $patch = [int]$matches[3]

    if ($major -gt 3 -or ($major -eq 3 -and $minor -gt 12) -or ($major -eq 3 -and $minor -eq 12 -and $patch -ge 4)) {
        Write-Host "Python $pythonVersion has already been installed."
    } else {
        Write-Host "Install Python 3.12.4..."
        choco install python --version 3.12.4 -y
    }
} else {
    Write-Host "Install Python 3.12.4..."
    choco install python --version 3.12.4 -y
}

# Установка pip
Write-Host "Updating pip to version 25.0.1..."
python -m pip install --upgrade "pip==25.0.1"

# Установка зависимостей requirements.txt
Write-Host "Installing packages from requirements.txt..."
pip install -r requirements.txt

Write-Host "Installation complete."
