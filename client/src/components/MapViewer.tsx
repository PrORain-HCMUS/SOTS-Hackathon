import { Component, createSignal, onMount, onCleanup } from 'solid-js';
import L from 'leaflet';
import { 
  OcTelescope2, 
  OcLocation2,
  OcPulse2
} from 'solid-icons/oc';

import { IoLayers, IoMap } from 'solid-icons/io';

interface MapViewerProps {
  center?: [number, number];
  zoom?: number;
}

const MapViewer: Component<MapViewerProps> = (props) => {
  let mapContainer: HTMLDivElement | undefined;
  let map: L.Map | undefined;
  const [currentLayer, setCurrentLayer] = createSignal<'satellite' | 'streets' | 'terrain'>('satellite');
  
  let satelliteLayer: L.TileLayer;
  let streetsLayer: L.TileLayer;
  let terrainLayer: L.TileLayer;

  onMount(() => {
    if (!mapContainer) return;

    const center = props.center || [16.0, 106.0];
    const zoom = props.zoom || 6;

    map = L.map(mapContainer, { zoomControl: false }).setView(center, zoom);
    L.control.zoom({ position: 'topright' }).addTo(map);
    L.control.scale({ position: 'bottomright' }).addTo(map);

    satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri',
      maxZoom: 18,
    });

    streetsLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 18,
    });

    terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenTopoMap',
      maxZoom: 17,
    });

    satelliteLayer.addTo(map);

    const cities = [
      { name: 'Hà Nội', coords: [21.0285, 105.8542] as [number, number] },
      { name: 'TP.HCM', coords: [10.8231, 106.6297] as [number, number] },
      { name: 'Đà Nẵng', coords: [16.0544, 108.2022] as [number, number] },
      { name: 'Cần Thơ', coords: [10.0452, 105.7469] as [number, number] },
    ];

    cities.forEach((city) => {
      L.marker(city.coords).addTo(map!).bindPopup(`<b>${city.name}</b><br>Crop monitoring area`);
    });
  });

  onCleanup(() => map?.remove());

  const switchLayer = (layerType: 'satellite' | 'streets' | 'terrain') => {
    if (!map) return;
    [satelliteLayer, streetsLayer, terrainLayer].forEach(l => map?.removeLayer(l));
    
    if (layerType === 'satellite') satelliteLayer.addTo(map);
    else if (layerType === 'streets') streetsLayer.addTo(map);
    else terrainLayer.addTo(map);
    
    setCurrentLayer(layerType);
  };

  return (
    <div class="relative h-full w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 shadow-inner">
      <div ref={mapContainer} class="h-full w-full z-0" />
      
      {/* Base Map Switcher */}
      <div class="absolute top-4 left-4 flex flex-col w-48 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-1000 p-3 space-y-3">
        <div class="flex items-center gap-2 text-slate-900 dark:text-white">
          <IoMap size={16} class="text-blue-500" />
          <h3 class="font-bold text-xs uppercase tracking-wider">Base Map</h3>
        </div>
        <div class="space-y-1.5">
          {(['satellite', 'streets', 'terrain'] as const).map((type) => (
            <button 
              onClick={() => switchLayer(type)}
              class={`w-full px-3 py-2 text-xs rounded-lg transition-all capitalize font-medium text-left ${
                currentLayer() === type 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Layers Panel */}
      <div class="absolute top-52 left-4 w-48 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-1000 p-3 space-y-3">
        <div class="flex items-center gap-2 text-slate-900 dark:text-white">
          <IoLayers size={16} class="text-indigo-500" />
          <h3 class="font-bold text-xs uppercase tracking-wider">Analysis</h3>
        </div>
        <div class="space-y-1">
          {['NDVI Overlay', 'Crop Boundaries', 'Irrigation'].map((layer) => (
            <label class="flex items-center gap-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 p-1.5 rounded-md transition-colors group">
              <input type="checkbox" class="w-3.5 h-3.5 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500" />
              <span class="text-xs text-slate-600 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white">{layer}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div class="absolute bottom-4 left-4 w-48 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-1000 p-3 space-y-3">
        <div class="flex items-center gap-2 text-slate-900 dark:text-white">
          <OcTelescope2 size={16} class="text-emerald-500" />
          <h3 class="font-bold text-xs uppercase tracking-wider">Legend</h3>
        </div>
        <div class="space-y-2.5">
          <LegendItem color="bg-emerald-400" label="Rice Fields" />
          <LegendItem color="bg-blue-400" label="Water Bodies" />
          <LegendItem color="bg-rose-400" label="Risk Areas" />
          <div class="flex items-center gap-3">
            <OcLocation2 size={12} class="text-blue-500" />
            <span class="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Monitoring Hubs</span>
          </div>
          <div class="pt-2 border-t border-slate-200 dark:border-slate-700">
            <div class="flex justify-between text-[10px] text-slate-400 mb-1 font-mono uppercase">
              <span>Low</span>
              <span>NDVI</span>
              <span>High</span>
            </div>
            <div class="w-full h-1.5 bg-linear-to-r from-rose-500 via-yellow-400 to-emerald-500 rounded-full"></div>
          </div>
        </div>
      </div>

      {/* Bottom Right Info */}
      <div class="absolute bottom-4 right-14 flex items-center gap-3 bg-slate-900/80 backdrop-blur text-white px-3 py-1.5 rounded-full z-1000 border border-white/10 shadow-2xl">
        <OcPulse2 size={14} class="text-emerald-400 animate-pulse" />
        <span class="text-[10px] font-bold tracking-widest uppercase">Live Monitoring</span>
      </div>
    </div>
  );
};

const LegendItem = (props: { color: string, label: string }) => (
  <div class="flex items-center gap-3">
    <div class={`w-3 h-3 ${props.color} rounded-sm ring-1 ring-black/5 dark:ring-white/10 shadow-sm`}></div>
    <span class="text-xs text-slate-600 dark:text-slate-300 font-medium">{props.label}</span>
  </div>
);

export default MapViewer;