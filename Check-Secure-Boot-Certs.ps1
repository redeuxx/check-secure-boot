# Check-Secure-Boot-Certs.ps1
# Checks the Secure Boot certificates on the local computer
# and sends the results to a specified API endpoint.

# Server address. Change to the appropriate server as needed.
$uri = "http://localhost:8000/api"

# Get the computer name
$computerName = $env:COMPUTERNAME

# Default values – ensures we never send nulls
$active_db  = $false

$default_db = $false
$notes = ""

# --- Active DB (db) ---
try {
    $activeVar = Get-SecureBootUEFI -Name db -ErrorAction SilentlyContinue

    if ($null -ne $activeVar) {
        $activeText = [System.Text.Encoding]::ASCII.GetString($activeVar.Bytes)
        $active_db  = [bool]($activeText -match 'Windows UEFI CA 2023')
    }
    else {
        $notes += "UEFI variable 'db' is undefined on this system. "
    }
}
catch {
    $active_db = $false
    $notes += "Error reading UEFI variable 'db': $($_.Exception.Message). "
}

# --- Default DB (dbdefault) ---
try {
    $defaultVar = Get-SecureBootUEFI -Name dbdefault -ErrorAction SilentlyContinue

    if ($null -ne $defaultVar) {
        $defaultText = [System.Text.Encoding]::ASCII.GetString($defaultVar.Bytes)
        $default_db  = [bool]($defaultText -match 'Windows UEFI CA 2023')
    }
    else {
        $notes += "UEFI variable 'dbdefault' is undefined on this system. "
    }
}
catch {
    $default_db = $false
    $notes += "Error reading UEFI variable 'dbdefault': $($_.Exception.Message). "
}

# Build JSON body – booleans only, no nulls
$body = @{
    computer_name     = $computerName
    active_db_status  = $active_db
    default_db_status = $default_db
    notes             = $notes
} | ConvertTo-Json

Write-Host "Sending request to: $uri"
Write-Host "Request Body:"
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri $uri -Method Put -ContentType "application/json" -Body $body
    Write-Host "API Response:"
    $response | ConvertTo-Json -Depth 100 | Write-Host
}
catch {
    Write-Error "Error calling API: $($_.Exception.Message)"

    $webResponse = $_.Exception.Response
    if ($webResponse -and $webResponse.GetResponseStream) {
        try {
            $reader = New-Object System.IO.StreamReader($webResponse.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "HTTP Response Body:"
            Write-Host $responseBody
        } catch {
            Write-Host "Could not read HTTP response body."
        }
    }
}