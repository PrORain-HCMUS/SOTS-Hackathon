import { Component, createSignal, onMount, onCleanup } from 'solid-js';
import mapboxgl from 'mapbox-gl';

// Free MapBox token (demo purposes - replace with your own)
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

    // Initialize MapBox map (Vietnam center)
    const center = props.center || [106.0, 16.0]; // [lng, lat] for MapBox
    const zoom = props.zoom || 6;

    map = new mapboxgl.Map({
      container: mapContainer,
      style: mapStyles.satellite,
      center: center as [number, number],
      zoom: zoom,
      pitch: 0,
      bearing: 0,
    });

    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.addControl(new mapboxgl.ScaleControl(), 'bottom-right');
    map.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    // Add markers for major cities
    const cities = [
      { name: 'Hà Nội', coords: [105.8542, 21.0285] },
      { name: 'TP.HCM', coords: [106.6297, 10.8231] },
      { name: 'Đà Nẵng', coords: [108.2022, 16.0544] },
      { name: 'Cần Thơ', coords: [105.7469, 10.0452] },
      { name: 'An Giang', coords: [105.1258, 10.5216] },
    ];

    map.on('load', () => {
      // Add markers
      cities.forEach((city) => {
        const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(
          `<strong>${city.name}</strong><br>Crop monitoring area`
        );

        new mapboxgl.Marker({ color: '#3b82f6' })
          .setLngLat(city.coords as [number, number])
          .setPopup(popup)
          .addTo(map!);
      });

      // Add Mekong Delta polygon
      map!.addSource('mekong-delta', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [104.5, 10.5],
              [106.5, 10.5],
              [106.5, 9.0],
              [104.5, 9.0],
              [104.5, 10.5],
            ]],
          },
          properties: {
            name: 'Đồng Bằng Sông Cửu Long',
          },
        },
      });

      map!.addLayer({
        id: 'mekong-delta-fill',
        type: 'fill',
        source: 'mekong-delta',
        paint: {
          'fill-color': '#22c55e',
          'fill-opacity': 0.3,
        },
      });

      map!.addLayer({
        id: 'mekong-delta-outline',
        type: 'line',
        source: 'mekong-delta',
        paint: {
          'line-color': '#16a34a',
          'line-width': 2,
        },
      });
    });
  });

  onCleanup(() => {
    if (map) {
      map.remove();
    }
  });

  const changeMapStyle = (style: 'satellite' | 'streets' | 'dark') => {
    if (map) {
      map.setStyle(mapStyles[style]);
      setCurrentStyle(style);
    }
  };

  const toggleNDVI = () => {
    setShowNDVI(!showNDVI());
    // NDVI overlay logic would go here
  };

  return (
    <div class="relative h-full w-full">
      <div ref={mapContainer} class="h-full w-full" />
      
      {/* Basemap Switcher */}
      <div class="absolute top-4 left-4 bg-white rounded-lg shadow-xl p-3 z-10 min-w-[200px]">
        <h3 class="font-semibold text-gray-800 mb-3 text-sm">Base Map</h3>
        <div class="space-y-2">
          <button
            onClick={() => changeMapStyle('satellite')}
            class={`w-full px-3 py-2 text-sm rounded transition-colors ${
              currentStyle() === 'satellite'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🛰️ Satellite
          </button>
          <button
            onClick={() => changeMapStyle('streets')}
            class={`w-full px-3 py-2 text-sm rounded transition-colors ${
              currentStyle() === 'streets'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🗺️ Streets
          </button>
          <button
            onClick={() => changeMapStyle('dark')}
            class={`w-full px-3 py-2 text-sm rounded transition-colors ${
              currentStyle() === 'dark'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🌙 Dark
          </button>
        </div>
      </div>

      {/* Layers Panel */}
      <div class="absolute top-48 left-4 bg-white rounded-lg shadow-xl p-3 z-10 min-w-[200px]">
        <h3 class="font-semibold text-gray-800 mb-3 text-sm">Layers</h3>
        <div class="space-y-2">
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showNDVI()}
              onChange={toggleNDVI}
              class="w-4 h-4 text-primary-500 rounded"
            />
            <span class="text-sm text-gray-700">NDVI Overlay</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-sm text-gray-700">Crop Boundaries</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked class="w-4 h-4 text-primary-500 rounded" />
            <span class="text-sm text-gray-700">Cities</span>
          </label>
        </div>
      </div>

      {/* Legend */}
      <div class="absolute bottom-4 left-4 bg-white rounded-lg shadow-xl p-4 z-10">
        <h3 class="font-semibold text-gray-800 mb-2 text-sm">Legend</h3>
        <div class="space-y-2 text-xs">
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-green-400 rounded"></div>
            <span>Rice Fields</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-blue-400 rounded"></div>
            <span>Water Bodies</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-4 h-4 bg-red-400 rounded"></div>
            <span>Risk Areas</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 bg-primary-500 rounded-full"></div>
            <span>Monitoring Points</span>
          </div>
        </div>
      </div>

      {/* Coordinates Display */}
      <div class="absolute bottom-4 right-4 bg-white rounded-lg shadow-xl px-3 py-2 z-10 text-xs font-mono">
        Zoom: {map?.getZoom().toFixed(1)} | Center: Vietnam
      </div>
    </div>
  );
};

export default MapBoxViewer;
