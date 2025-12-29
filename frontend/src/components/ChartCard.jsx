import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { Info } from 'lucide-react';
import { marked } from 'marked';

Chart.register(...registerables, ChartDataLabels);

const formatShortNumber = (val) => {
  if (val == null) return '';
  const abs = Math.abs(val);
  if (abs >= 100000000) return (val / 100000000).toFixed(1) + '億';
  if (abs >= 10000) return (val / 10000).toFixed(0) + '万';
  return val.toLocaleString();
};

const ChartCard = ({ title, data, type = 'bar', insight, layoutMode }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (chartRef.current && data) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const labels = Object.keys(data);
      const values = Object.values(data);

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: type,
        data: {
          labels: labels,
          datasets: [{
            label: title,
            data: values,
            backgroundColor: type === 'pie' || type === 'doughnut' 
              ? ['#2563eb', '#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#84cc16', '#eab308', '#f97316']
              : '#2563eb',
            borderColor: '#2563eb',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: type === 'pie' || type === 'doughnut',
              position: 'right'
            },
            datalabels: {
              anchor: 'end',
              align: 'top',
              formatter: (value) => formatShortNumber(value),
              font: { size: 10, weight: 'bold' }
            }
          },
          scales: type === 'pie' || type === 'doughnut' ? {} : {
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => formatShortNumber(value)
              }
            }
          }
        }
      });
    }
  }, [data, type, title]);

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col transition-all hover:shadow-md">
      <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
        <div className="w-1 h-4 bg-blue-600 rounded-full"></div>
        {title}
      </h3>
      <div className={`relative w-full ${layoutMode === 1 ? 'h-[350px]' : 'h-[250px]'} mb-4`}>
        <canvas ref={chartRef}></canvas>
      </div>
      {insight && (
        <div className="mt-auto bg-slate-50 p-3 rounded-xl border border-slate-100 flex gap-2 items-start">
          <Info size={16} className="text-blue-500 mt-0.5 shrink-0" />
          <div 
            className="text-xs text-slate-600 leading-relaxed prose-insight" 
            dangerouslySetInnerHTML={{ __html: marked.parse(insight) }}
          />
        </div>
      )}
    </div>
  );
};

export default ChartCard;
