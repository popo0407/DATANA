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
API_KEY = os.environ.get('API_KEY')

def is_ip_allowed(source_ip):
...existing code...
    except Exception as e:
        print(f"IP validation error: {e}")
        return False

def validate_api_key(headers):
    """
    API Keyの検証
    """
    if not API_KEY:
        return True # API Keyが設定されていない場合はスキップ
    
    request_key = headers.get('x-api-key') or headers.get('X-API-Key')
    return request_key == API_KEY

def handler(event, context):
    """
    分析ジョブの受付
    1. IP制限チェック
    2. API Keyチェック
    3. ジョブID発行
    4. S3 Presigned URL発行 または 外部S3ソースの登録
    5. DynamoDBに初期状態保存
    6. 分析Lambdaを非同期で起動 (外部ソース時のみ即時)
    """
    try:
        headers = event.get('headers', {})
        
        # IP制限チェック
        source_ip = event.get('requestContext', {}).get('http', {}).get('sourceIp')
        if source_ip and not is_ip_allowed(source_ip):
            print(f"Access denied for IP: {source_ip}")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: IP address not allowed'})
            }

        # API Keyチェック (外部システムからの呼び出しを想定)
        # フロントエンドからの呼び出し（Authorizationヘッダーあり）はCognitoで検証済みとする
        if not headers.get('authorization') and not validate_api_key(headers):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized: Invalid API Key'})
            }

        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass

        job_id = str(uuid.uuid4())
        data_source = body.get('data_source')
        callback_url = body.get('callback_url')
        
        item = {
            'jobId': job_id,
            'status': 'PENDING',
            'createdAt': datetime.utcnow().isoformat(),
            'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())
        }

        if callback_url:
            item['callbackUrl'] = callback_url

        response_body = {'jobId': job_id}

        if data_source and data_source.get('type') == 's3' and data_source.get('uri'):
            # 外部S3ソースが指定された場合
            item['dataSource'] = data_source
            item['status'] = 'PROCESSING' # 即時開始
            
            # DynamoDBに登録
            table = dynamodb.Table(JOB_TABLE)
            table.put_item(Item=item)
            
            # 分析Lambdaを非同期で起動
            lambda_client.invoke(
                FunctionName=PROCESS_FUNCTION,
                InvocationType='Event',
                Payload=json.dumps({
                    'jobId': job_id,
                    'dataSource': data_source
                })
            )
        else:
            # 通常のアップロードフロー
            file_name = f"uploads/{job_id}.csv"
            presigned_url = s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': DATA_BUCKET,
                    'Key': file_name,
                    'ContentType': 'text/csv'
                },
                ExpiresIn=3600
            )
            response_body['uploadUrl'] = presigned_url
            
            # DynamoDBに登録
            table = dynamodb.Table(JOB_TABLE)
            table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
