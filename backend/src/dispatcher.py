import json
import os
import uuid
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

DATA_BUCKET = os.environ['DATA_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']
PROCESS_FUNCTION = os.environ['PROCESS_FUNCTION']

def handler(event, context):
    """
    分析ジョブの受付
    1. ジョブID発行
    2. S3 Presigned URL発行 (アップロード用)
    3. DynamoDBに初期状態保存
    4. 分析Lambdaを非同期で起動
    """
    try:
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
