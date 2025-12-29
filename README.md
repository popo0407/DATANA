# 🚀 MAJIN Data Analysis System (AWS Serverless)

このシステムは、高度なデータ分析プロンプトのロジックを AWS サーバーレスアーキテクチャ上で再現した、プロフェッショナルなデータ分析プラットフォームです。特に製造業の生産技術者による設備ログや品質データの分析を強力にサポートします。

## 🏗️ アーキテクチャ

- **Frontend**: React + Tailwind CSS + Chart.js (Hosted on S3 + CloudFront)
- **Backend**: Python 3.12 + Pandas (Lambda)
- **AI**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Database**: DynamoDB (Job Management)
- **Storage**: S3 (Data & Frontend Hosting)
- **API**: API Gateway (REST API)

## 🚀 デプロイ手順

### 1. 事前準備

- AWS CLI がインストールされ、適切な権限（AdministratorAccess 推奨）で設定されていること。
- Node.js (v18 以上) がインストールされていること。
- Python 3.12 がインストールされていること。

### 2. インフラのデプロイ

CloudFormation を使用して、すべての AWS リソースを構築します。
`powershell
.\scripts\deploy-infra.ps1
`

### 3. アプリケーションのデプロイ

インフラの準備ができたら、バックエンドとフロントエンドをデプロイします。

`powershell

# バックエンド（Lambda 関数）のデプロイ

.\scripts\deploy-backend.ps1

# フロントエンド（React + S3/CloudFront）のデプロイ

.\scripts\deploy-frontend.ps1
`

デプロイ完了後、フロントエンドの URL（CloudFront のドメイン）がターミナルに表示されます。

## 📊 汎用セマンティック分析エンジン (Universal AI Engine)

本システムは、Amazon Bedrock (Claude 3.5 Sonnet) を活用した「汎用セマンティック分析」エンジンを搭載しています。アップロードされた CSV データの構造を AI が自動的に解釈し、データに最適な分析プランを動的に生成します。製造現場のデータ（サイクルタイム、不良率、設備稼働率など）に対しても、生産技術エキスパートの視点で深い洞察を提供します。

### 分析プロセス

1.  **Semantic Planning**: データの列定義（指標、属性、時間軸）を特定し、製造現場の課題解決に直結する 20 以上の最適なグラフ構成を計画。
2.  **Dynamic Execution**: AI が生成したプランに基づき、Pandas を用いて動的に集計処理を実行。
3.  **Strategic Insight**: 集計結果から、ボトルネック特定や品質改善アクションプランを AI が生成。

### 生成されるレポート内容

- **KPI サマリー**: 主要な指標（売上、数量、利益等）の自動抽出と集計。
- **動的グラフ群**: 時系列推移、ランキング、構成比、分布、相関など、データ特性に合わせた 20 種類以上の可視化。
- **AI 洞察**: データの傾向、異常値、改善提案などのテキスト解説。

## 📄 エクスポート機能

- **PDF**: ダッシュボード全体を PDF として保存
- **JSON**: 分析データ（生データ）を JSON 形式で保存
- **HTML**: インタラクティブなグラフを含む単一 HTML ファイルとして保存

## 🛠️ 開発者向け情報

- **Backend**: ackend/src/ に分析ロジックと AI プロンプトがあります。
- **Frontend**: rontend/src/ に React コンポーネントがあります。
- **Infrastructure**: infra/ に CloudFormation テンプレートがあります。

## 📝 ライセンス

MIT License
