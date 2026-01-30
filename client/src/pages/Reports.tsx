import { Component, createSignal, For, Show } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import { 
  OcGraph2, 
  OcAlert2, 
  OcFile2, 
  OcSearch2, 
  OcDownload2, 
  OcEye2,
  OcTable2,
  OcTerminal2,
  OcPlus2,
  OcPulse2,
} from 'solid-icons/oc';
import { AiOutlineFilePdf } from 'solid-icons/ai'
import { IoWaterOutline } from 'solid-icons/io'

interface Report {
  id: string;
  title: string;
  date: string;
  type: string;
  status: 'completed' | 'processing' | 'scheduled';
  size: string;
  progress?: number; // Added for professional UX
}

const Reports: Component = () => {
  const [reports] = createSignal<Report[]>([
    { id: '1', title: 'Q1 2026 Agricultural Performance Report', date: '2026-03-31', type: 'Quarterly', status: 'completed', size: '4.2 MB' },
    { id: '2', title: 'Weekly Yield Analysis - Week 12', date: '2026-03-24', type: 'Weekly', status: 'completed', size: '1.8 MB' },
    { id: '3', title: 'Risk Assessment - Mekong Delta', date: '2026-03-20', type: 'Custom', status: 'completed', size: '3.5 MB' },
    { id: '4', title: 'Water Usage Optimization Report', date: '2026-03-15', type: 'processing', progress: 65, status: 'completed', size: '-' },
    { id: '5', title: 'Seasonal Forecast Report - Summer 2026', date: '2026-04-01', type: 'Seasonal', status: 'scheduled', size: '-' },
  ]);

  const getStatusStyle = (status: Report['status']) => {
    switch (status) {
      case 'completed': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
      case 'processing': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      case 'scheduled': return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  return (
    <Layout>
      <div class="p-8 space-y-8 max-w-7xl mx-auto animate-in fade-in duration-500">
        
        {/* Header Section */}
        <div class="flex items-end justify-between">
          <div class="space-y-1">
            <h1 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">System Reports</h1>
            <p class="text-slate-500 dark:text-slate-400 font-medium">Audit and export agricultural intelligence data</p>
          </div>
          <button class="flex items-center gap-2 px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold transition-all shadow-lg shadow-blue-500/25 active:scale-95 group">
            <OcPlus2 size={18} class="group-hover:rotate-90 transition-transform" />
            Generate New Report
          </button>
        </div>

        {/* Templates Grid */}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <TemplateCard title="Performance" desc="Yield and efficiency analysis" icon={<OcGraph2 size={24} />} color="blue" />
          <TemplateCard title="Risk Assessment" desc="Identify potential threats" icon={<OcAlert2 size={24} />} color="rose" />
          <TemplateCard title="Resource Audit" desc="Water and cost optimization" icon={<IoWaterOutline size={24} />} color="indigo" />
        </div>

        {/* Reporting Log Table */}
        <div class="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors">
          <div class="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/30 dark:bg-slate-800/30">
            <div class="flex items-center gap-2">
              <OcPulse2 size={16} class="text-blue-500" />
              <h3 class="text-xs font-bold uppercase tracking-[0.15em] text-slate-700 dark:text-slate-300">Live Reporting Log</h3>
            </div>
            <div class="relative w-72">
              <OcSearch2 class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
              <input
                type="text"
                placeholder="Filter by report title..."
                class="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-medium outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-sm"
              />
            </div>
          </div>

          <div class="divide-y divide-slate-100 dark:divide-slate-800">
            <For each={reports()}>
              {(report) => (
                <div class="p-6 hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-all group">
                  <div class="flex items-center justify-between">
                    <div class="flex items-start gap-5">
                      <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-slate-400 group-hover:text-blue-500 transition-colors">
                        <OcFile2 size={22} />
                      </div>
                      <div class="space-y-1.5">
                        <div class="flex items-center gap-3">
                          <h4 class="text-sm font-bold text-slate-900 dark:text-white leading-none">{report.title}</h4>
                          <span class={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-tighter ${getStatusStyle(report.status)}`}>
                            {report.status}
                          </span>
                        </div>
                        
                        <div class="flex items-center gap-3 text-[11px] font-bold text-slate-400 uppercase tracking-tight">
                          <span>{report.type}</span>
                          <span class="w-1.5 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full" />
                          <span>{new Date(report.date).toLocaleDateString()}</span>
                          <Show when={report.size !== '-'}>
                            <span class="w-1.5 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full" />
                            <span>{report.size}</span>
                          </Show>
                        </div>

                        {/* Professional Progress Bar for Processing State */}
                        <Show when={report.status === 'processing'}>
                          <div class="w-48 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full mt-3 overflow-hidden">
                            <div class="h-full bg-blue-500 animate-pulse" style={{ width: `${report.progress}%` }}></div>
                          </div>
                        </Show>
                      </div>
                    </div>
                    
                    <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0">
                      <Show when={report.status === 'completed'}>
                        <ReportAction icon={<OcEye2 size={16} />} label="Preview" />
                        <ReportAction icon={<OcDownload2 size={16} />} label="Export" primary />
                      </Show>
                      <Show when={report.status !== 'completed'}>
                         <div class="text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-lg">
                           Standby
                         </div>
                      </Show>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>

        {/* Data Export Formats HUD */}
        <div class="bg-slate-900 dark:bg-slate-950 rounded-3xl p-8 border border-white/5 shadow-2xl relative overflow-hidden">
          <div class="absolute top-0 right-0 p-8 opacity-10">
            <OcPulse2 size={120} class="text-white" />
          </div>
          <div class="relative z-10">
            <h3 class="text-xs font-black uppercase tracking-[0.3em] text-blue-400 mb-6">Raw Data Engine</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ExportBtn icon={<AiOutlineFilePdf size={24} class="text-rose-500" />} label="PDF Report" />
              <ExportBtn icon={<OcTable2 size={24} class="text-emerald-500" />} label="XLSX Sheet" />
              <ExportBtn icon={<OcFile2 size={24} class="text-blue-400" />} label="CSV Stream" />
              <ExportBtn icon={<OcTerminal2 size={24} class="text-slate-400" />} label="JSON Endpoint" />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

const TemplateCard = (props: any) => (
  <div class={`bg-linear-to-br from-${props.color}-50/50 to-${props.color}-100/50 dark:from-${props.color}-900/10 dark:to-${props.color}-800/10 rounded-3xl p-7 border border-${props.color}-200/50 dark:border-${props.color}-800/30 hover:shadow-2xl hover:-translate-y-1.5 transition-all cursor-pointer group`}>
    <div class={`w-14 h-14 flex items-center justify-center rounded-2xl bg-white dark:bg-slate-900 shadow-md mb-5 text-${props.color}-600 group-hover:scale-110 transition-transform`}>
      {props.icon}
    </div>
    <h3 class="text-sm font-black text-slate-900 dark:text-white mb-2 uppercase tracking-tight">{props.title}</h3>
    <p class="text-xs text-slate-500 dark:text-slate-400 font-bold leading-relaxed">{props.desc}</p>
  </div>
);

const ReportAction = (props: any) => (
  <button class={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black transition-all active:scale-90 ${
    props.primary 
    ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/20' 
    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50'
  }`}>
    {props.icon} <span class="uppercase tracking-tighter">{props.label}</span>
  </button>
);

const ExportBtn = (props: any) => (
  <button class="flex flex-col items-center justify-center p-6 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl transition-all hover:scale-[1.02] group">
    <div class="mb-3 group-hover:rotate-12 transition-transform">{props.icon}</div>
    <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest group-hover:text-white transition-colors">{props.label}</span>
  </button>
);

export default Reports;