# 開発タスクリスト: Majin Analytics

## フェーズ 1: インフラ構築 (CloudFormation)

- [x] 1.1 S3 バケットの作成 (Frontend 用, Data 用)
- [x] 1.2 DynamoDB テーブルの作成 (JobState)
- [x] 1.3 IAM ロールとポリシーの定義 (Lambda 用)
- [x] 1.4 API Gateway (HTTP API) の基本設定
- [x] 1.5 CloudFront + OAC の設定

## フェーズ 2: バックエンド実装 (Lambda)

- [x] 2.1 Lambda Authorizer (Cognito 連携) の実装
- [x] 2.2 Job Dispatcher Lambda の実装 (POST /analyze)
- [x] 2.3 Job Status Lambda の実装 (GET /jobs/{id})
- [x] 2.4 Analysis & AI Lambda の実装
  - [x] 2.4.1 データクレンジングロジック (BOM 除去, 数値変換)
  - [x] 2.4.2 統計集集計ロジック (20 種以上のグラフデータ)
  - [x] 2.4.3 Bedrock (Claude 3.5 Sonnet) 連携プロンプト実装
- [x] 2.5 API Gateway と Lambda の統合

## フェーズ 3: フロントエンド実装 (React)

- [x] 3.1 プロジェクト初期化 (Vite + React + Tailwind)
- [x] 3.2 Cognito 認証連携 (AWS Amplify Auth または独自実装)
- [x] 3.3 ファイルアップロード機能 (Presigned URL)
- [x] 3.4 ポーリングによる進捗管理 UI
- [x] 3.5 ダッシュボード表示 (Chart.js 20 種)
- [x] 3.6 AI レポート表示 (Markdown)
- [x] 3.7 エクスポート機能 (PDF, JSON, HTML)

## フェーズ 4: 統合・テスト

- [x] 4.1 エンドツーエンドテスト (CSV アップロード〜レポート生成)
- [x] 4.2 Excel (VBA) からの呼び出しテスト
- [x] 4.3 ドキュメント作成 (README.md, 利用マニュアル)

## フェーズ 6: 汎用 AI 分析エンジンへの刷新 (Universal Semantic Analysis)

- [x] 6.1 [Backend] AI プランニング機能の実装
  - [x] 6.1.1 カラム意味解析プロンプトの作成 (Semantic Analysis)
  - [x] 6.1.2 20 種以上のグラフ構成案生成プロンプトの作成 (Composition Plan)
  - [x] 6.1.3 DynamoDB への `analysisPlan` 保存ロジック追加
- [x] 6.2 [Backend] 動的集計エンジンの実装
  - [x] 6.2.1 AI プランに基づく Pandas 動的集計ロジック
  - [x] 6.2.2 汎用的なデータクレンジング・表記揺れ吸収の強化
- [x] 6.3 [Frontend] 動的ダッシュボードの刷新
  - [x] 6.3.1 `chartConfigs` 固定定義の廃止と動的レンダリング実装
  - [x] 6.3.2 スプラッシュ画面 (Splash Screen) の実装
  - [x] 6.3.3 コンパクトヘッダーとレイアウト切替機能の実装
  - [x] 6.3.4 数値の短縮表示 (formatShortNumber) の徹底適用
- [x] 6.4 [Docs] 振り返り (retrospective.md) の更新
- [x] 6.5 [Docs] README.md の更新
- [x] 6.6 [Git] 最終成果物のコミットとプッシュ
- [x] 7.1 [Backend] 製造業向けプロンプトの最適化 (processor.py)
- [x] 7.2 [Data] 製造業向けサンプルデータの作成 (input/production_data.csv)
- [x] 7.3 [Docs] 製造業視点でのシステムデザイン更新 (system-design.md)

## フェーズ 8: 外部システム向け API 公開

- [x] 8.1 [Infra] API Key 認証の導入 (API Gateway Usage Plan)
- [x] 8.2 [Infra] IP アドレス制限の実装 (AllowedIpRange パラメータ追加)
- [x] 8.3 [Backend] Webhook 通知機能の実装 (callback_url 対応)
- [x] 8.4 [Backend] データ入力方式の拡張 (S3 URI / Direct Data)
- [x] 8.5 [Docs] OpenAPI 3.0 仕様書の作成
- [x] 8.6 [Docs] 外部システム向け連携ガイドの作成
