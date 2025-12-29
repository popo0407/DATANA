# システム設計書: Majin Analytics (AWS 版)

## 1. 概要

本システムは、CSV データをアップロードし、AI（Amazon Bedrock）による高度な分析レポートと、Chart.js による 20 種類以上の動的グラフを生成するデータ分析 Web アプリケーションである。特に製造業の生産技術者による設備ログや品質データの分析を主眼に置き、ボトルネック特定やバラツキ分析を自動化する。

## 2. アーキテクチャ

REST API + ポーリング方式を採用し、ブラウザおよび外部ツール（Excel 等）からの利用を可能にする。

### 構成図

```mermaid
flowchart TD
    User((User / Browser))
    Excel((Excel / VBA))

    subgraph AWS_Cloud [AWS Cloud]
        subgraph Frontend_Hosting [Frontend Hosting]
            CF[CloudFront]
            S3Web[S3 Bucket Web Assets]
        end

        subgraph Authentication [Authentication]
            Cognito[Cognito User Pool]
        end

        subgraph Backend_API [Backend API]
            APIGW[API Gateway HTTP API]

            subgraph Compute [Compute]
                LambdaAuth[Lambda: Authorizer]
                LambdaDispatch[Lambda: Job Dispatcher]
                LambdaProcess[Lambda: Analysis & AI]
                LambdaStatus[Lambda: Check Status]
            end

            subgraph Storage [Storage]
                DDB[(DynamoDB Job State)]
                S3Data[(S3 Bucket User Data)]
            end

            subgraph AI_Service [AI Service]
                Bedrock[Amazon Bedrock Claude 3.5 Sonnet]
            end
        end
    end

    User -->|HTTPS| CF
    CF --> S3Web

    User -->|Auth| Cognito
    Excel -->|Auth| Cognito

    User -->|REST Polling| APIGW
    Excel -->|REST Polling| APIGW

    APIGW -->|POST /analyze| LambdaDispatch
    APIGW -->|GET /jobs/{id}| LambdaStatus

    LambdaDispatch -->|Async Invoke| LambdaProcess
    LambdaDispatch -->|Create Job| DDB

    LambdaProcess --> S3Data
    LambdaProcess -->|Update Status| DDB
    LambdaProcess --> Bedrock

    LambdaStatus -->|Read Status| DDB
```

## 3. コンポーネント詳細

### 3.1 Frontend (React + Tailwind CSS)

フロントエンドは、ユーザーインターフェースの提供、データのアップロード管理、および分析結果の動的レンダリングを担当する。

- **コンポーネント構成:**
  - `App.jsx`: メインロジック、状態管理（Job ID, Status, Result）、API 通信、エクスポート処理を統括。
  - `SplashScreen.jsx`: 初期表示画面。ファイル選択ボタンのみを配置し、分析開始のトリガーとなる。
  - `ChartCard.jsx`: 個別のグラフ描画コンポーネント。Chart.js を使用し、`analysisPlan` に基づく動的な設定変更に対応。
  - `KPIPanel.jsx`: 総売上、件数などの主要指標をスリムなデザインで表示。
- **動的レンダリングロジック:**
  - バックエンドから返却される `analysisPlan`（グラフの種類、タイトル、軸設定）をループ処理し、`ChartCard` を動的に生成する。
  - `formatShortNumber` 関数により、軸やラベルの数値を「1.2 億」「3500 万」形式に自動変換。
- **状態管理と遷移:**
  - `isLoaded`: ファイルアップロード済みか。
  - `isLoading`: 分析中（ポーリング中）か。
  - `layoutMode`: 1 列（詳細）/ 2 列（一覧）の切り替え。
- **エクスポート機能:**
  - `jsPDF` + `html2canvas`: ダッシュボードの PDF 出力。
  - `Blob` API: 分析データ（JSON）およびインタラクティブな単一 HTML レポートの生成。

### 3.2 Backend (API Gateway + Lambda)

- **API Gateway (HTTP API):** 低レイテンシな RESTful エンドポイントを提供。
- **認証:** Cognito JWT Authorizer により、正当なユーザーのみが分析を実行可能。
- **エンドポイント:**
  - `POST /analyze`:
    - ジョブ ID 発行。
    - S3 アップロード用 Presigned URL 生成。
    - DynamoDB に `PENDING` 状態でレコード作成。
  - `GET /jobs/{id}`:
    - DynamoDB から現在のステータス、エラー内容、および完了時の結果 URL を取得。

### 3.3 Backend (Compute: Analysis Engine)

分析 Lambda は、Pandas による高速なデータ処理と Bedrock による AI 推論を組み合わせた「汎用分析エンジン」として動作する。

- **Step 1: Universal Semantic Analysis & Planning (AI):**
  - **入力:** CSV ヘッダー + サンプルデータ（5 行）。
  - **処理:** Bedrock (Claude 3.5 Sonnet) に対し、データの意味論的解析を依頼。製造業のドメイン知識（サイクルタイム、不良率、設備稼働率等）を優先的に適用。
  - **出力:**
    - `column_mapping`: 各カラムの役割（Metric, Dimension, Date, Ignore）。
    - `chart_specs`: 20 種類以上のグラフ構成案（ID, Title, Type, X/Y axis, Aggregation）。パレート図や散布図による相関分析を重視。
  - **保存:** このプランを DynamoDB の `analysisPlan` フィールドに JSON として保存。
- **Step 2: Dynamic Execution (Pandas):**
  - **クレンジング:** `column_mapping` に基づき、数値カラムの記号除去（¥, カンマ）や日付変換を自動実行。
  - **集計:** `chart_specs` をループし、Pandas の `groupby` や `resample` を用いて動的に集計。
  - **最適化:** 項目数が多い Dimension は自動的に「上位 10 件＋その他」に集約。
- **Step 3: Strategic Insight (AI):**
  - **入力:** 全集計結果のサマリー。
  - **処理:** Bedrock により、生産技術エキスパートの視点から戦略レポート（現状分析 7 割、改善アクション 3 割）を生成。
  - **出力:** Markdown 形式のレポートと、各グラフへのマイクロインサイト。

### 3.4 Data Schema

#### DynamoDB (JobTable)

| 属性名         | 型          | 説明                                            |
| :------------- | :---------- | :---------------------------------------------- |
| `jobId`        | String (PK) | ユニークなジョブ ID                             |
| `status`       | String      | PENDING, PROCESSING, COMPLETED, FAILED          |
| `analysisPlan` | Map/JSON    | AI が策定した分析プラン（カラム定義・グラフ案） |
| `resultKey`    | String      | S3 上の結果 JSON へのパス                       |
| `error`        | String      | 失敗時のエラーメッセージ                        |
| `createdAt`    | Number      | TTL 用のタイムスタンプ                          |

#### S3 (DataBucket)

- `uploads/{jobId}.csv`: ユーザーがアップロードした生データ。
- `results/{jobId}.json`: 最終的な集計結果、AI レポート、マイクロインサイトを含む完全なデータセット。

### 3.4 Storage

- **S3 (Data):** ユーザーデータおよび分析結果の保存。ライフサイクルポリシーにより自動削除設定。
- **DynamoDB:** ジョブのステータス管理（PENDING, PROCESSING, COMPLETED, FAILED）。

## 4. セキュリティ

- 全ての API リクエストは Cognito JWT による認証を必須とする。
- S3 バケットはパブリックアクセス禁止。Presigned URL による一時的なアクセスのみ許可。
- IAM ロールは最小権限の原則に従う。

## 5. 運用・拡張性

- **環境変数:** AI モデル ID、データ保存期間、デバッグモード等を Lambda 環境変数で制御。
- **IaC:** 全てのリソースを CloudFormation で管理。
