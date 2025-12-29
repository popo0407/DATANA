import React from 'react';
import { Upload, BarChart3 } from 'lucide-react';

const SplashScreen = ({ onFileSelect }) => {
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelect(file);
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-50 to-slate-200 z-40 flex flex-col items-center justify-center">
      <div className="text-center p-10 max-w-lg w-full">
        <div className="mb-8 flex justify-center">
          <div className="bg-blue-600 p-4 rounded-2xl shadow-xl shadow-blue-500/20">
            <BarChart3 size={48} className="text-white" />
          </div>
        </div>
        <h1 className="text-4xl font-extrabold text-slate-800 mb-3 tracking-tight">
          Majin Analytics
        </h1>
        <p className="text-slate-500 mb-10 font-medium text-lg">
          高度なデータ分析とAI戦略レポートを、<br />
          あなたのローカル環境で。
        </p>
        
        <label className="group relative flex items-center justify-center gap-4 w-full bg-blue-600 hover:bg-blue-700 text-white text-xl font-bold py-6 px-8 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-blue-500/30 active:scale-[0.98] overflow-hidden">
          <Upload size={24} />
          <span>データ分析を開始する (CSV読込)</span>
          <input 
            type="file" 
            accept=".csv" 
            className="hidden" 
            onChange={handleFileChange}
          />
        </label>
        
        <p className="mt-6 text-slate-400 text-sm">
          ※ アップロードされたデータは暗号化され、安全に処理されます。
        </p>
      </div>
    </div>
  );
};

export default SplashScreen;
