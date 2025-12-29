import React, { useState, useEffect } from 'react';
import SplashScreen from './components/SplashScreen';
import ChartCard from './components/ChartCard';
import { Loader2, Download, FileJson, LayoutGrid, List, RefreshCw, FileCode, Banknote, ShoppingCart, Users, TrendingUp, Truck } from 'lucide-react';
import axios from 'axios';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import { marked } from 'marked';

const API_BASE_URL = 'https://zog416mima.execute-api.ap-northeast-1.amazonaws.com'; 

// markedの設定
marked.setOptions({
  breaks: true,
  gfm: true
});
const App = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [layoutMode, setLayoutMode] = useState(1);

  const formatShortNumber = (val) => {
    if (val == null) return '';
    const abs = Math.abs(val);
    if (abs >= 100000000) return (val / 100000000).toFixed(1) + '億';
    if (abs >= 10000) return (val / 10000).toFixed(0) + '万';
    return val.toLocaleString();
  };

  const startAnalysis = async (file) => {
    setIsLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analyze`);
      const { jobId, uploadUrl } = data;
      setJobId(jobId);

      await axios.put(uploadUrl, file, {
        headers: { 'Content-Type': 'text/csv' }
      });

      setIsLoaded(true);
      startPolling(jobId);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('アップロードに失敗しました。');
      setIsLoading(false);
    }
  };

  const startPolling = (id) => {
    const interval = setInterval(async () => {
      try {
        const { data } = await axios.get(`${API_BASE_URL}/jobs/${id}`);
        setJobStatus(data.status);
        
        if (data.status === 'COMPLETED') {
          clearInterval(interval);
          fetchResult(data.resultUrl);
        } else if (data.status === 'FAILED') {
          clearInterval(interval);
          alert('分析に失敗しました: ' + data.error);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 3000);
  };

  const fetchResult = async (url) => {
    try {
      const { data } = await axios.get(url);
      setAnalysisResult(data);
      setIsLoading(false);
    } catch (error) {
      console.error('Fetch result failed:', error);
      setIsLoading(false);
    }
  };

  const exportPDF = async () => {
    const element = document.getElementById('dashboard-content');
    const canvas = await html2canvas(element, { 
      scale: 2,
      useCORS: true,
      logging: false
    });
    
    const imgData = canvas.toDataURL('image/jpeg', 0.8);
    const pdf = new jsPDF('p', 'mm', 'a4');
    
    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
    
    const pageHeight = pdf.internal.pageSize.getHeight();
    let heightLeft = pdfHeight;
    let position = 0;

    // 1ページ目
    pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, pdfHeight);
    heightLeft -= pageHeight;

    // 2ページ目以降
    while (heightLeft > 0) {
      position = heightLeft - pdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, pdfHeight);
      heightLeft -= pageHeight;
    }
    
    pdf.save(`Majin_Analysis_${jobId}.pdf`);
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(analysisResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Majin_Analysis_${jobId}.json`;
    a.click();
  };

  const exportHTML = () => {
    const metricsHtml = Object.entries(analysisResult.summary.metrics_summary).map(([key, val], idx) => `
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden">
        <p class="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">
          ${analysisResult.analysisPlan.column_mapping[key]?.label || key}
        </p>
        <p class="text-2xl font-black text-slate-800">¥${formatShortNumber(val)}</p>
      </div>
    `).join('');

    const chartsHtml = analysisResult.analysisPlan.chart_specs.map(config => `
      <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
        <h3 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <div class="w-1 h-4 bg-blue-600 rounded-full"></div>
          ${config.title}
        </h3>
        <div class="relative w-full h-[300px] mb-4">
          <canvas id="chart-${config.id}"></canvas>
        </div>
        ${analysisResult.micro_insights[config.id] ? `
          <div class="mt-auto bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs text-slate-600 leading-relaxed">
            ${marked.parse(analysisResult.micro_insights[config.id])}
          </div>
        ` : ''}
      </div>
    `).join('');

    const chartScripts = analysisResult.analysisPlan.chart_specs.map(config => {
      const data = analysisResult.charts[config.id];
      const labels = Object.keys(data);
      const values = Object.values(data);
      return `
        new Chart(document.getElementById('chart-${config.id}'), {
          type: '${config.type}',
          data: {
            labels: ${JSON.stringify(labels)},
            datasets: [{
              label: '${config.title}',
              data: ${JSON.stringify(values)},
              backgroundColor: ${config.type === 'pie' || config.type === 'doughnut' ? "['#2563eb', '#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#84cc16', '#eab308', '#f97316']" : "'#2563eb'"},
              borderColor: '#2563eb',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: ${config.type === 'pie' || config.type === 'doughnut'}, position: 'right' }
            },
            scales: ${config.type === 'pie' || config.type === 'doughnut' ? '{}' : `{
              y: { beginAtZero: true }
            }`}
          }
        });
      `;
    }).join('');

    const htmlContent = `
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>Majin Analysis Report - ${jobId}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Noto+Sans+JP:wght@400;700;900&display=swap');
    body { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #f8fafc; }
    .prose-ai { font-size: 1rem; line-height: 1.8; color: #334155; }
    .prose-ai h1 { font-size: 1.75rem; font-weight: 900; margin: 2rem 0 1.25rem; color: #1e3a8a; border-left: 6px solid #2563eb; padding-left: 1rem; }
    .prose-ai h2 { font-size: 1.4rem; font-weight: 800; margin: 1.5rem 0 1rem; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
    .prose-ai h3 { font-size: 1.2rem; font-weight: 800; margin: 1.25rem 0 0.75rem; color: #2563eb; display: flex; align-items: center; gap: 0.5rem; }
    .prose-ai h3::before { content: "■"; color: #60a5fa; }
    .prose-ai strong { color: #1e3a8a; font-weight: 800; background: linear-gradient(transparent 60%, #bfdbfe 60%); padding: 0 2px; }
    .prose-ai ul { list-style-type: disc; margin-left: 1.5rem; margin-bottom: 1.5rem; }
    .prose-ai li { margin-bottom: 0.5rem; }
  </style>
</head>
<body class="p-10">
  <div class="max-w-6xl mx-auto space-y-8">
    <div class="bg-white p-12 rounded-[2.5rem] shadow-2xl border border-slate-100">
      <div class="flex items-center justify-between mb-12 border-b-4 border-blue-600 pb-6">
        <h1 class="text-4xl font-black text-slate-800 tracking-tighter">MAJIN <span class="text-blue-600">STRATEGIC REPORT</span></h1>
        <div class="text-right text-sm text-slate-400 font-bold">
          ID: ${jobId}<br>
          DATE: ${new Date().toLocaleDateString()}
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <p class="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">データ件数</p>
          <p class="text-2xl font-black text-slate-800">${analysisResult.summary.total_rows.toLocaleString()}件</p>
        </div>
        ${metricsHtml}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        ${chartsHtml}
      </div>

      <div class="bg-blue-600 px-8 py-4 rounded-t-3xl flex items-center gap-3">
        <div class="w-2 h-2 bg-white rounded-full"></div>
        <h2 class="text-white font-black tracking-tight m-0">AI STRATEGIC INSIGHT REPORT</h2>
      </div>
      <div class="p-10 prose-ai border border-blue-100 rounded-b-3xl bg-white">
        ${marked.parse(analysisResult.ai_report)}
      </div>
      
      <div class="mt-16 pt-8 border-t border-slate-100 text-center">
        <p class="text-xs font-black text-slate-300 tracking-[0.2em] uppercase">Generated by Majin Analytics Platform</p>
      </div>
    </div>
  </div>
  <script>
    ${chartScripts}
  </script>
</body>
</html>`;
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Majin_Analysis_${jobId}.html`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <style>{`
        .prose-ai h1 { font-size: 1.6rem; font-weight: 900; margin: 2rem 0 1.25rem; color: #1e3a8a; border-left: 6px solid #2563eb; padding-left: 1rem; line-height: 1.2; }
        .prose-ai h2 { font-size: 1.35rem; font-weight: 800; margin: 1.75rem 0 1rem; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
        .prose-ai h3 { font-size: 1.15rem; font-weight: 800; margin: 1.25rem 0 0.75rem; color: #2563eb; display: flex; align-items: center; gap: 0.5rem; }
        .prose-ai h3::before { content: "■"; font-size: 0.9em; color: #60a5fa; }
        .prose-ai strong { color: #1e3a8a; font-weight: 800; background: linear-gradient(transparent 70%, #dbeafe 70%); padding: 0 2px; }
        .prose-ai u { text-decoration: none; border-bottom: 2px solid #3b82f6; }
        .prose-ai code { background-color: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.9em; color: #475569; }
        .prose-ai ul { list-style-type: disc; margin-left: 1.5rem; margin-bottom: 1.25rem; }
        .prose-ai li { margin-bottom: 0.5rem; color: #334155; }
        .prose-ai p { margin-bottom: 1rem; line-height: 1.8; color: #334155; }
        .prose-insight p { margin: 0; }
        .prose-insight strong { color: #1e3a8a; font-weight: 800; }
      `}</style>

      {!isLoaded && <SplashScreen onFileSelect={startAnalysis} />}
      
      {isLoading && (
        <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
          <p className="text-lg font-bold text-slate-700">
            {jobStatus === 'PROCESSING' ? 'AIがデータを分析中...' : 'システムを起動中...'}
          </p>
        </div>
      )}

      {isLoaded && (
        <>
          <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
            <div className="max-w-[1200px] mx-auto px-4 py-2 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h2 className="font-black text-blue-600 text-lg tracking-tighter">MAJIN</h2>
                <button onClick={() => window.location.reload()} className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors">
                  <RefreshCw size={14} /> 新規分析
                </button>
              </div>
              
              <div className="flex items-center gap-2">
                <button onClick={() => setLayoutMode(1)} className={`p-2 rounded-lg transition-colors ${layoutMode === 1 ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:bg-slate-100'}`}><List size={18} /></button>
                <button onClick={() => setLayoutMode(2)} className={`p-2 rounded-lg transition-colors ${layoutMode === 2 ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:bg-slate-100'}`}><LayoutGrid size={18} /></button>
                <div className="w-px h-6 bg-slate-200 mx-2"></div>
                <button onClick={exportPDF} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm"><Download size={14} /> PDF</button>
                <button onClick={exportJSON} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm"><FileJson size={14} /> JSON</button>
                <button onClick={exportHTML} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm"><FileCode size={14} /> HTML</button>
              </div>
            </div>
          </header>

          <main id="dashboard-content" className="max-w-[1200px] mx-auto p-6">
            {analysisResult ? (
              <div className="space-y-8">
                <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                      <ShoppingCart className="w-12 h-12 text-blue-600" />
                    </div>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">データ件数</p>
                    <p className="text-2xl font-black text-slate-800">{analysisResult.summary.total_rows.toLocaleString()}件</p>
                  </div>
                  {Object.entries(analysisResult.summary.metrics_summary).map(([key, val], idx) => (
                    <div key={key} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden group">
                      <div className="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Banknote className={`w-12 h-12 ${['text-emerald-600', 'text-indigo-600', 'text-orange-600', 'text-rose-600'][idx % 4]}`} />
                      </div>
                      <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">
                        {analysisResult.analysisPlan.column_mapping[key]?.label || key}
                      </p>
                      <p className="text-2xl font-black text-slate-800">¥{formatShortNumber(val)}</p>
                    </div>
                  ))}
                </section>

                <section className={`grid gap-6 ${layoutMode === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                  {analysisResult.analysisPlan.chart_specs.map(config => (
                    <ChartCard 
                      key={config.id}
                      title={config.title}
                      type={config.type}
                      data={analysisResult.charts[config.id]}
                      insight={analysisResult.micro_insights[config.id]}
                      layoutMode={layoutMode}
                    />
                  ))}
                </section>

                <section className="bg-white rounded-3xl border border-blue-100 shadow-xl overflow-hidden">
                  <div className="bg-blue-600 px-8 py-4 flex items-center gap-3">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                    <h2 className="text-white font-black tracking-tight">AI STRATEGIC INSIGHT REPORT</h2>
                  </div>
                  <div className="p-10 prose-ai max-w-none" dangerouslySetInnerHTML={{ __html: marked.parse(analysisResult.ai_report) }}>
                  </div>
                </section>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-40 text-slate-300">
                <Loader2 className="w-10 h-10 animate-spin mb-4 opacity-20" />
                <p className="font-bold tracking-widest text-sm">ANALYZING DATA...</p>
              </div>
            )}
          </main>
        </>
      )}
    </div>
  );
};

export default App;
