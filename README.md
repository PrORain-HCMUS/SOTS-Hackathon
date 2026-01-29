# Son of Sea - Agricultural Intelligence Platform

Modern web application for agricultural monitoring and analysis using satellite data.

## Tech Stack

- **Frontend Framework**: SolidJS 1.9+ with TypeScript
- **Build Tool**: Vite 6.0
- **Styling**: TailwindCSS
- **Maps**: Leaflet
- **Charts**: Apache ECharts
- **Routing**: Solid Router
- **State Management**: SolidJS Signals + Solid Query

## Features

- 🗺️ **Interactive Map Viewer** - Leaflet-based map with satellite imagery
- 💬 **AI Chatbot** - Floating chatbot interface for user queries
- 📊 **Dashboard** - Real-time agricultural monitoring
- 📈 **Analytics** - Data visualization with charts
- 📄 **Reports** - Export and share reports

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Sidebar.tsx
│   ├── FloatingChatbot.tsx
│   └── MapViewer.tsx
├── layouts/            # Layout components
│   └── MainLayout.tsx
├── pages/             # Page components
│   └── Dashboard.tsx
├── App.tsx            # Root component
├── index.tsx          # Entry point
└── index.css          # Global styles
```

## Features Overview

### Floating Chatbot

- Always accessible via floating button
- Real-time chat interface
- Typing indicators
- Message history
- Responsive design

### Map Viewer

- Leaflet integration
- Multiple map layers
- Custom markers and polygons
- Interactive controls
- Legend and overlays

### Dashboard

- Real-time statistics
- Region filtering
- Alert notifications
- Quick actions
- Responsive layout

## License

MIT
