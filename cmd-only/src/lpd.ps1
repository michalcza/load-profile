param (
    [string]$filename
)

# Add headers if they are not present
$fileContent = Get-Content -Path $filename -TotalCount 1
if ($fileContent -notmatch "^date,time,kw$") {
    $header = "date,time,kw"
    $content = Get-Content -Path $filename
    Set-Content -Path $filename -Value $header
    Add-Content -Path $filename -Value $content
    Write-Host "Headers added successfully to '$filename'."
} else {
    Write-Host "Headers are already present in '$filename'."
}

# Call the Python script
$scriptPath = "lpd.py"
$process = Start-Process -NoNewWindow -FilePath "python" -ArgumentList "$scriptPath", "$filename" -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Host "Python script failed with exit code $($process.ExitCode)."
} else {
    Write-Host "Python script executed successfully."
}
