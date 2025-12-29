import json
import os
import uuid
import boto3
import ipaddress
from datetime import datetime, timedelta

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

DATA_BUCKET = os.environ['DATA_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']
PROCESS_FUNCTION = os.environ['PROCESS_FUNCTION']
ALLOWED_IP_RANGE = os.environ.get('ALLOWED_IP_RANGE', '0.0.0.0/0')

def is_ip_allowed(source_ip):
    """
    送信元IPが許可リストに含まれているかチェック
    """
    if ALLOWED_IP_RANGE == '0.0.0.0/0':
        return True
    try:
        return ipaddress.ip_address(source_ip) in ipaddress.ip_network(ALLOWED_IP_RANGE)
    except Exception as e:
        print(f"IP validation error: {e}")
        return False

def handler(event, context):
    """
    分析ジョブの受付
    1. IP制限チェック (外部API呼び出し時)
    2. ジョブID発行
    3. S3 Presigned URL発行 (アップロード用)
    4. DynamoDBに初期状態保存
    5. 分析Lambdaを非同期で起動
    """
    try:
        # IP制限チェック
        source_ip = event.get('requestContext', {}).get('http', {}).get('sourceIp')
        if source_ip and not is_ip_allowed(source_ip):
            print(f"Access denied for IP: {source_ip}")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: IP address not allowed'})
            }

        job_id = str(uuid.uuid4())
        file_name = f"uploads/{job_id}.csv"
        
        # S3 Presigned URL (PUT) 発行
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': DATA_BUCKET,
                'Key': file_name,
                'ContentType': 'text/csv'
            },
            ExpiresIn=3600
        )
        
        # DynamoDBにジョブを登録
        table = dynamodb.Table(JOB_TABLE)
        table.put_item(
            Item={
                'jobId': job_id,
                'status': 'PENDING',
                'createdAt': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())
            }
        )
        
        # 分析Lambdaを非同期で起動 (Event)
        # 注: 実際にはS3のアップロード完了イベントをトリガーにする方が確実ですが、
        # 今回はシンプルにAPIレスポンス後にポーリングを開始する想定で、
        # フロントエンドがアップロード完了後に別のAPIを叩くか、
        # ここで非同期起動してLambda側でS3の存在を待つなどの設計があります。
        # ここでは「アップロード用URLを返す」ことに専念します。
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'jobId': job_id,
                'uploadUrl': presigned_url
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
