param (
    [string]$filePath  # Parameter to accept the file path as an argument
)

# Define the headers to be added
$headers = "meter,date,time,kw"

# Check if the file exists
if (-Not (Test-Path $filePath)) {
    Write-Error "Error: File '$filePath' not found."
    exit 1  # Exit the script if the file does not exist
}

# Read the first line of the file to check for an existing header
$firstLine = Get-Content -Path $filePath -TotalCount 1

# Check if the first line is already the header
if ($firstLine -eq $headers) {
    Write-Output "Header already exists in '$filePath'. No changes made."
} else {
    # Create a temporary file to store the updated content
    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        # Read the existing content of the file
        $content = Get-Content $filePath

        # Write the headers and then append the existing content
        $headers | Out-File $tempFile -Encoding utf8 -Force  # Write the headers to the temporary file
        $content | Out-File $tempFile -Encoding utf8 -Append  # Append the original file content to the temporary file

        # Replace the original file with the updated file
        Move-Item -Path $tempFile -Destination $filePath -Force  # Overwrite the original file with the temporary file

        Write-Output "Headers added successfully to '$filePath'."
    }
    catch {
        Write-Error "An error occurred: $_"  # Handle any errors that occur during the process
        exit 1  # Exit the script if an error occurs
    }
    finally {
        # Cleanup: Ensure temp file is removed if not already moved
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force  # Remove the temporary file if it still exists
        }
    }
}

# Call the Python script regardless of whether the header was added
python "C:\Users\mczarnecki\GitHub\load-profile\lpd.py" $filePath
