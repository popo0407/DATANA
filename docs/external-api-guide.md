# 外部システム向け API 連携ガイド

本ガイドでは、Majin Analytics の分析機能を外部システムから呼び出すための具体的な手順を説明します。

## 1. 認証準備
API を呼び出すには、以下の情報が必要です。

- **API Endpoint**: `https://{api-id}.execute-api.{region}.amazonaws.com`
- **X-API-Key**: 管理者から発行された API キー
- **許可 IP**: 呼び出し元サーバーのグローバル IP アドレスが許可リストに登録されている必要があります。
- **S3 アクセス権限**: パターン A を使用する場合、対象の S3 バケットに対して Majin Analytics の Lambda ロールからの `s3:GetObject` 権限を許可する必要があります。

## 2. 連携フロー

### パターン A: S3 経由でのデータ提供 (推奨)
外部システムの S3 バケットにあるデータを直接分析する場合。

1. `POST /analyze` を呼び出し、`data_source` に S3 URI を指定。
2. 分析が完了すると、`callback_url` に通知が届く（指定した場合）。
3. `GET /jobs/{id}` で結果を取得。

### パターン B: 直接アップロード
分析データを API 経由でアップロードする場合。

1. `POST /analyze` を呼び出し、`uploadUrl` を取得。
2. `uploadUrl` に対して `PUT` リクエストで CSV ファイルを送信。
3. ポーリングまたは Webhook で完了を確認。

## 3. 実装例 (Python)

```python
import requests

API_URL = "https://your-api-id.execute-api.ap-northeast-1.amazonaws.com"
API_KEY = "your-api-key"

# 1. 分析ジョブの作成
res = requests.post(
    f"{API_URL}/analyze",
    headers={"X-API-Key": API_KEY},
    json={
        "data_source": {"type": "s3", "uri": "s3://my-bucket/input.csv"},
        "callback_url": "https://my-webhook.com/notify"
    }
)
job_id = res.json()["jobId"]

# 2. 状態確認 (Webhookを使わない場合)
status_res = requests.get(
    f"{API_URL}/jobs/{job_id}",
    headers={"X-API-Key": API_KEY}
)
print(status_res.json())
```

## 4. Webhook 通知の受信
分析完了時、指定した `callback_url` に以下の JSON が POST されます。

```json
{
  "jobId": "uuid-...",
  "status": "COMPLETED",
  "resultKey": "results/uuid-....json"
}
```
通知を受け取ったら、`GET /jobs/{id}` を呼び出して詳細な分析結果を取得してください。
