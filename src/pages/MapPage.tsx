import { Component } from 'solid-js';
import Layout from '../layouts/Layout.tsx';
import MapViewer from '../components/MapViewer.tsx';

const MapPage: Component = () => {
  return (
    <Layout>
      <div class="h-full relative">
        <MapViewer />
      </div>
    </Layout>
  );
};

export default MapPage;
