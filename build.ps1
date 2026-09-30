param(
    [string]$PythonExecutable = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    throw 'Create .venv and install requirements-dev.txt before building.'
}
$PythonExecutable = (Resolve-Path -LiteralPath $PythonExecutable).Path
$toolsToBuild = @(
    @{ Name = 'InvoiceHelper_AllInOne'; Source = 'invoiceMaster.py' },
    @{ Name = 'InvoiceRenamer_Only'; Source = 'invoiceTool.py' },
    @{ Name = 'InvoiceMerger_Only'; Source = 'mergeInvoices.py' }
)
Push-Location $PSScriptRoot
try {
    foreach ($toolToBuild in $toolsToBuild) {
        & $PythonExecutable -m PyInstaller --noconfirm --onefile --console `
            --name $toolToBuild.Name --distpath dist --workpath build --specpath build $toolToBuild.Source
        if ($LASTEXITCODE -ne 0) {
            throw ('Build failed: ' + $toolToBuild.Name)
        }
    }
} finally {
    Pop-Location
}
