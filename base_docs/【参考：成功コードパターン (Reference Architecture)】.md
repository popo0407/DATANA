### 【参考：成功コードパターン (Reference Architecture)】
**以下のコード構造は、実務運用で検証済みの「最終形態」です。この構造（CDN読み込み、BOM除去、Chart.js設定、AI連携、PDF出力ロジック、エラー分離、データクレンジング、項目集約）をそのままテンプレートとして採用し、実装してください。**

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小売・流通業向け 高度データ分析ダッシュボード</title>
    
    <!-- 1. Technical Stack & Libraries (CDN) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    
    <!-- Fonts & Global Styles -->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap');
        
        body { 
            font-family: 'Inter', 'Noto Sans JP', sans-serif; 
            background-color: #f8fafc; 
            color: #1e293b;
            overflow-x: hidden; /* Prevent horizontal scroll */
        }
        
        /* Container Constraint */
        .app-container { 
            max-width: 1200px; 
            margin: 0 auto; 
            width: 100%; 
            padding: 1rem; 
        }

        /* Chart Card Styling */
        .chart-card { 
            background: white; 
            border-radius: 1rem; 
            border: 1px solid #e2e8f0; 
            padding: 1.25rem; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
            display: flex; 
            flex-direction: column; 
            width: 100%; 
            overflow: hidden; 
            transition: transform 0.2s;
            break-inside: avoid; /* Print optimization */
        }
        .chart-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .chart-container { 
            position: relative; 
            width: 100%; 
            transition: height 0.3s ease; 
        }
        
        /* Layout Modes */
        .cols-1 .chart-container { height: 420px; }
        .cols-2 .chart-container { height: 280px; }

        .dashboard-grid { 
            display: grid; 
            gap: 1.5rem; 
            width: 100%; 
        }
        .cols-1 { grid-template-columns: 1fr; }
        .cols-2 { grid-template-columns: repeat(2, 1fr); }
        
        @media (max-width: 768px) { 
            .cols-2 { grid-template-columns: 1fr; } 
            .cols-2 .chart-container { height: 350px; }
        }

        /* Professional AI Insight Styling */
        .prose-ai { font-size: 0.95rem; line-height: 1.7; color: #334155; }
        .prose-ai h1 { font-size: 1.5rem; font-weight: 800; margin: 1.5rem 0 1rem; color: #1e3a8a; border-left: 4px solid #2563eb; padding-left: 0.75rem;}
        .prose-ai h2 { font-size: 1.25rem; font-weight: 700; margin: 1.25rem 0 0.75rem; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.25rem; }
        .prose-ai h3 { font-size: 1.1rem; font-weight: 700; margin: 1rem 0 0.5rem; color: #2563eb; display: flex; align-items: center; gap: 0.5rem;}
        .prose-ai h3::before { content: "■"; font-size: 0.8em; color: #60a5fa; }
        .prose-ai ul { list-style-type: disc; margin-left: 1.5rem; margin-bottom: 1rem; }
        .prose-ai li { margin-bottom: 0.25rem; }
        /* Strong tag styling - ensure bold is visible */
        .prose-ai strong, .prose-ai b { 
            color: #1e3a8a; 
            font-weight: 800; 
            background: linear-gradient(transparent 60%, #bfdbfe 60%); 
            padding-left: 2px;
            padding-right: 2px;
            border-radius: 2px;
        }
        .prose-ai table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.85rem; border: 1px solid #e2e8f0; }
        .prose-ai th { background: #f8fafc; padding: 0.75rem; border: 1px solid #cbd5e1; text-align: left; font-weight: 600; color: #475569;}
        .prose-ai td { padding: 0.75rem; border: 1px solid #cbd5e1; background: white; }
        .prose-ai tr:nth-child(even) td { background: #f9fafb; }

        /* Loading & Header */
        .loading-overlay { background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(4px); }
        /* Header Hidden Initially */
        #appHeader.hidden { display: none; }
        header { position: sticky; top: 0; z-index: 50; transition: all 0.3s; }
        
        /* Custom Scrollbar for Filters */
        .filter-scroll::-webkit-scrollbar { height: 4px; }
        .filter-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

        /* Splash Screen */
        .splash-screen {
            position: fixed;
            inset: 0;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            z-index: 40;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .splash-screen.hidden { display: none; }
    </style>
</head>
<body>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="fixed inset-0 z-[100] flex flex-col items-center justify-center hidden loading-overlay">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mb-4"></div>
        <p class="text-lg font-bold text-slate-700 animate-pulse" id="loadingText">システムを起動中...</p>
    </div>

    <!-- Initial Splash Screen (Visible on Load) -->
    <div id="initialSplash" class="splash-screen">
        <div class="text-center p-10 max-w-lg w-full">
            <div class="mb-8 flex justify-center">
                <div class="bg-white p-6 rounded-3xl shadow-xl border border-slate-100">
                    <i data-lucide="bar-chart-3" class="w-20 h-20 text-blue-600"></i>
                </div>
            </div>
            <!-- Updated Title -->
            <h1 class="text-3xl font-extrabold text-slate-800 mb-3 tracking-tight">Majin Analytics</h1>
            <p class="text-slate-500 mb-10 font-medium">高度なデータ分析とAI戦略レポートを、<br>あなたのローカル環境で。</p>
            
            <label class="group relative flex items-center justify-center gap-4 w-full bg-blue-600 hover:bg-blue-700 text-white text-lg font-bold py-5 px-8 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-blue-500/30 active:scale-[0.98] overflow-hidden">
                <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <i data-lucide="upload-cloud" class="w-7 h-7 relative z-10"></i>
                <span class="relative z-10">データ分析を開始する (CSV)</span>
                <input type="file" id="csvFileInputSplash" class="hidden" accept=".csv">
            </label>
        </div>
    </div>

    <!-- Compact Header (Hidden Initially) -->
    <header id="appHeader" class="bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm sticky top-0 z-50 hidden">
        <div class="max-w-[1200px] mx-auto px-4 py-2">
            <div class="flex flex-wrap items-center justify-between gap-3">
                
                <!-- Left: File Operations -->
                <div class="flex items-center gap-2">
                    <label class="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-xs font-bold cursor-pointer transition-all shadow-sm active:scale-95 whitespace-nowrap">
                        <i data-lucide="upload" class="w-3.5 h-3.5"></i>
                        <span>CSV再読込</span>
                        <input type="file" id="csvFileInputHeader" class="hidden" accept=".csv">
                    </label>
                    <button id="btnExportPdf" class="flex items-center gap-2 px-3 py-1.5 bg-slate-700 text-white rounded-md hover:bg-slate-600 text-xs font-bold transition-all shadow-sm active:scale-95 hidden whitespace-nowrap">
                        <i data-lucide="file-down" class="w-3.5 h-3.5"></i>
                        <span>PDF保存</span>
                    </button>
                    <!-- New JSON Export Button -->
                    <button id="btnExportJson" class="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 text-white rounded-md hover:bg-emerald-500 text-xs font-bold transition-all shadow-sm active:scale-95 hidden whitespace-nowrap">
                        <i data-lucide="file-json" class="w-3.5 h-3.5"></i>
                        <span>JSON保存</span>
                    </button>
                </div>

                <!-- Right: Controls & Filters (Single Line) -->
                <div id="controlPanel" class="flex flex-wrap items-center gap-2 flex-1 justify-end">
                    
                    <!-- Filters -->
                    <div class="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded-md border border-slate-200 opacity-50 pointer-events-none" id="filterContainer1">
                        <i data-lucide="store" class="w-3 h-3 text-slate-400"></i>
                        <select id="filterStore" class="bg-transparent text-xs font-semibold focus:outline-none max-w-[100px] text-slate-600">
                            <option value="all">全店舗</option>
                        </select>
                    </div>

                    <div class="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded-md border border-slate-200 opacity-50 pointer-events-none" id="filterContainer2">
                        <i data-lucide="calendar" class="w-3 h-3 text-slate-400"></i>
                        <div class="flex items-center gap-1">
                            <input type="month" id="filterDateStart" class="bg-transparent text-[10px] font-semibold focus:outline-none w-[75px] text-slate-600">
                            <span class="text-slate-300">-</span>
                            <input type="month" id="filterDateEnd" class="bg-transparent text-[10px] font-semibold focus:outline-none w-[75px] text-slate-600">
                        </div>
                    </div>

                    <!-- Layout Toggle -->
                    <div class="flex items-center bg-slate-100 p-0.5 rounded-md border border-slate-200 ml-1">
                        <button id="btnLayout1" class="p-1 rounded bg-white shadow-sm text-blue-600 transition-all" title="1列">
                            <i data-lucide="layout-list" class="w-3.5 h-3.5"></i>
                        </button>
                        <button id="btnLayout2" class="p-1 rounded text-slate-400 hover:text-slate-600 transition-all" title="2列">
                            <i data-lucide="layout-grid" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main class="app-container py-6">
        
        <!-- Dashboard Content -->
        <div id="dashboardContent" class="hidden space-y-6">
            
            <!-- KPI Cards with Icons -->
            <!-- Added ID for PDF Capture -->
            <section id="kpiSection" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <i data-lucide="banknote" class="w-16 h-16 text-blue-600"></i>
                    </div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">売上総額</p>
                    <h3 id="kpi-sales" class="text-xl font-extrabold text-slate-800 tracking-tight">-</h3>
                </div>

                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <i data-lucide="trending-up" class="w-16 h-16 text-emerald-600"></i>
                    </div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">粗利益率</p>
                    <h3 id="kpi-margin" class="text-xl font-extrabold text-emerald-600 tracking-tight">-</h3>
                </div>

                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <i data-lucide="shopping-cart" class="w-16 h-16 text-indigo-600"></i>
                    </div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">受注件数</p>
                    <h3 id="kpi-count" class="text-xl font-extrabold text-slate-800 tracking-tight">-</h3>
                </div>

                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <i data-lucide="users" class="w-16 h-16 text-orange-600"></i>
                    </div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">平均顧客評価</p>
                    <h3 id="kpi-rating" class="text-xl font-extrabold text-slate-800 tracking-tight">-</h3>
                </div>

                <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <i data-lucide="truck" class="w-16 h-16 text-rose-600"></i>
                    </div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">平均配送日数</p>
                    <h3 id="kpi-duration" class="text-xl font-extrabold text-slate-800 tracking-tight">-</h3>
                </div>
            </section>

            <!-- Charts Grid -->
            <section id="chartsGrid" class="dashboard-grid cols-1">
                <!-- Charts generated by JS -->
            </section>

            <!-- AI Insight Section -->
            <section id="aiSection" class="bg-white rounded-xl border border-blue-100 shadow-sm overflow-hidden relative">
                <div class="bg-blue-50/50 px-5 py-3 border-b border-blue-100 flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="bg-blue-600 text-white p-1 rounded shadow-sm">
                            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                        </div>
                        <h2 class="text-sm font-bold text-blue-900">AI 戦略分析レポート</h2>
                    </div>
                    <div id="aiStatusBadge" class="flex items-center gap-2 px-2 py-0.5 bg-white rounded-full border border-blue-100 shadow-sm text-[10px] font-bold text-blue-600">
                        <span class="relative flex h-1.5 w-1.5">
                          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                          <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500"></span>
                        </span>
                        Thinking...
                    </div>
                </div>
                <div class="p-6 min-h-[150px]">
                    <div id="aiContent" class="prose-ai">
                        <!-- Content injected by JS -->
                        <div class="flex flex-col items-center justify-center h-24 text-slate-400 gap-2">
                            <i data-lucide="brain-circuit" class="w-8 h-8 opacity-20"></i>
                            <p class="text-xs font-medium">データを分析中...</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Footer Analysis -->
            <section class="bg-slate-800 text-slate-300 rounded-xl p-6 text-center mt-8">
                <p class="text-xs opacity-80">
                    Generated by Majin Analytics
                </p>
            </section>
        </div>
    </main>

    <script>
        // --- 1. Configuration & State ---
        // APIキーは実行環境(Canvas)から自動的に提供されます。
        const apiKey = ""; 
        
        let rawData = [];
        let filteredData = [];
        let charts = {};
        let currentLayout = 1;
        // Global reference to definitions for JSON export
        let globalChartDefinitions = [];

        // Chart.js Default Settings
        Chart.defaults.font.family = "'Inter', 'Noto Sans JP', sans-serif";
        Chart.defaults.color = '#64748b';
        Chart.defaults.scale.grid.color = '#f1f5f9';
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 6;
        Chart.defaults.plugins.tooltip.titleFont = { size: 11 };
        Chart.defaults.plugins.tooltip.bodyFont = { size: 11 };
        
        const COLORS = [
            '#2563eb', '#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', 
            '#84cc16', '#eab308', '#f97316', '#ef4444', '#f43f5e', 
            '#d946ef', '#8b5cf6', '#6366f1', '#4f46e5', '#3b82f6',
            '#64748b', '#475569', '#334155', '#1e293b', '#0f172a'
        ];

        // --- 2. Utility Functions ---
        const cleanNum = (val) => {
            if (val === null || val === undefined) return 0;
            const s = String(val).replace(/[^-0-9.]/g, ''); 
            const n = parseFloat(s);
            return isNaN(n) ? 0 : n;
        };

        // Short number formatter (万, 億)
        const formatShortNumber = (val) => {
            if (val === null || val === undefined) return '';
            if (typeof val !== 'number') return val;
            
            const abs = Math.abs(val);
            if (abs >= 100000000) return (val / 100000000).toFixed(1) + '億';
            if (abs >= 10000) return (val / 10000).toFixed(0) + '万';
            return val.toLocaleString();
        };

        const formatDate = (dateStr) => {
            if (!dateStr) return null;
            const d = new Date(dateStr);
            return isNaN(d.getTime()) ? null : d;
        };

        // Aggressive aggregation for top items
        // includeOthersフラグを追加し、ランキング系ではfalseにできるように変更
        const aggregateData = (data, key, measure, op = 'sum', limit = 10, includeOthers = true) => {
            const map = {};
            data.forEach(d => {
                const k = d[key] || '不明・未入力';
                const v = d[measure] || 0;
                if (!map[k]) map[k] = [];
                map[k].push(v);
            });

            let entries = Object.entries(map).map(([k, vals]) => {
                let val = 0;
                if (op === 'sum') val = vals.reduce((a, b) => a + b, 0);
                if (op === 'count') val = vals.length;
                if (op === 'avg') val = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
                return { key: k, val };
            });

            // Sort desc
            entries.sort((a, b) => b.val - a.val);

            if (entries.length > limit) {
                const top = entries.slice(0, limit);
                // includeOthers が true の場合のみ「その他」を追加
                if (includeOthers) {
                    const otherVal = entries.slice(limit).reduce((acc, cur) => acc + cur.val, 0);
                    if (op === 'avg') {
                        top.push({ key: 'その他', val: otherVal / (entries.length - limit) }); 
                    } else {
                        top.push({ key: 'その他', val: otherVal });
                    }
                }
                entries = top;
            }
            return {
                labels: entries.map(e => e.key),
                data: entries.map(e => e.val)
            };
        };

        // --- 3. Main Logic ---
        window.onload = () => {
            lucide.createIcons();
            // Bind both file inputs to the same handler
            document.getElementById('csvFileInputSplash').addEventListener('change', handleFile);
            document.getElementById('csvFileInputHeader').addEventListener('change', handleFile);
            
            document.getElementById('btnLayout1').addEventListener('click', () => toggleLayout(1));
            document.getElementById('btnLayout2').addEventListener('click', () => toggleLayout(2));
            document.getElementById('btnExportPdf').addEventListener('click', exportPDF);
            document.getElementById('btnExportJson').addEventListener('click', exportJSON);
            
            // Filter listeners
            ['filterStore', 'filterDateStart', 'filterDateEnd'].forEach(id => {
                document.getElementById(id).addEventListener('change', applyFilters);
            });
        };

        function toggleLayout(mode) {
            currentLayout = mode;
            const grid = document.getElementById('chartsGrid');
            const btn1 = document.getElementById('btnLayout1');
            const btn2 = document.getElementById('btnLayout2');
            
            if (mode === 1) {
                grid.classList.remove('cols-2');
                grid.classList.add('cols-1');
                btn1.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
                btn1.classList.remove('text-slate-400');
                btn2.classList.remove('bg-white', 'shadow-sm', 'text-blue-600');
                btn2.classList.add('text-slate-400');
            } else {
                grid.classList.remove('cols-1');
                grid.classList.add('cols-2');
                btn2.classList.add('bg-white', 'shadow-sm', 'text-blue-600');
                btn2.classList.remove('text-slate-400');
                btn1.classList.remove('bg-white', 'shadow-sm', 'text-blue-600');
                btn1.classList.add('text-slate-400');
            }
            // Trigger resize for charts
            Object.values(charts).forEach(c => c.resize());
        }

        function handleFile(e) {
            const file = e.target.files[0];
            if (!file) return;

            document.getElementById('loadingOverlay').classList.remove('hidden');

            Papa.parse(file, {
                header: true,
                skipEmptyLines: 'greedy', 
                encoding: 'Shift_JIS',
                complete: (results) => {
                    const keys = results.meta.fields || Object.keys(results.data[0] || {});
                    const hasKeywords = keys.some(k => 
                        k.includes('売上') || k.includes('受注') || k.includes('金額') || k.includes('Sales') || k.includes('取引')
                    );

                    if (!hasKeywords && keys.length > 0) {
                        console.log("Shift_JIS appears invalid. Retrying UTF-8.");
                        Papa.parse(file, {
                            header: true,
                            skipEmptyLines: 'greedy',
                            encoding: 'UTF-8',
                            complete: (resUTF) => processData(resUTF.data)
                        });
                    } else {
                        processData(results.data);
                    }
                },
                error: (err) => {
                    console.error("CSV Parse Error", err);
                    document.getElementById('loadingOverlay').classList.add('hidden');
                    alert("CSVファイルの読み込みに失敗しました。形式を確認してください。");
                }
            });
        }

        function processData(data) {
            rawData = data.map(row => {
                const getVal = (keys) => {
                    for (const k of keys) {
                        if (row[k] !== undefined) return row[k];
                    }
                    return null;
                };

                // Metric Mapping
                const sales = cleanNum(getVal(['売上総額', '売上', 'Sales', 'Amount', 'Total']));
                const profit = cleanNum(getVal(['粗利益', '利益', '粗利', 'Profit', 'Margin']));
                const quantity = cleanNum(getVal(['数量', 'Qty', 'Quantity']));
                const discount = cleanNum(getVal(['割引額', 'Discount']));
                const discountRate = cleanNum(getVal(['割引率', 'DiscountRate']));
                const rating = cleanNum(getVal(['顧客評価', 'Rating', 'Score']));
                const reviewLen = cleanNum(getVal(['レビュー文字数', 'ReviewLength']));
                
                // Date Mapping
                const orderDate = formatDate(getVal(['取引日', '売上日', '受注日', 'Date', 'OrderDate']));
                // Attempt to combine date and time if available for peak analysis
                const timeStr = getVal(['取引時間', 'Time']);
                let orderHour = null;
                if (timeStr) {
                    const parts = timeStr.split(':');
                    if (parts.length > 0) orderHour = parseInt(parts[0], 10);
                }

                // Dimension Mapping
                const store = (getVal(['店舗名', '店舗', 'Store', 'Branch']) || '未分類').trim();
                const region = (getVal(['地域', 'Region', 'Area']) || '不明').trim();
                const prefecture = (getVal(['都道府県', 'Prefecture', 'State']) || '不明').trim();
                const category = (getVal(['大カテゴリ', 'カテゴリ', 'Category', 'MajorCategory']) || 'その他').trim();
                const subCategory = (getVal(['中カテゴリ', 'サブカテゴリ', 'SubCategory', 'MinorCategory']) || 'その他').trim();
                const product = (getVal(['商品名', '商品', 'Product', 'Item']) || '不明').trim();
                const brand = (getVal(['ブランド名', 'ブランド', 'Brand']) || '不明').trim();
                const ageGroup = (getVal(['年代', '年齢層', 'AgeGroup']) || '不明').trim();
                const gender = (getVal(['性別', 'Gender']) || '不明').trim();
                const memberRank = (getVal(['会員ランク', 'ランク', 'MemberRank']) || '一般').trim();
                const payment = (getVal(['支払方法', '決済', 'Payment']) || '現金').trim();
                const channel = (getVal(['販売チャネル', 'Channel']) || '店舗').trim();
                const device = (getVal(['デバイス', 'Device']) || '不明').trim();
                const source = (getVal(['流入元', 'Source']) || '不明').trim();
                const shippingMethod = (getVal(['配送方法', 'Shipping']) || '標準').trim();
                const shippingStatus = (getVal(['配送状況', 'Status']) || '完了').trim();
                
                // Delivery Calculation
                let duration = 0;
                const shipDateStr = getVal(['配送予定日', '出荷日', 'ShipDate']);
                if (shipDateStr && orderDate) {
                    const shipDate = new Date(shipDateStr);
                    if (!isNaN(shipDate.getTime())) {
                        duration = Math.max(0, (shipDate - orderDate) / (1000 * 60 * 60 * 24));
                    }
                }

                return {
                    sales, profit, quantity, discount, discountRate, rating, reviewLen,
                    orderDate, orderHour, duration,
                    store, region, prefecture, category, subCategory, product, brand,
                    ageGroup, gender, memberRank, payment, channel, device, source,
                    shippingMethod, shippingStatus
                };
            }).filter(d => d.sales > 0 || d.quantity > 0);

            initFilters();
            
            // Switch UI from Splash to Dashboard
            document.getElementById('initialSplash').classList.add('hidden');
            document.getElementById('appHeader').classList.remove('hidden');
            document.getElementById('dashboardContent').classList.remove('hidden');
            
            document.getElementById('filterContainer1').classList.remove('opacity-50', 'pointer-events-none');
            document.getElementById('filterContainer2').classList.remove('opacity-50', 'pointer-events-none');
            document.getElementById('btnExportPdf').classList.remove('hidden');
            document.getElementById('btnExportJson').classList.remove('hidden');
            
            applyFilters();
        }

        function initFilters() {
            const stores = [...new Set(rawData.map(d => d.store))].sort();
            const sel = document.getElementById('filterStore');
            sel.innerHTML = '<option value="all">全店舗</option>';
            stores.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                sel.appendChild(opt);
            });
        }

        function applyFilters() {
            const store = document.getElementById('filterStore').value;
            const startStr = document.getElementById('filterDateStart').value;
            const endStr = document.getElementById('filterDateEnd').value;
            
            const start = startStr ? new Date(startStr + "-01") : null;
            const end = endStr ? new Date(endStr + "-31") : null;

            filteredData = rawData.filter(d => {
                if (store !== 'all' && d.store !== store) return false;
                if (!d.orderDate) return false;
                if (start && d.orderDate < start) return false;
                if (end && d.orderDate > end) return false;
                return true;
            });

            updateKPIs();
            renderCharts();
            generateAIInsight();
        }

        function updateKPIs() {
            const totalSales = filteredData.reduce((a, b) => a + b.sales, 0);
            const totalProfit = filteredData.reduce((a, b) => a + b.profit, 0);
            const count = filteredData.length || 1;
            const margin = totalSales > 0 ? (totalProfit / totalSales) * 100 : 0;
            
            // Average Rating
            const ratings = filteredData.map(d => d.rating).filter(r => r > 0);
            const avgRating = ratings.length ? ratings.reduce((a,b)=>a+b,0)/ratings.length : 0;
            
            // Average Duration
            const durations = filteredData.map(d => d.duration).filter(d => d > 0);
            const avgDur = durations.length ? durations.reduce((a,b)=>a+b,0)/durations.length : 0;

            document.getElementById('kpi-sales').textContent = formatShortNumber(totalSales);
            document.getElementById('kpi-margin').textContent = margin.toFixed(1) + '%';
            document.getElementById('kpi-count').textContent = formatShortNumber(count) + '件';
            document.getElementById('kpi-rating').textContent = avgRating.toFixed(2);
            document.getElementById('kpi-duration').textContent = avgDur.toFixed(1) + '日';
        }

        function renderCharts() {
            const container = document.getElementById('chartsGrid');
            container.innerHTML = '';
            charts = {};

            // Apply Short formatting to all LINEAR scales
            Chart.defaults.scales.linear.ticks.callback = function(value) {
                return formatShortNumber(value);
            };

            globalChartDefinitions = [
                // 1. 店舗別 売上ランキング
                {
                    id: 'c1', title: '店舗別 売上ランキング TOP10', type: 'bar',
                    getData: () => {
                        // ランキングなので「その他」を除外 (includeOthers = false)
                        const d = aggregateData(filteredData, 'store', 'sales', 'sum', 10, false);
                        return { labels: d.labels, datasets: [{ label: '売上', data: d.data, backgroundColor: COLORS[0] }] };
                    },
                    options: { indexAxis: 'y' }
                },
                // 2. 月別 売上・粗利推移
                {
                    id: 'c2', title: '月別 売上・粗利推移トレンド', type: 'bar',
                    getData: () => {
                        const m = {};
                        filteredData.forEach(d => {
                            const k = d.orderDate.toISOString().slice(0, 7);
                            if (!m[k]) m[k] = { sales: 0, profit: 0 };
                            m[k].sales += d.sales;
                            m[k].profit += d.profit;
                        });
                        const keys = Object.keys(m).sort();
                        return {
                            labels: keys,
                            datasets: [
                                { type: 'line', label: '粗利益', data: keys.map(k=>m[k].profit), borderColor: COLORS[7], yAxisID: 'y1' },
                                { type: 'bar', label: '売上金額', data: keys.map(k=>m[k].sales), backgroundColor: COLORS[0], yAxisID: 'y' }
                            ]
                        };
                    },
                    options: { scales: { y: { position: 'left' }, y1: { position: 'right', grid: { drawOnChartArea: false } } } }
                },
                // 3. 大カテゴリ別 売上構成比
                {
                    id: 'c3', title: '大カテゴリ別 売上構成比', type: 'doughnut',
                    getData: () => {
                        const d = aggregateData(filteredData, 'category', 'sales', 'sum');
                        return { labels: d.labels, datasets: [{ data: d.data, backgroundColor: COLORS }] };
                    }
                },
                // 4. 中カテゴリ別 利益率比較
                {
                    id: 'c4', title: '中カテゴリ別 利益率比較', type: 'bar',
                    getData: () => {
                        const m = {};
                        filteredData.forEach(d => {
                            if (!m[d.subCategory]) m[d.subCategory] = { s:0, p:0 };
                            m[d.subCategory].s += d.sales;
                            m[d.subCategory].p += d.profit;
                        });
                        const res = Object.keys(m).map(k => ({ k, v: m[k].s ? (m[k].p/m[k].s)*100 : 0 }))
                            .sort((a,b)=>b.v-a.v).slice(0,10);
                        return { labels: res.map(r=>r.k), datasets: [{ label: '利益率(%)', data: res.map(r=>r.v), backgroundColor: COLORS[3] }] };
                    }
                },
                // 5. 地域エリア別 売上シェア
                {
                    id: 'c5', title: '地域エリア別 売上シェア', type: 'pie',
                    getData: () => {
                        // シェア分析なので「その他」を含める (デフォルト)
                        const d = aggregateData(filteredData, 'region', 'sales', 'sum');
                        return { labels: d.labels, datasets: [{ data: d.data, backgroundColor: COLORS }] };
                    }
                },
                // 6. 商品別 販売数量ランキング
                {
                    id: 'c6', title: '商品別 販売数量ランキング TOP10', type: 'bar',
                    getData: () => {
                        // 修正箇所：ランキングなので「その他」を除外して純粋なTOP10を表示
                        const d = aggregateData(filteredData, 'product', 'quantity', 'sum', 10, false);
                        return { labels: d.labels, datasets: [{ label: '数量', data: d.data, backgroundColor: COLORS[4] }] };
                    },
                    options: { indexAxis: 'y' }
                },
                // 7. 年代別・性別 購入額分布
                {
                    id: 'c7', title: '年代別・性別 売上分布', type: 'bar',
                    getData: () => {
                        const bins = {}; 
                        filteredData.forEach(d => {
                            if (!bins[d.ageGroup]) bins[d.ageGroup] = { m:0, f:0, u:0 };
                            //英語の Male/Female の場合には順序を逆にしないと正しくグラフ化できないので注意
                            if (d.gender.includes('男')) bins[d.ageGroup].m += d.sales;
                            else if (d.gender.includes('女')) bins[d.ageGroup].f += d.sales;
                            else bins[d.ageGroup].u += d.sales;
                        });
                        const labels = Object.keys(bins).sort();
                        return {
                            labels,
                            datasets: [
                                { label: '男性', data: labels.map(l=>bins[l].m), backgroundColor: '#3b82f6' },
                                { label: '女性', data: labels.map(l=>bins[l].f), backgroundColor: '#ec4899' }
                            ]
                        };
                    },
                    options: { scales: { x: { stacked: true }, y: { stacked: true } } }
                },
                // 8. 会員ランク別 売上貢献度
                {
                    id: 'c8', title: '会員ランク別 売上貢献度', type: 'pie',
                    getData: () => {
                        const d = aggregateData(filteredData, 'memberRank', 'sales', 'sum');
                        return { labels: d.labels, datasets: [{ data: d.data, backgroundColor: COLORS }] };
                    }
                },
                // 9. 曜日別 平均来店/購入トレンド
                {
                    id: 'c9', title: '曜日別 平均来店(件数)トレンド', type: 'line',
                    getData: () => {
                        const days = ['日', '月', '火', '水', '木', '金', '土'];
                        const m = Array(7).fill(0);
                        filteredData.forEach(d => {
                            m[d.orderDate.getDay()] += 1;
                        });
                        return { labels: days, datasets: [{ label: '件数', data: m, borderColor: COLORS[5], tension: 0.3, fill: true, backgroundColor: COLORS[5]+'20' }] };
                    }
                },
                // 10. 時間帯別 売上ピーク分析
                {
                    id: 'c10', title: '時間帯別 売上ピーク分析', type: 'line',
                    getData: () => {
                        const hours = Array(24).fill(0);
                        filteredData.forEach(d => {
                            if (d.orderHour !== null) hours[d.orderHour] += d.sales;
                        });
                        return { 
                            labels: hours.map((_, i) => i + ':00'), 
                            datasets: [{ label: '売上', data: hours, borderColor: COLORS[6], pointRadius: 2 }] 
                        };
                    }
                },
                // 11. 支払方法 利用比率
                {
                    id: 'c11', title: '支払方法 利用比率', type: 'doughnut',
                    getData: () => {
                        const d = aggregateData(filteredData, 'payment', 'sales', 'count');
                        return { labels: d.labels, datasets: [{ data: d.data, backgroundColor: COLORS }] };
                    }
                },
                // 12. 販売チャネル別 収益性比較
                {
                    id: 'c12', title: '販売チャネル別 収益性(粗利)比較', type: 'bar',
                    getData: () => {
                        const d = aggregateData(filteredData, 'channel', 'profit', 'sum');
                        return { labels: d.labels, datasets: [{ label: '粗利益', data: d.data, backgroundColor: COLORS[7] }] };
                    }
                },
                // 13. ブランド別 平均顧客評価スコア
                {
                    id: 'c13', title: 'ブランド別 平均顧客評価スコア', type: 'bar',
                    getData: () => {
                        // 修正: 評価が0（未評価）のデータを除外し、有効な評価のみで平均を算出
                        const validData = filteredData.filter(d => d.rating > 0);
                        // ランキング形式でTOP10を表示 (その他は除外)
                        const d = aggregateData(validData, 'brand', 'rating', 'avg', 10, false);
                        return { labels: d.labels, datasets: [{ label: '平均評価(1-5)', data: d.data, backgroundColor: COLORS[8] }] };
                    },
                    // Y軸の範囲固定(min:3)を削除し、データに合わせて自動調整させる
                    options: {} 
                },
                // 14. 配送方法別 平均配送日数
                {
                    id: 'c14', title: '配送方法別 平均配送日数', type: 'bar',
                    getData: () => {
                        const d = aggregateData(filteredData, 'shippingMethod', 'duration', 'avg');
                        return { labels: d.labels, datasets: [{ label: '平均日数', data: d.data, backgroundColor: COLORS[9] }] };
                    }
                },
                // 15. デバイス別 利用シェア
                {
                    id: 'c15', title: 'デバイス・OS別 利用シェア', type: 'pie',
                    getData: () => {
                        const d = aggregateData(filteredData, 'device', 'sales', 'count');
                        return { labels: d.labels, datasets: [{ data: d.data, backgroundColor: COLORS }] };
                    }
                },
                // 16. 流入元別 売上獲得効率
                {
                    id: 'c16', title: '流入元別 売上獲得効率', type: 'bar',
                    getData: () => {
                        const d = aggregateData(filteredData, 'source', 'sales', 'sum', 8);
                        return { labels: d.labels, datasets: [{ label: '売上', data: d.data, backgroundColor: COLORS[10] }] };
                    }
                },
                // 17. 都道府県別 売上上位
                {
                    id: 'c17', title: '都道府県別 売上 TOP10', type: 'bar',
                    getData: () => {
                        // ランキングなので「その他」を除外
                        const d = aggregateData(filteredData, 'prefecture', 'sales', 'sum', 10, false);
                        return { labels: d.labels, datasets: [{ label: '売上', data: d.data, backgroundColor: COLORS[11] }] };
                    }
                },
                // 18. 割引率と利益率の相関分析
                {
                    id: 'c18', title: '割引率 vs 利益率の相関分析', type: 'scatter',
                    getData: () => {
                        return {
                            datasets: [{
                                label: '取引',
                                data: filteredData.slice(0, 300).map(d => ({ x: d.discountRate, y: d.sales > 0 ? (d.profit/d.sales)*100 : 0 })),
                                backgroundColor: COLORS[12]
                            }]
                        };
                    },
                    options: { scales: { x: { title: { display: true, text: '割引率' } }, y: { title: { display: true, text: '利益率(%)' } } } }
                },
                // 19. 顧客評価とレビュー文字数の関係
                {
                    id: 'c19', title: '顧客評価 vs レビュー文字数', type: 'scatter',
                    getData: () => {
                        return {
                            datasets: [{
                                label: 'レビュー',
                                data: filteredData.slice(0, 300).filter(d => d.reviewLen > 0).map(d => ({ x: d.rating, y: d.reviewLen })),
                                backgroundColor: COLORS[13]
                            }]
                        };
                    },
                    options: { scales: { x: { title: { display: true, text: '評価スコア' } }, y: { title: { display: true, text: '文字数' } } } }
                },
                // 20. 配送遅延発生件数 (月別)
                {
                    id: 'c20', title: '配送遅延発生件数 (月別)', type: 'bar',
                    getData: () => {
                        const m = {};
                        filteredData.forEach(d => {
                            if (d.duration < 3) return; // 3日以上を遅延気味と定義
                            const k = d.orderDate.toISOString().slice(0, 7);
                            m[k] = (m[k] || 0) + 1;
                        });
                        const keys = Object.keys(m).sort();
                        return { labels: keys, datasets: [{ label: '配送3日以上件数', data: keys.map(k=>m[k]), backgroundColor: COLORS[14] }] };
                    }
                }
            ];

            globalChartDefinitions.forEach(def => {
                try {
                    const div = document.createElement('div');
                    div.className = 'chart-card';
                    div.innerHTML = `
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="text-sm font-bold text-slate-700 flex items-center gap-2">
                                <span class="w-1 h-4 bg-blue-500 rounded-full"></span>
                                ${def.title}
                            </h4>
                        </div>
                        <div class="chart-container">
                            <canvas id="${def.id}"></canvas>
                        </div>
                    `;
                    container.appendChild(div);

                    const ctx = document.getElementById(def.id).getContext('2d');
                    const data = def.getData();
                    
                    charts[def.id] = new Chart(ctx, {
                        type: def.type,
                        data: data,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { 
                                    display: def.type === 'pie' || def.type === 'doughnut' || def.title.includes('推移') || def.title.includes('分布'),
                                    position: (def.type === 'pie' || def.type === 'doughnut') ? 'right' : 'bottom',
                                    labels: { boxWidth: 10, font: { size: 10 } }
                                },
                                datalabels: {
                                    display: (ctx) => {
                                        return ctx.dataset.data.length < 20 && ctx.chart.width > 200 && def.type !== 'scatter'; 
                                    },
                                    color: '#fff',
                                    font: { weight: 'bold', size: 9 },
                                    formatter: (value) => {
                                        if (value === null || value === undefined) return '';
                                        if (def.type === 'scatter') return '';
                                        return formatShortNumber(value);
                                    },
                                    textShadowColor: 'rgba(0,0,0,0.5)',
                                    textShadowBlur: 2
                                }
                            },
                            scales: (def.type === 'pie' || def.type === 'doughnut' || def.type === 'radar') ? {} : (def.options?.scales || {}),
                            ...def.options
                        }
                    });
                } catch (e) {
                    console.error(`Error rendering chart ${def.title}:`, e);
                }
            });
            document.getElementById('loadingOverlay').classList.add('hidden');
        }

        async function generateAIInsight() {
            const contentDiv = document.getElementById('aiContent');
            const statusBadge = document.getElementById('aiStatusBadge');

            if (filteredData.length === 0) return;
            
            statusBadge.classList.remove('hidden');
            statusBadge.innerHTML = '<span class="animate-ping inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75 mr-2"></span>Thinking...';
            contentDiv.innerHTML = '<div class="space-y-3 animate-pulse"><div class="h-4 bg-slate-100 rounded w-3/4"></div><div class="h-4 bg-slate-100 rounded w-full"></div><div class="h-4 bg-slate-100 rounded w-5/6"></div></div>';

            // Gather rich data for AI
            const kpi = {
                sales: document.getElementById('kpi-sales').textContent,
                count: document.getElementById('kpi-count').textContent,
                margin: document.getElementById('kpi-margin').textContent,
                branch: document.getElementById('filterStore').value
            };

            const getTop3 = (key) => aggregateData(filteredData, key, 'sales', 'sum', 3).labels.join(', ');
            const topStores = getTop3('store');
            const topCategories = getTop3('category');
            const topProducts = getTop3('product');
            const topRegions = getTop3('region');

            const prompt = `
            あなたは小売・流通業界のプロフェッショナルな経営コンサルタントです。
            以下の集計データを深く分析し、経営層および現場マネージャー向けの「戦略インサイトレポート」を作成してください。

            ## 分析対象データ要約
            - フィルタ対象: ${kpi.branch}
            - 総売上: ${kpi.sales}
            - 受注件数: ${kpi.count}
            - 平均粗利率: ${kpi.margin}
            - 売上上位店舗: ${topStores}
            - 主力カテゴリ: ${topCategories}
            - 人気商品: ${topProducts}
            - 主要地域: ${topRegions}

            ## レポート要件 (Markdown形式)
            1. **データの傾向分析** (全体の約7割)
               - 売上や利益率の現状トレンド分析
               - 上位店舗や商品の特徴、顧客属性（年齢層や区分など）の傾向
               - チャネル別やリードタイムに関するデータ読み取り

            2. **戦略インサイト・提言** (全体の約3割)
               - 上記分析に基づき、次期に向けて打つべき具体的な施策を3点
               - 現場が即座に行動できる具体的なアクションプラン

            **重要: セクションの見出しには、「70%」や「30%」といった割合の数値を絶対に含めないでください。**
            **重要: 太字にする際は、Markdownの ** (アスタリスク2つ) を使用し、HTMLタグやエスケープ文字は使用しないでください。強調したい言葉の前後には必ず半角スペースを入れてください（例: 「 **強調** 」）。**
            ※文体は「です・ます」調で、数値に基づいた論理的かつ前向きなトーンで書いてください。
            `;

            try {
                // Modified fetchWithRetry to handle content validation and JSON parsing errors
                const fetchAndValidate = async (url, options, retries = 3) => {
                    for (let i = 0; i < retries; i++) {
                        try {
                            const res = await fetch(url, options);
                            if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
                            
                            const data = await res.json();
                            // Check if candidate exists and has text content
                            if (!data.candidates || !data.candidates[0]?.content?.parts?.[0]?.text) {
                                throw new Error("Invalid API Response: No text content found");
                            }
                            return data; // Return valid data
                        } catch (err) {
                            console.warn(`Attempt ${i + 1} failed: ${err.message}`);
                            if (i === retries - 1) throw err;
                            await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i))); // Exponential backoff
                        }
                    }
                };

                const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
                
                // Use the new robust fetch function
                const data = await fetchAndValidate(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
                });

                const mdText = data.candidates?.[0]?.content?.parts?.[0]?.text || "分析結果を取得できませんでした。";
                
                // Parse markdown
                let htmlContent = marked.parse(mdText);
                htmlContent = htmlContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
                contentDiv.innerHTML = htmlContent;
                
                statusBadge.innerHTML = '<i data-lucide="check" class="w-3 h-3 mr-1"></i>Completed';
                statusBadge.classList.remove('text-blue-600', 'bg-white');
                statusBadge.classList.add('text-green-600', 'bg-green-50');
                lucide.createIcons();

            } catch (error) {
                console.error("AI Error:", error);
                contentDiv.innerHTML = `
                    <div class="text-center py-8 text-red-500 bg-red-50 rounded-lg">
                        <p class="font-bold">AI分析エラー</p>
                        <p class="text-xs mt-1">ネットワーク接続を確認するか、しばらく待ってから再試行してください。</p>
                        <p class="text-xs text-slate-400 mt-2">${error.message}</p>
                    </div>
                `;
                statusBadge.classList.add('hidden');
            }
        }

        // Updated PDF Export with Optimized Layout (Page 1: 2 charts, Page 2+: 3 charts) and JPEG Compression
        async function exportPDF() {
            document.getElementById('loadingOverlay').classList.remove('hidden');
            document.getElementById('loadingText').textContent = 'PDFレポート作成中...';

            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pageWidth = 210;
            const pageHeight = 297;
            const margin = 10;
            let currentY = margin;

            // Image Format & Quality for Compression (JPEG with 0.75 quality)
            const imgFormat = 'JPEG';
            const quality = 0.75;

            // --- Pre-process for PDF ---
            // 1. Hide AI Status Badge
            const aiBadge = document.getElementById('aiStatusBadge');
            if (aiBadge) aiBadge.classList.add('hidden');

            // 2. Remove Marker Style specifically for PDF export
            // We inject a temporary style tag to override background
            const styleTag = document.createElement('style');
            styleTag.innerHTML = `.prose-ai strong, .prose-ai b { background: none !important; }`;
            document.head.appendChild(styleTag);

            try {
                // --- Page 1 ---
                // 1. Header Title
                pdf.setFontSize(16);
                pdf.text(`Majin Analytics Report - ${new Date().toLocaleDateString()}`, margin, currentY + 5);
                currentY += 18;

                // 2. KPI Section
                const kpiSection = document.getElementById('kpiSection');
                if (kpiSection) {
                    const canvas = await html2canvas(kpiSection, { scale: 2, useCORS: true });
                    const imgWidth = pageWidth - (margin * 2);
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;
                    pdf.addImage(canvas.toDataURL('image/jpeg', quality), imgFormat, margin, currentY, imgWidth, imgHeight);
                    currentY += imgHeight + 10;
                }

                // 3. Charts (Page 1: First 2 charts)
                const chartCards = document.querySelectorAll('.chart-card');
                const chartsArray = Array.from(chartCards);
                
                const page1ChartLimit = 2;
                const pageNextChartLimit = 3;

                // Calculate height for 2 charts on Page 1 to fit nicely
                const availableH_p1 = pageHeight - currentY - margin;
                const heightPerChart_p1 = (availableH_p1 - 10) / 2; // -10 for gap
                const chartH_p1 = Math.min(heightPerChart_p1, 90);

                let chartIndex = 0;

                // Render Page 1 Charts
                for (let i = 0; i < page1ChartLimit && chartIndex < chartsArray.length; i++) {
                    const card = chartsArray[chartIndex];
                    const canvas = await html2canvas(card, { scale: 2, useCORS: true });
                    const imgWidth = pageWidth - (margin * 2);
                    let imgHeight = (canvas.height * imgWidth) / canvas.width;
                    
                    if (imgHeight > chartH_p1) {
                         imgHeight = chartH_p1;
                    }

                    pdf.addImage(canvas.toDataURL('image/jpeg', quality), imgFormat, margin, currentY, imgWidth, imgHeight);
                    currentY += imgHeight + 5;
                    chartIndex++;
                }

                // --- Page 2+ (3 Charts per page) ---
                while (chartIndex < chartsArray.length) {
                    pdf.addPage();
                    currentY = margin;
                    
                    // Logic for 3 charts per page with BOTTOM BUFFER (Modified from 20 to 10 as requested)
                    // Available height: 297 - 10 (top) - 10 (bottom buffer) = 277mm
                    const bottomBuffer = 10;
                    const availableH_p2 = pageHeight - (margin * 2) - bottomBuffer;
                    
                    // Height per chart: 277 / 3 = ~92mm.
                    const maxChartH_p2 = availableH_p2 / pageNextChartLimit; 
                    
                    const chartsOnThisPage = Math.min(pageNextChartLimit, chartsArray.length - chartIndex);
                    
                    for (let i = 0; i < chartsOnThisPage; i++) {
                        const card = chartsArray[chartIndex];
                        const canvas = await html2canvas(card, { scale: 2, useCORS: true });
                        const imgWidth = pageWidth - (margin * 2);
                        let imgHeight = (canvas.height * imgWidth) / canvas.width;
                        
                        // Enforce max height to respect bottom margin
                        if (imgHeight > maxChartH_p2) {
                            imgHeight = maxChartH_p2; 
                        }
                        
                        // Check if we accidentally overflow (just in case)
                        if (currentY + imgHeight > pageHeight - bottomBuffer) {
                             // This shouldn't happen with the math above, but as a safeguard:
                             // If it's the very first chart on page, print it anyway (clipped), else break page?
                             // With fixed math, we trust it fits.
                        }

                        pdf.addImage(canvas.toDataURL('image/jpeg', quality), imgFormat, margin, currentY, imgWidth, imgHeight);
                        currentY += imgHeight + 5;
                        chartIndex++;
                    }
                }

                // 4. AI Insight Section (Smart Slicing Logic)
                const aiSection = document.getElementById('aiSection');
                if (aiSection) {
                    pdf.addPage(); 
                    currentY = margin;

                    const canvas = await html2canvas(aiSection, { 
                        scale: 2, 
                        useCORS: true,
                        backgroundColor: '#ffffff' 
                    });
                    
                    const imgWidth = pageWidth - (margin * 2);
                    // Use context to analyze pixels for smart cut
                    const ctx = canvas.getContext('2d');
                    
                    let srcY_px = 0; 
                    let remainingH_px = canvas.height;

                    // Helper to detect safe split point in pixels (scan upward for whitespace)
                    const findSafeSplitY = (ctx, width, startY, searchRange = 80) => {
                        const imgData = ctx.getImageData(0, startY - searchRange, width, searchRange);
                        const data = imgData.data;
                        // Scan from bottom (startY) upwards
                        for (let row = searchRange - 1; row >= 0; row--) {
                            let hasText = false;
                            for (let col = 0; col < width; col+=5) { // Skip pixels for speed
                                const idx = (row * width + col) * 4;
                                const r = data[idx];
                                const g = data[idx+1];
                                const b = data[idx+2];
                                // Text is dark (e.g. < 200). Background is white (255)
                                if (r < 230 && g < 230 && b < 230) {
                                    hasText = true;
                                    break;
                                }
                            }
                            if (!hasText) {
                                // Found a safe row (mostly white)
                                return startY - (searchRange - row);
                            }
                        }
                        return startY; // No safe split found
                    };

                    while (remainingH_px > 0) {
                         // Available height on PDF page in mm
                         const pdfAvailableH_mm = (srcY_px === 0) ? (pageHeight - margin * 2) : (pageHeight - margin * 2);
                         // Convert available mm to pixels
                         const maxPageH_px = (pdfAvailableH_mm / imgWidth) * canvas.width;

                         let splitH_px = Math.min(remainingH_px, maxPageH_px);

                         // If we need to split (not the last chunk), try to find a safe line
                         if (splitH_px < remainingH_px) {
                             // Try to find a whitespace gap in the bottom 100px of the slice
                             const safeSplitY = findSafeSplitY(ctx, canvas.width, srcY_px + splitH_px, 100); 
                             splitH_px = safeSplitY - srcY_px;
                         }

                         // Draw this slice to a temp canvas
                         const sliceCanvas = document.createElement('canvas');
                         sliceCanvas.width = canvas.width;
                         sliceCanvas.height = splitH_px;
                         const sCtx = sliceCanvas.getContext('2d');
                         
                         sCtx.drawImage(canvas, 0, srcY_px, canvas.width, splitH_px, 0, 0, sliceCanvas.width, splitH_px);
                         
                         // Convert pixels back to mm for PDF sizing
                         const sliceH_mm = (splitH_px / canvas.width) * imgWidth;

                         pdf.addImage(sliceCanvas.toDataURL('image/jpeg', quality), imgFormat, margin, currentY, imgWidth, sliceH_mm);
                         
                         srcY_px += splitH_px;
                         remainingH_px -= splitH_px;
                         
                         if (remainingH_px > 0) {
                             pdf.addPage();
                             currentY = margin;
                         }
                    }
                }

                pdf.save(`Majin_Analytics_Report_${Date.now()}.pdf`);

            } catch (e) {
                console.error(e);
                alert('PDF生成に失敗しました: ' + e.message);
            } finally {
                // Cleanup: Show badge again, remove style override
                if (aiBadge) aiBadge.classList.remove('hidden');
                if (styleTag.parentNode) styleTag.parentNode.removeChild(styleTag);
                
                document.getElementById('loadingOverlay').classList.add('hidden');
            }
        }

        function exportJSON() {
            try {
                // 1. Collect Metadata
                const exportData = {
                    metadata: {
                        exportedAt: new Date().toISOString(),
                        filterCondition: {
                            store: document.getElementById('filterStore').value,
                            dateStart: document.getElementById('filterDateStart').value || null,
                            dateEnd: document.getElementById('filterDateEnd').value || null
                        }
                    },
                    kpi: {
                        sales: document.getElementById('kpi-sales').textContent,
                        margin: document.getElementById('kpi-margin').textContent,
                        count: document.getElementById('kpi-count').textContent,
                        rating: document.getElementById('kpi-rating').textContent,
                        duration: document.getElementById('kpi-duration').textContent
                    },
                    charts: []
                };

                // 2. Collect Chart Data
                // We use globalChartDefinitions which contains the logic to regenerate data for current filter
                globalChartDefinitions.forEach(def => {
                    exportData.charts.push({
                        id: def.id,
                        title: def.title,
                        type: def.type,
                        data: def.getData() // Get currently filtered data
                    });
                });

                // 3. Create Blob and Download
                const dataStr = JSON.stringify(exportData, null, 2);
                const blob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const link = document.createElement('a');
                link.href = url;
                link.download = `Majin_Analytics_Data_${Date.now()}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);

            } catch (e) {
                console.error(e);
                alert('JSON出力に失敗しました: ' + e.message);
            }
        }
    </script>
</body>
</html>