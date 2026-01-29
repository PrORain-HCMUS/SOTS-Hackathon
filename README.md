# Son of Sea - Agricultural Intelligence Platform

Modern web application for agricultural monitoring and analysis using satellite data.

## Tech Stack

- **Frontend Framework**: SolidJS 1.9.3 with TypeScript 5.7
- **Build Tool**: Vite 6.0.7
- **Styling**: TailwindCSS 3.4
- **Maps**: Leaflet 1.9 & Mapbox GL 3.8
- **Charts**: Apache ECharts 5.6
- **Routing**: Solid Router 0.15
- **State Management**: SolidJS Signals + Tanstack Solid Query 5.66
- **HTTP Client**: Axios 1.7

## Features

- 🗺️ **Interactive Map Viewer** - Dual map support (Leaflet & Mapbox GL)
- 💬 **AI Chatbot** - Floating chatbot interface for user assistance
- 📊 **Dashboard** - Real-time agricultural monitoring and statistics
- 📈 **Analytics** - Advanced data visualization with ECharts
- 📄 **Reports** - Generate and export agricultural reports
- ⚙️ **Settings** - Customizable application preferences
- 🌓 **Dark Mode** - Theme switching support

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

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
├── components/              # Reusable UI components
│   ├── Header.tsx           # Top navigation bar
│   ├── Sidebar.tsx          # Side navigation menu
│   ├── FloatingChatbot.tsx  # AI chatbot widget
│   ├── MapViewer.tsx        # Leaflet map component
│   └── MapBoxViewer.tsx     # Mapbox GL component
├── context/                 # React context providers
│   └── ThemeContext.tsx     # Theme management
├── layouts/                 # Layout wrappers
│   └── Layout.tsx           # Main app layout
├── pages/                   # Page components
│   ├── Dashboard.tsx        # Main dashboard
│   ├── MapPage.tsx          # Map visualization
│   ├── Analytics.tsx        # Data analytics
│   ├── Reports.tsx          # Report generation
│   └── Settings.tsx         # App settings
├── App.tsx                  # Root component with routing
├── index.tsx                # Application entry point
└── index.css                # Global styles & Tailwind
```

## Features Overview

### Floating Chatbot

- Always accessible via floating button
- Real-time chat interface
- Typing indicators and message history
- Expandable/collapsible design
- Responsive layout

### Map Viewer

- Dual map engine support (Leaflet & Mapbox GL)
- Multiple map layers and tile providers
- Custom markers and polygons
- Interactive controls and zoom
- Legend and data overlays

### Dashboard

- Real-time agricultural statistics
- Region and crop filtering
- Alert notifications system
- Quick action buttons
- Responsive grid layout

### Analytics

- Interactive charts powered by ECharts
- Data visualization and trends
- Export capabilities
- Customizable metrics

## Development

Built with modern web technologies for optimal performance and developer experience. Uses Vite for fast HMR and SolidJS for reactive UI updates.

## License

MIT
