param (
    [string]$BaseStackName = "majin-base"
)

Write-Host "--- Starting Frontend Deployment ---" -ForegroundColor Cyan

# 0. Check AWS Authentication
Write-Host "Checking AWS authentication..." -ForegroundColor Yellow
$CallerId = aws sts get-caller-identity --query "Account" --output text 2>$null
if ($LASTEXITCODE -ne 0 -or -not $CallerId) {
    Write-Error "AWS authentication failed. Please run 'aws configure' or check your credentials."
    exit 1
}
Write-Host "Authenticated as account: $CallerId" -ForegroundColor Green

# 1. Get Outputs from Base Stack
Write-Host "Fetching outputs from $BaseStackName..." -ForegroundColor Yellow
$BaseOutputsJson = aws cloudformation describe-stacks --stack-name $BaseStackName --query "Stacks[0].Outputs" --output json
if ($LASTEXITCODE -ne 0 -or -not $BaseOutputsJson) {
    Write-Error "Failed to fetch outputs from stack $BaseStackName. Please ensure the stack exists."
    exit 1
}
$BaseOutputs = $BaseOutputsJson | ConvertFrom-Json

$BucketName = ($BaseOutputs | Where-Object { $_.OutputKey -eq "FrontendBucketName" }).OutputValue
$DistributionId = ($BaseOutputs | Where-Object { $_.OutputKey -eq "FrontendDistributionId" }).OutputValue

if (-not $BucketName -or -not $DistributionId) {
    Write-Error "Could not find required outputs (FrontendBucketName, FrontendDistributionId) in stack $BaseStackName."
    exit 1
}

$ProjectRoot = Get-Location
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "--- Starting Frontend Deployment ---" -ForegroundColor Cyan

# 1. Build
Write-Host "Building React application..." -ForegroundColor Yellow
Set-Location $FrontendDir
npm install
npm run build

# 2. Sync to S3
Write-Host "Syncing to S3 bucket: $BucketName..." -ForegroundColor Yellow
aws s3 sync dist/ "s3://$BucketName" --delete > $null

# 3. Invalidate CloudFront
Write-Host "Invalidating CloudFront cache: $DistributionId..." -ForegroundColor Yellow
aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*" > $null

Write-Host "--- Frontend Deployment Completed! ---" -ForegroundColor Green
Set-Location $ProjectRoot
