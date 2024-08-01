param (
    [string]$filePath
)

# Define the headers to be added
$headers = "meter,date,time,kw"

# Check if the file exists
if (-Not (Test-Path $filePath)) {
    Write-Error "Error: File '$filePath' not found."
    exit 1
}

# Create a temporary file to store the updated content
$tempFile = [System.IO.Path]::GetTempFileName()

try {
    # Read the existing content of the file
    $content = Get-Content $filePath

    # Write the headers and then append the existing content
    $headers | Out-File $tempFile -Encoding utf8 -Force
    $content | Out-File $tempFile -Encoding utf8 -Append

    # Replace the original file with the updated file
    Move-Item -Path $tempFile -Destination $filePath -Force

    Write-Output "Headers added successfully to '$filePath'."
    # Call the Python script if header addition is successful
    python "Q:\Energy\Engineering\R Stuff\working folder michal\lpd-r1\lpd-r6.py" LP_comma_202401301627.csv
}
catch {
    Write-Error "An error occurred: $_"
    exit 1
}
finally {
    # Cleanup: Ensure temp file is removed if not already moved
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}

