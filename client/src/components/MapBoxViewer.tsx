import { Component, createSignal, onMount, onCleanup, createEffect } from 'solid-js';
import mapboxgl from 'mapbox-gl';
import { 
  OcTelescope2, 
  OcSun2, 
  OcMoon2,
  OcLocation2
} from 'solid-icons/oc';
import { FaSolidMapLocationDot, FaSolidLayerGroup, FaSolidSatelliteDish } from 'solid-icons/fa'

// Replace with your actual token
mapboxgl.accessToken = 'pk.eyJ1IjoiZXhhbXBsZS11c2VyIiwiYSI6ImNrZXhhbXBsZTEyMzQ1Njc4OTAifQ.example';

interface MapBoxViewerProps {
  center?: [number, number];
  zoom?: number;
}

const MapBoxViewer: Component<MapBoxViewerProps> = (props) => {
  let mapContainer: HTMLDivElement | undefined;
  let map: mapboxgl.Map | undefined;
  const [currentStyle, setCurrentStyle] = createSignal<'satellite' | 'streets' | 'dark'>('satellite');
  const [showNDVI, setShowNDVI] = createSignal(false);

  const mapStyles = {
    satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
    streets: 'mapbox://styles/mapbox/streets-v12',
    dark: 'mapbox://styles/mapbox/dark-v11',
  };

  onMount(() => {
    if (!mapContainer) return;

    map = new mapboxgl.Map({
      container: mapContainer,
      style: mapStyles[currentStyle()],
      center: props.center || [106.0, 16.0],
      zoom: props.zoom || 5.5,
      antialias: true
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.addControl(new mapboxgl.ScaleControl(), 'bottom-right');

    map.on('load', () => {
      // Add Mekong Delta GeoJSON
      map?.addSource('mekong-delta', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[[104.5, 10.5], [106.5, 10.5], [106.5, 9.0], [104.5, 9.0], [104.5, 10.5]]],
          },
          properties: {},
        },
      });

      map?.addLayer({
        id: 'mekong-delta-fill',
        type: 'fill',
        source: 'mekong-delta',
        paint: { 'fill-color': '#22c55e', 'fill-opacity': 0.2 },
      });
    });
  });

  // Handle style changes reactively
  createEffect(() => {
    const style = currentStyle();
    if (map) map.setStyle(mapStyles[style]);
  });

  onCleanup(() => map?.remove());

  return (
    <div class="relative h-full w-full overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800">
      <div ref={mapContainer} class="h-full w-full" />
      
      {/* Control Panels Container */}
      <div class="absolute top-4 left-4 flex flex-col gap-4 z-10">
        
        {/* Basemap Switcher */}
        <div class="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl p-3 w-48 space-y-3">
          <div class="flex items-center gap-2 text-slate-800 dark:text-slate-200">
            <FaSolidMapLocationDot size={16} class="text-blue-500" />
            <h3 class="font-bold text-xs uppercase tracking-wider">Base Map</h3>
          </div>
          <div class="space-y-1">
            <MapStyleBtn active={currentStyle() === 'satellite'} onClick={() => setCurrentStyle('satellite')} label="Satellite" icon={<FaSolidSatelliteDish size={14} />} />
            <MapStyleBtn active={currentStyle() === 'streets'} onClick={() => setCurrentStyle('streets')} label="Streets" icon={<OcSun2 size={14} />} />
            <MapStyleBtn active={currentStyle() === 'dark'} onClick={() => setCurrentStyle('dark')} label="Night" icon={<OcMoon2 size={14} />} />
          </div>
        </div>

        {/* Analysis Layers */}
        <div class="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl p-3 w-48 space-y-3">
          <div class="flex items-center gap-2 text-slate-800 dark:text-slate-200">
            <FaSolidLayerGroup size={16} class="text-emerald-500" />
            <h3 class="font-bold text-xs uppercase tracking-wider">Analytics</h3>
          </div>
          <div class="space-y-2">
            <LayerToggle checked={showNDVI()} onChange={setShowNDVI} label="NDVI Index" />
            <LayerToggle checked={true} onChange={() => {}} label="Crop Health" />
          </div>
        </div>
      </div>

      {/* Legend - Bottom Left */}
      <div class="absolute bottom-4 left-4 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl p-4 z-10 space-y-3">
        <div class="flex items-center gap-2 text-slate-800 dark:text-slate-200">
          <OcTelescope2 size={16} class="text-indigo-500" />
          <h3 class="font-bold text-xs uppercase tracking-wider">Legend</h3>
        </div>
        <div class="space-y-2 text-[11px] font-medium text-slate-600 dark:text-slate-400">
          <LegendItem color="bg-emerald-400" label="Healthy Crops" />
          <LegendItem color="bg-blue-400" label="Irrigation Zones" />
          <div class="flex items-center gap-2">
            <OcLocation2 size={12} class="text-blue-500" />
            <span>Active Sensors</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Reusable Sub-components
const MapStyleBtn = (props: { active: boolean, onClick: () => void, label: string, icon: any }) => (
  <button
    onClick={props.onClick}
    class={`w-full flex items-center gap-2 px-3 py-2 text-xs rounded-lg transition-all ${
      props.active 
        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
    }`}
  >
    {props.icon} {props.label}
  </button>
);

const LayerToggle = (props: { checked: boolean, onChange: (v: boolean) => void, label: string }) => (
  <label class="flex items-center justify-between cursor-pointer group">
    <span class="text-xs text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{props.label}</span>
    <input 
      type="checkbox" 
      checked={props.checked} 
      onChange={(e) => props.onChange(e.currentTarget.checked)}
      class="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500 bg-transparent" 
    />
  </label>
);

const LegendItem = (props: { color: string, label: string }) => (
  <div class="flex items-center gap-2">
    <div class={`w-3 h-3 ${props.color} rounded-sm shadow-sm ring-1 ring-black/5`}></div>
    <span>{props.label}</span>
  </div>
);

export default MapBoxViewer;