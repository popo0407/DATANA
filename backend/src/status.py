import json
import os
import boto3
import ipaddress

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
JOB_TABLE = os.environ['JOB_TABLE']
DATA_BUCKET = os.environ.get('DATA_BUCKET')
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
    ジョブのステータス確認
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
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(item, default=str)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
