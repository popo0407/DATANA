import json
import os
import boto3
import ipaddress

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
JOB_TABLE = os.environ['JOB_TABLE']
DATA_BUCKET = os.environ.get('DATA_BUCKET')
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
        return True
    
    request_key = headers.get('x-api-key') or headers.get('X-API-Key')
    return request_key == API_KEY

def handler(event, context):
    """
    ジョブのステータス確認
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

        # API Keyチェック
        if not headers.get('authorization') and not validate_api_key(headers):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized: Invalid API Key'})
            }

        job_id = event.get('pathParameters', {}).get('id')
        if not job_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing job ID'})}
            
        table = dynamodb.Table(JOB_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Job not found'})}
            
        item = response['Item']
        
        # COMPLETED の場合、結果取得用の Presigned URL を発行
        if item.get('status') == 'COMPLETED' and item.get('resultKey'):
            try:
                presigned_url = s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': DATA_BUCKET,
                        'Key': item['resultKey']
                    },
                    ExpiresIn=3600
                )
                item['resultUrl'] = presigned_url
            except Exception as e:
                print(f"Error generating presigned URL: {str(e)}")

        return {
            'statusCode': 200,
            'body': json.dumps(item, default=str)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
