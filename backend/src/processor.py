import json
import os
import re
import boto3
import pandas as pd
import io
import urllib3
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
http = urllib3.PoolManager()

DATA_BUCKET = os.environ['DATA_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']
MODEL_ID = os.environ.get('MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')

def send_webhook(callback_url, payload):
    """
    Webhook通知の送信
    """
    try:
        encoded_data = json.dumps(payload).encode('utf-8')
        res = http.request(
            'POST',
            callback_url,
            body=encoded_data,
            headers={'Content-Type': 'application/json'},
            timeout=10.0
        )
        print(f"Webhook sent to {callback_url}, status: {res.status}")
    except Exception as e:
        print(f"Failed to send webhook: {str(e)}")

def clean_num(val):
    """
    Aggressive Number Parsing: カンマ、円記号、全角数字などを除去して数値化
    """
    if pd.isna(val) or val == '':
        return 0
    s = str(val).replace(' ', '').replace('　', '')
    # 正規表現で数値、マイナス、ドット以外を除去
    s = re.sub(r'[^-0-9.]', '', s)
    try:
        return float(s)
    except:
        return 0

def call_bedrock(prompt, max_tokens=4000):
    """
    Bedrock (Claude 3.5 Sonnet) 呼び出しの共通関数
    """
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    })
    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    res_raw = json.loads(response['body'].read())['content'][0]['text']
    
    # JSON抽出ロジック
    json_match = re.search(r'\{.*\}', res_raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(), strict=False)
        except:
            return res_raw
    return res_raw

def aggregate_dynamic(df, spec):
    """
    AIプランに基づく動的集計
    spec: { id, title, type, dimension, metric, aggregation, limit }
    """
    dim = spec.get('dimension')
    met = spec.get('metric')
    agg_type = spec.get('aggregation', 'sum')
    limit = spec.get('limit', 10)
    chart_type = spec.get('type', 'bar')

    if dim not in df.columns or met not in df.columns:
        return {}

    if agg_type == 'sum':
        agg = df.groupby(dim)[met].sum()
    elif agg_type == 'count':
        agg = df.groupby(dim)[met].count()
    elif agg_type == 'mean':
        valid_df = df[df[met] > 0]
        agg = valid_df.groupby(dim)[met].mean() if not valid_df.empty else pd.Series()
    elif agg_type == 'max':
        agg = df.groupby(dim)[met].max()
    elif agg_type == 'min':
        agg = df.groupby(dim)[met].min()
    elif agg_type == 'std':
        agg = df.groupby(dim)[met].std()
    else:
        agg = df.groupby(dim)[met].sum()

    agg = agg.sort_values(ascending=False)

    # Ranking vs Share logic
    include_others = chart_type in ['pie', 'doughnut']
    
    if len(agg) > limit + 2:
        top_n = agg.head(limit)
        if include_others:
            others_val = agg.iloc[limit:].sum()
            others = pd.Series({'その他': others_val})
            return pd.concat([top_n, others]).to_dict()
        return top_n.to_dict()
    return agg.to_dict()

def handler(event, context):
    """
    汎用AI分析エンジン (Universal Semantic Analysis & Dynamic Execution)
    """
    table = dynamodb.Table(JOB_TABLE)
    job_id = None
    callback_url = None

    try:
        if 'Records' in event:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            job_id = key.split('/')[-1].replace('.csv', '')
        else:
            job_id = event.get('jobId')
            data_source = event.get('dataSource')
            if data_source and data_source.get('type') == 's3':
                # s3://bucket/key 形式をパース
                uri = data_source['uri'].replace('s3://', '')
                bucket, key = uri.split('/', 1)
            else:
                bucket = DATA_BUCKET
                key = f"uploads/{job_id}.csv"

        # ジョブ情報の取得 (callbackUrl確認用)
        job_item = table.get_item(Key={'jobId': job_id}).get('Item', {})
        callback_url = job_item.get('callbackUrl')

        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'PROCESSING'}
        )

        # 1. CSV取得 & エンコーディング判定
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        
        try:
            text = body.decode('utf-8-sig')
        except:
            text = body.decode('shift_jis', errors='replace')

        # 2. データ読み込み & サンプル抽出
        df_raw = pd.read_csv(io.StringIO(text))
        df_raw.columns = [c.strip() for c in df_raw.columns]
        sample_data = df_raw.head(5).to_json(orient='records', force_ascii=False)
        headers = list(df_raw.columns)

        # 2.5 DB構造情報の読み込み (もし存在すれば)
        db_info = ""
        db_txt_path = os.path.join(os.path.dirname(__file__), 'DB.txt')
        if os.path.exists(db_txt_path):
            try:
                with open(db_txt_path, 'r', encoding='utf-8') as f:
                    db_info = f.read()
            except:
                pass

        # 3. Step 1: Universal Semantic Analysis & Planning (AI)
        planning_prompt = f"""
        あなたは高度なデータサイエンティストであり、製造業の生産技術エキスパートです。
        提供されたCSVの構造と、以下のDB構造情報を分析し、生産性向上、品質改善、設備稼働率最適化の観点から最適な分析プランを策定してください。

        ## DB構造情報 (補足コンテキスト)
        {db_info if db_info else "なし"}

        ## CSVヘッダー
        {headers}

        ## サンプルデータ
        {sample_data}

        ## 依頼事項
        1. 各カラムの役割を特定してください (metric, dimension, date, ignore)。
           - 製造業の文脈（サイクルタイム、不良数、停止時間、温度、圧力、号機、ロット、工程など）を優先的に解釈すること。
           - 日付カラムは 'YYYYMMDDhhmmss' 形式や標準的な日時形式が含まれる可能性があります。
        2. 生産技術者が現場の課題（ボトルネック特定、バラツキ分析、相関分析）を解決するための、20種類のグラフ構成案を作成してください。
           - 比較(Ranking): 設備別停止時間、工程別不良率など。
           - 推移(Trend): サイクルタイム推移、歩留まり推移など。
           - 構成(Share): 停止要因内訳、不良内容内訳など。
           - 相関(Correlation): 圧力と寸法の関係、温度と不良率の関係など。
           - 分布(Distribution): 寸法精度のバラツキ（ヒストグラム的分析）、重量分布など。
           - グラフ種類は 'bar', 'line', 'pie', 'doughnut', 'scatter' から選択。

        ## 出力形式 (JSONのみ)
        {{
          "column_mapping": {{
            "カラム名": {{ "role": "metric|dimension|date|ignore", "label": "日本語表示名" }},
            ...
          }},
          "chart_specs": [
            {{
              "id": "g1",
              "title": "グラフタイトル",
              "type": "bar|line|pie|doughnut|scatter",
              "dimension": "X軸または分類に使うカラム名",
              "metric": "集計対象のカラム名",
              "aggregation": "sum|count|mean|max|min|std",
              "limit": 10
            }},
            ... (20個以上)
          ]
        }}
        """
        
        plan = call_bedrock(planning_prompt)
        if not isinstance(plan, dict):
            raise Exception("AI Planning failed to return valid JSON")

        # プランをDynamoDBに保存
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET analysisPlan = :p",
            ExpressionAttributeValues={':p': plan}
        )

        # 4. Step 2: Dynamic Execution (Pandas)
        # データクレンジング
        df = df_raw.copy()
        col_map = plan.get('column_mapping', {})
        
        metrics = [c for c, m in col_map.items() if m.get('role') == 'metric']
        dates = [c for c, m in col_map.items() if m.get('role') == 'date']
        
        for m in metrics:
            df[m] = df[m].apply(clean_num)
        
        for d in dates:
            # YYYYMMDDhhmmss 形式や標準的な形式を柔軟にパース
            df[d] = pd.to_datetime(df[d], format='%Y%m%d%H%M%S', errors='coerce').fillna(
                pd.to_datetime(df[d], errors='coerce')
            )
            # 日付がパースできない行は除外せず、集計時に考慮
        
        # 動的集計
        charts_res = {}
        for spec in plan.get('chart_specs', []):
            chart_id = spec.get('id')
            if spec.get('type') == 'scatter':
                # 散布図はサンプリングして生データを返す
                m1 = spec.get('dimension') # X
                m2 = spec.get('metric')    # Y
                if m1 in df.columns and m2 in df.columns:
                    charts_res[chart_id] = df.sample(min(100, len(df)))[[m1, m2]].to_dict(orient='records')
            elif col_map.get(spec.get('dimension'), {}).get('role') == 'date':
                # 時系列集計
                d_col = spec.get('dimension')
                m_col = spec.get('metric')
                agg_type = spec.get('aggregation', 'sum')
                
                if d_col in df.columns and m_col in df.columns:
                    # 期間に応じて粒度を自動調整 (時間, 日, 月)
                    delta = df[d_col].max() - df[d_col].min()
                    if delta.days < 2:
                        resampled = df.set_index(d_col)[m_col].resample('H')
                    elif delta.days < 60:
                        resampled = df.set_index(d_col)[m_col].resample('D')
                    else:
                        resampled = df.set_index(d_col)[m_col].resample('M')
                    
                    if agg_type == 'mean':
                        charts_res[chart_id] = resampled.mean().dropna().to_dict()
                    elif agg_type == 'max':
                        charts_res[chart_id] = resampled.max().dropna().to_dict()
                    else:
                        charts_res[chart_id] = resampled.sum().dropna().to_dict()
                    
                    # キーを文字列に変換
                    charts_res[chart_id] = {str(k): v for k, v in charts_res[chart_id].items()}
            else:
                charts_res[chart_id] = aggregate_dynamic(df, spec)

        # 5. Step 3: Strategic Insight (AI)
        metrics_summary = {}
        for m in metrics[:5]:
            # 指標名に「率」や「タイム」「温度」「圧力」が含まれる場合は平均、それ以外は合計
            if any(x in m for x in ['率', 'タイム', 'Time', '温度', 'Temp', '圧力', 'Press', '単価', '精度']):
                metrics_summary[m] = float(df[m].mean())
            else:
                metrics_summary[m] = float(df[m].sum())

        summary = {
            "total_rows": len(df),
            "metrics_summary": metrics_summary
        }

        insight_prompt = f"""
        あなたは製造現場の改善を専門とする生産技術コンサルタントです。
        以下の集計結果を分析し、現場の生産性向上と品質改善に向けた戦略レポートを作成してください。

        ## データ概要
        {json.dumps(summary, ensure_ascii=False)}

        ## 集計結果 (一部)
        {json.dumps({k: v for k, v in list(charts_res.items())[:10]}, ensure_ascii=False)}

        ## レポート要件 (Markdown)
        1. 現状の課題と傾向分析 (70%): ボトルネック、バラツキ、異常値の指摘。
        2. 具体的な改善アクション案 (30%): 設備調整、工程見直し、品質管理の強化策。
        
        ※重要事項：
        - 見出し（# ## ###）を適切に使い、構造化してください。
        - **太字**や<u>下線</u>（HTMLタグ <u></u> を使用可）、リスト（- や 1.）を多用し、視覚的に重要なポイントがすぐわかるようにしてください。
        - 数値や重要なキーワードは強調してください。
        - 見出しに「70%」等の数値を含めないこと。
        - 各グラフ(g1-g20)への短い気づき(micro_insights)も作成してください。

        ## 出力形式 (JSON)
        {{
          "global_report": "Markdown形式のレポート",
          "micro_insights": {{ "g1": "...", "g2": "...", ... }}
        }}
        """
        
        ai_data = call_bedrock(insight_prompt)
        if not isinstance(ai_data, dict):
            ai_data = {"global_report": str(ai_data), "micro_insights": {}}

        # 6. 結果保存
        final_result = {
            'jobId': job_id,
            'summary': summary,
            'charts': charts_res,
            'ai_report': ai_data.get('global_report', ''),
            'micro_insights': ai_data.get('micro_insights', {}),
            'analysisPlan': plan,
            'processedAt': datetime.utcnow().isoformat()
        }
        
        result_key = f"results/{job_id}.json"
        s3.put_object(
            Bucket=DATA_BUCKET,
            Key=result_key,
            Body=json.dumps(final_result, ensure_ascii=False),
            ContentType='application/json'
        )

        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #s = :s, resultKey = :rk",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'COMPLETED', ':rk': result_key}
        )

        # Webhook通知
        if callback_url:
            send_webhook(callback_url, {
                'jobId': job_id,
                'status': 'COMPLETED',
                'resultKey': result_key
            })

    except Exception as e:
        print(f"Error: {str(e)}")
        if job_id:
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression="SET #s = :s, #e = :e",
                ExpressionAttributeNames={'#s': 'status', '#e': 'error'},
                ExpressionAttributeValues={':s': 'FAILED', ':e': str(e)}
            )
            if callback_url:
                send_webhook(callback_url, {
                    'jobId': job_id,
                    'status': 'FAILED',
                    'error': str(e)
                })

