# 外部システム向け API 公開設計書 (External API Design)

## 1. 目的
本ドキュメントは、Majin Analytics の分析機能を外部システム（ERP、生産管理システム等）からプログラム経由で利用するための API 仕様および実装方針を定義する。

## 2. 認証方式
外部システムとのサーバー間通信を想定し、以下の方式を採用する。

- **方式**: API Gateway API Key + Usage Plan
- **理由**: 
  - ユーザー個別のログイン（Cognito）を介さずに認証が可能。
  - クライアントごとの流量制限（スロットリング）やクォータ設定が容易。
  - 実装コストが低く、標準的な API 公開手法である。

## 3. API エンドポイント仕様

### 3.1 分析ジョブの作成 (POST /analyze)
既存のエンドポイントを拡張し、外部システム向けのオプションを追加する。

**Request Body (JSON):**
```json
{
  "filename": "production_log_202312.csv",
  "data_source": {
    "type": "s3", 
    "uri": "s3://external-bucket/data.csv"
  },
  "callback_url": "https://external-system.com/api/webhook",
  "options": {
    "priority": "high"
  }
}
```
- `data_source` (Optional): 指定がない場合は、レスポンスで返却される `uploadUrl` (Presigned URL) を使用してアップロードする。
- `callback_url` (Optional): 分析完了時に結果を通知する URL。

**Response (JSON):**
```json
{
  "jobId": "uuid-1234-5678",
  "status": "PENDING",
  "uploadUrl": "https://s3... (data_source未指定時のみ)"
}
```

### 3.2 ジョブ状態・結果の取得 (GET /jobs/{id})
分析結果の JSON データを直接取得できるようにする。

**Response (JSON):**
```json
{
  "jobId": "uuid-1234-5678",
  "status": "COMPLETED",
  "result": {
    "summary": "分析結果の要約...",
    "analysisPlan": [ ... ],
    "data": [ ... ]
  }
}
```

## 4. Webhook 通知仕様
分析完了時（`COMPLETED` または `FAILED`）、`callback_url` に対して以下のデータを POST する。

**Payload:**
```json
{
  "jobId": "uuid-1234-5678",
  "status": "COMPLETED",
  "result_url": "https://api-endpoint/jobs/uuid-1234-5678"
}
```

## 5. 実装ステップ

1. **API Gateway 設定変更**: API Key 認証を有効化した新しいステージまたはリソースを作成。
2. **Dispatcher Lambda 修正**: `data_source` や `callback_url` の受け取り、DynamoDB への保存処理を追加。
3. **Processor Lambda 修正**: 
   - `data_source` が S3 URI の場合、そのファイルを読み込む処理を追加。
   - 処理完了後、DynamoDB から `callback_url` を取得し、HTTP POST を実行する処理を追加。
4. **ドキュメント作成**: OpenAPI 3.0 形式で仕様書を出力。

## 6. セキュリティ考慮事項
- API Key は `X-API-Key` ヘッダーで送信する。
- Webhook 送信時には、改ざん防止のための署名（HMAC 等）をヘッダーに付与することを検討する。
