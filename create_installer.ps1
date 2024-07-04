<#
.SYNOPSIS
    This script creates an installer for the PDF Tool using BruckerCo Setup.

.DESCRIPTION
    This script defines paths for the source directory, output directory, and the BruckerCo Setup script.
    It then invokes the BruckerCo Setup Compiler to generate an installer based on the specified configuration.

.PARAMETER SourceDir
    The directory containing the files to be included in the installer.

.PARAMETER OutputDir
    The directory where the installer will be created.

.PARAMETER InstallerScript
    The path to the BruckerCo Setup script that defines the installer configuration.

.EXAMPLE
    .\create_installer.ps1 -SourceDir "C:\path\to\dist" -OutputDir "C:\path\to\output" -InstallerScript "C:\path\to\script.bcs"
#>

param (
    [string]$SourceDir = "C:\path\to\dist",
    [string]$OutputDir = "C:\path\to\output",
    [string]$InstallerScript = ".\script.bcs"
)

# Ensure BruckerCo Setup Compiler path is correct
$BruckerCoSetupCompiler = "C:\Program Files (x86)\BruckerCo Setup\BCSC.exe"
if (-Not (Test-Path $BruckerCoSetupCompiler)) {
    Write-Error "BruckerCo Setup Compiler not found at $BruckerCoSetupCompiler"
    exit 1
}

# Ensure Source Directory exists
if (-Not (Test-Path $SourceDir)) {
    Write-Error "Source directory not found at $SourceDir"
    exit 1
}

# Ensure Installer Script exists
if (-Not (Test-Path $InstallerScript)) {
    Write-Error "Installer script not found at $InstallerScript"
    exit 1
}

# Create Output Directory if it does not exist
if (-Not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Run BruckerCo Setup Compiler
try {
    & $BruckerCoSetupCompiler $InstallerScript
    Write-Output "Installer successfully created in $OutputDir"
} catch {
    Write-Error "Failed to create installer: $_"
    exit 1
}
