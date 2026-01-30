import { Component } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import MapViewer from '../components/MapViewer.tsx';
import { OcPulse2, OcLocation2, OcShieldcheck2 } from 'solid-icons/oc';

const MapPage: Component = () => {
  return (
    <Layout>
      <div class="h-full w-full relative group">
        
        {/* Fullscreen Map Container */}
        <div class="absolute inset-0 z-0 w-full h-screen">
          <MapViewer />
        </div>

        {/* Top Floating Status Bar - Professional Overlay */}
        <div class="absolute top-6 left-1/2 -translate-x-1/2 flex items-center gap-6 px-6 py-3 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-700/50 rounded-2xl shadow-2xl z-10 transition-all duration-500 hover:py-4">
          <div class="flex items-center gap-3 border-r border-slate-200 dark:border-slate-800 pr-6">
            <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <div class="flex flex-col">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">System Status</span>
              <span class="text-xs font-bold text-slate-900 dark:text-white">Active Monitoring</span>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <MapStatusItem 
              icon={<OcLocation2 size={16} class="text-blue-500" />} 
              label="Sensors" 
              value="1,284" 
            />
            <MapStatusItem 
              icon={<OcPulse2 size={16} class="text-emerald-500" />} 
              label="Health" 
              value="98.2%" 
            />
            <MapStatusItem 
              icon={<OcShieldcheck2 size={16} class="text-indigo-500" />} 
              label="Incidents" 
              value="0" 
            />
          </div>
        </div>

        {/* Coordinates/Info Badge - Bottom Right */}
        <div class="absolute bottom-6 right-6 flex items-center gap-3 px-4 py-2 bg-slate-900/90 backdrop-blur-md text-white rounded-xl border border-white/10 shadow-2xl z-10 font-mono text-[10px] tracking-tighter">
          <span class="opacity-50 tracking-widest uppercase">Geospatial Engine:</span>
          <span class="font-bold text-blue-400 uppercase">Vector-HD</span>
          <span class="w-px h-3 bg-white/20" />
          <span>VN_SOUTH_ZONE_48N</span>
        </div>

      </div>
    </Layout>
  );
};

// Internal Sub-component for the overlay status items
const MapStatusItem = (props: { icon: any, label: string, value: string }) => (
  <div class="flex items-center gap-3 group/item cursor-default">
    <div class="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg group-hover/item:scale-110 transition-transform">
      {props.icon}
    </div>
    <div class="flex flex-col">
      <span class="text-[10px] font-medium text-slate-500 uppercase leading-none mb-1">{props.label}</span>
      <span class="text-sm font-bold text-slate-900 dark:text-white leading-none">{props.value}</span>
    </div>
  </div>
);

export default MapPage;