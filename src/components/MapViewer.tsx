import { Component, createSignal, onMount, onCleanup } from 'solid-js';
import L from 'leaflet';

interface MapViewerProps {
  center?: [number, number];
  zoom?: number;
}

const MapViewer: Component<MapViewerProps> = (props) => {
  let mapContainer: HTMLDivElement | undefined;
  let map: L.Map | undefined;
  const [currentLayer, setCurrentLayer] = createSignal<'satellite' | 'streets' | 'terrain'>('satellite');
  
  // Layer references
  let satelliteLayer: L.TileLayer;
  let streetsLayer: L.TileLayer;
  let terrainLayer: L.TileLayer;

  onMount(() => {
    if (!mapContainer) return;

    // Initialize map (Vietnam center)
    const center = props.center || [16.0, 106.0];
    const zoom = props.zoom || 6;

    map = L.map(mapContainer, {
      zoomControl: false,
    }).setView(center, zoom);

    // Add zoom control to top-right
    L.control.zoom({ position: 'topright' }).addTo(map);
    
    // Add scale control
    L.control.scale({ position: 'bottomright' }).addTo(map);

    // Create different base layers
    satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri',
      maxZoom: 18,
    });

    streetsLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    });

    terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenTopoMap contributors',
      maxZoom: 17,
    });

    // Add default satellite layer
    satelliteLayer.addTo(map);

    // Add sample markers (Vietnam major cities)
    const cities = [
      { name: 'Hà Nội', coords: [21.0285, 105.8542] as [number, number] },
      { name: 'TP.HCM', coords: [10.8231, 106.6297] as [number, number] },
      { name: 'Đà Nẵng', coords: [16.0544, 108.2022] as [number, number] },
      { name: 'Cần Thơ', coords: [10.0452, 105.7469] as [number, number] },
      { name: 'An Giang', coords: [10.5216, 105.1258] as [number, number] },
    ];

    cities.forEach((city) => {
      const marker = L.marker(city.coords).addTo(map!);
      marker.bindPopup(`<b>${city.name}</b><br>Crop monitoring area`);
    });

    // Add sample polygon (Mekong Delta region)
    const mekongDelta = L.polygon([
      [10.5, 104.5],
      [10.5, 106.5],
      [9.0, 106.5],
      [9.0, 104.5],
    ], {
      color: 'green',
      fillColor: '#90EE90',
      fillOpacity: 0.3,
    }).addTo(map);

    mekongDelta.bindPopup('<b>Đồng Bằng Sông Cửu Long</b><br>Rice cultivation area');
  });

  onCleanup(() => {
    if (map) {
      map.remove();
    }
  });

  const switchLayer = (layerType: 'satellite' | 'streets' | 'terrain') => {
    if (!map) return;
    
    // Remove all layers
    map.removeLayer(satelliteLayer);
    map.removeLayer(streetsLayer);
    map.removeLayer(terrainLayer);
    
    // Add selected layer
    if (layerType === 'satellite') {
      satelliteLayer.addTo(map);
    } else if (layerType === 'streets') {
      streetsLayer.addTo(map);
    } else {
      terrainLayer.addTo(map);
    }
    
    setCurrentLayer(layerType);
  };

  return (
    <div class="relative h-full w-full">
      <div ref={mapContainer} class="h-full w-full" />
      
      {/* Base Map Switcher */}
      <div class="absolute top-4 left-4 bg-white dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl shadow-2xl p-3 z-[1000] min-w-[200px]">
        <h3 class="font-semibold text-space-900 dark:text-white mb-3 text-sm">Base Map</h3>
        <div class="space-y-2">
          <button 
            onClick={() => switchLayer('satellite')}
            class={`w-full px-3 py-2 text-sm rounded-lg transition-all font-medium ${
              currentLayer() === 'satellite' 
                ? 'bg-primary-500 text-white shadow-md' 
                : 'bg-space-50 dark:bg-space-800 text-space-700 dark:text-space-300 hover:bg-space-100 dark:hover:bg-space-700'
            }`}
          >
            Satellite
          </button>
          <button 
            onClick={() => switchLayer('streets')}
            class={`w-full px-3 py-2 text-sm rounded-lg transition-all font-medium ${
              currentLayer() === 'streets' 
                ? 'bg-primary-500 text-white shadow-md' 
                : 'bg-space-50 dark:bg-space-800 text-space-700 dark:text-space-300 hover:bg-space-100 dark:hover:bg-space-700'
            }`}
          >
            Streets
          </button>
          <button 
            onClick={() => switchLayer('terrain')}
            class={`w-full px-3 py-2 text-sm rounded-lg transition-all font-medium ${
              currentLayer() === 'terrain' 
                ? 'bg-primary-500 text-white shadow-md' 
                : 'bg-space-50 dark:bg-space-800 text-space-700 dark:text-space-300 hover:bg-space-100 dark:hover:bg-space-700'
            }`}
          >
            Terrain
          </button>
        </div>
      </div>

      {/* Layers Panel */}
      <div class="absolute top-56 left-4 bg-white dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl shadow-2xl p-3 z-[1000] min-w-[200px]">
        <h3 class="font-semibold text-space-900 dark:text-white mb-3 text-sm">Data Layers</h3>
        <div class="space-y-2 text-sm">
          <label class="flex items-center gap-2 cursor-pointer hover:bg-space-50 dark:hover:bg-space-800 p-1 rounded">
            <input type="checkbox" class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-space-700 dark:text-space-300">NDVI Overlay</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer hover:bg-space-50 dark:hover:bg-space-800 p-1 rounded">
            <input type="checkbox" class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-space-700 dark:text-space-300">Crop Boundaries</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer hover:bg-space-50 dark:hover:bg-space-800 p-1 rounded">
            <input type="checkbox" checked class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-space-700 dark:text-space-300">Monitoring Points</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer hover:bg-space-50 dark:hover:bg-space-800 p-1 rounded">
            <input type="checkbox" class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-space-700 dark:text-space-300">Irrigation Systems</span>
          </label>
        </div>
      </div>

      {/* Legend */}
      <div class="absolute bottom-4 left-4 bg-white dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-xl shadow-2xl p-4 z-[1000] max-w-[200px]">
        <h3 class="font-semibold text-space-900 dark:text-white mb-3 text-sm">Legend</h3>
        <div class="space-y-2 text-xs">
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-green-400 rounded border border-green-600"></div>
            <span class="text-space-700 dark:text-space-300">Rice Fields</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-blue-400 rounded border border-blue-600"></div>
            <span class="text-space-700 dark:text-space-300">Water Bodies</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-red-400 rounded border border-red-600"></div>
            <span class="text-space-700 dark:text-space-300">Risk Areas</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 bg-primary-500 rounded-full border-2 border-white shadow"></div>
            <span class="text-space-700 dark:text-space-300">Monitoring Points</span>
          </div>
          <div class="border-t border-space-200 dark:border-space-700 my-2"></div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-2 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded"></div>
            <span class="text-space-700 dark:text-space-300">NDVI Index</span>
          </div>
        </div>
      </div>

      {/* Map Info */}
      <div class="absolute bottom-4 right-4 bg-white dark:bg-space-900 border border-space-200 dark:border-space-700 rounded-lg shadow-xl px-3 py-2 z-[1000] text-xs font-mono">
        <div class="text-space-600 dark:text-space-400">
          Vietnam Agricultural Monitoring
        </div>
      </div>
    </div>
  );
};

export default MapViewer;
