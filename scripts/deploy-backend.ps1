param (
    [string]$ApiStackName = "majin-api"
)

Write-Host "--- Starting Backend Deployment ---" -ForegroundColor Cyan

# 0. Check AWS Authentication
Write-Host "Checking AWS authentication..." -ForegroundColor Yellow
$CallerId = aws sts get-caller-identity --query "Account" --output text 2>$null
if ($LASTEXITCODE -ne 0 -or -not $CallerId) {
    Write-Error "AWS authentication failed. Please run 'aws configure' or check your credentials."
    exit 1
}
Write-Host "Authenticated as account: $CallerId" -ForegroundColor Green

# 1. Get Outputs from API Stack
Write-Host "Fetching outputs from $ApiStackName..." -ForegroundColor Yellow
$StackInfo = aws cloudformation describe-stacks --stack-name $ApiStackName --output json 2>$null
if ($LASTEXITCODE -ne 0 -or -not $StackInfo) {
    Write-Error "Stack '$ApiStackName' not found. Please run '.\scripts\deploy-infra.ps1' first to create the infrastructure."
    exit 1
}

$StackData = $StackInfo | ConvertFrom-Json
$StackStatus = $StackData.Stacks[0].StackStatus
Write-Host "Stack Status: $StackStatus" -ForegroundColor Cyan

if ($StackStatus -ne "CREATE_COMPLETE" -and $StackStatus -ne "UPDATE_COMPLETE") {
    Write-Error "Stack '$ApiStackName' is in state '$StackStatus'. It must be in CREATE_COMPLETE or UPDATE_COMPLETE to deploy."
    exit 1
}

$ApiOutputs = $StackData.Stacks[0].Outputs
$ApiId = ($ApiOutputs | Where-Object { $_.OutputKey -eq "ApiId" }).OutputValue
$DispatcherName = ($ApiOutputs | Where-Object { $_.OutputKey -eq "DispatcherFunctionName" }).OutputValue
$StatusName = ($ApiOutputs | Where-Object { $_.OutputKey -eq "StatusFunctionName" }).OutputValue
$ProcessorName = ($ApiOutputs | Where-Object { $_.OutputKey -eq "ProcessorFunctionName" }).OutputValue

if (-not $ApiId -or -not $DispatcherName -or -not $StatusName -or -not $ProcessorName) {
    Write-Error "Required outputs missing in stack $ApiStackName. (Outputs found: $(($ApiOutputs.OutputKey) -join ', '))"
    exit 1
}

$ProjectRoot = Get-Location
$BackendSrc = Join-Path $ProjectRoot "backend\src"
$TempZip = Join-Path $ProjectRoot "lambda_package.zip"
$DbTxtRoot = Join-Path $ProjectRoot "DB.txt"
$DbTxtDest = Join-Path $BackendSrc "DB.txt"

# 2. Package Source Code
Write-Host "Packaging source code..." -ForegroundColor Yellow
if (Test-Path $TempZip) { Remove-Item $TempZip }

# Copy DB.txt to src temporarily if it exists
$dbCopied = $false
if (Test-Path $DbTxtRoot) {
    Copy-Item $DbTxtRoot $DbTxtDest
    $dbCopied = $true
}

Compress-Archive -Path "$BackendSrc\*" -DestinationPath $TempZip

# Cleanup temporary DB.txt
if ($dbCopied) {
    Remove-Item $DbTxtDest
}

# 2. Update Lambda Functions
$Functions = @($DispatcherName, $StatusName, $ProcessorName)
foreach ($FuncName in $Functions) {
    Write-Host "Updating Lambda function: $FuncName..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name $FuncName --zip-file "fileb://$TempZip" > $null
}

# 3. Deploy API Gateway Stage
Write-Host "Deploying API Gateway stage: `$default..." -ForegroundColor Yellow
aws apigatewayv2 create-deployment --api-id $ApiId --stage-name '$default' > $null

# Cleanup
if (Test-Path $TempZip) { Remove-Item $TempZip }

Write-Host "--- Backend Deployment Completed! ---" -ForegroundColor Green
