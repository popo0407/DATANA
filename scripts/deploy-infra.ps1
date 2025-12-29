param (
    [string]$BaseStackName = "majin-base",
    [string]$ApiStackName = "majin-api"
)

Write-Host "--- Starting Infrastructure Deployment ---" -ForegroundColor Cyan

# 0. Check AWS Authentication
Write-Host "Checking AWS authentication..." -ForegroundColor Yellow
$CallerId = aws sts get-caller-identity --query "Account" --output text 2>$null
if ($LASTEXITCODE -ne 0 -or -not $CallerId) {
    Write-Error "AWS authentication failed. Please run 'aws configure' or check your credentials."
    exit 1
}
Write-Host "Authenticated as account: $CallerId" -ForegroundColor Green

# 1. Deploy Base Stack
Write-Host "Deploying Base Stack: $BaseStackName..." -ForegroundColor Yellow
aws cloudformation deploy `
    --template-file infra/base-stack.yml `
    --stack-name $BaseStackName `
    --capabilities CAPABILITY_NAMED_IAM

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy Base Stack. Please check the AWS CloudFormation console for details."
    exit 1
}

# 2. Get Outputs from Base Stack
Write-Host "Fetching outputs from $BaseStackName..." -ForegroundColor Yellow
$BaseOutputsJson = aws cloudformation describe-stacks --stack-name $BaseStackName --query "Stacks[0].Outputs" --output json
if ($LASTEXITCODE -ne 0 -or -not $BaseOutputsJson) {
    Write-Error "Failed to fetch outputs from stack $BaseStackName. Infrastructure deployment cannot continue."
    exit 1
}
$BaseOutputs = $BaseOutputsJson | ConvertFrom-Json

$DataBucketName = ($BaseOutputs | Where-Object { $_.OutputKey -eq "DataBucketName" }).OutputValue
$JobTableName = ($BaseOutputs | Where-Object { $_.OutputKey -eq "JobTableName" }).OutputValue
$LambdaRoleArn = ($BaseOutputs | Where-Object { $_.OutputKey -eq "LambdaRoleArn" }).OutputValue

if (-not $DataBucketName -or -not $JobTableName -or -not $LambdaRoleArn) {
    Write-Error "Required outputs missing from $BaseStackName. Please check the stack outputs."
    exit 1
}

# 3. Deploy API Stack
Write-Host "Deploying API Stack: $ApiStackName..." -ForegroundColor Yellow
aws cloudformation deploy `
    --template-file infra/api-stack.yml `
    --stack-name $ApiStackName `
    --capabilities CAPABILITY_NAMED_IAM `
    --parameter-overrides `
    DataBucketName=$DataBucketName `
    JobTableName=$JobTableName `
    LambdaRoleArn=$LambdaRoleArn

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to deploy API Stack. Please check the AWS CloudFormation console for details."
    exit 1
}

# 4. Configure S3 Notification (Trigger)
Write-Host "Configuring S3 Notification for $DataBucketName..." -ForegroundColor Yellow
$ApiOutputsJson = aws cloudformation describe-stacks --stack-name $ApiStackName --query "Stacks[0].Outputs" --output json
$ApiOutputs = $ApiOutputsJson | ConvertFrom-Json
$ProcessorArn = ($ApiOutputs | Where-Object { $_.OutputKey -eq "ProcessorFunctionArn" }).OutputValue

$NotificationConfig = @{
    LambdaFunctionConfigurations = @(
        @{
            LambdaFunctionArn = $ProcessorArn
            Events            = @("s3:ObjectCreated:*")
            Filter            = @{
                Key = @{
                    FilterRules = @(
                        @{
                            Name  = "prefix"
                            Value = "uploads/"
                        },
                        @{
                            Name  = "suffix"
                            Value = ".csv"
                        }
                    )
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

# Save to temp file because of PowerShell quoting issues with complex JSON in CLI
$TempConfigPath = Join-Path $env:TEMP "s3_notification.json"
[System.IO.File]::WriteAllText($TempConfigPath, $NotificationConfig)

aws s3api put-bucket-notification-configuration `
    --bucket $DataBucketName `
    --notification-configuration "file://$TempConfigPath" > $null

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to configure S3 notification. You may need to set it manually."
}
else {
    Write-Host "S3 Notification configured successfully." -ForegroundColor Green
}

Remove-Item $TempConfigPath

Write-Host "--- Infrastructure Deployment Completed! ---" -ForegroundColor Green
