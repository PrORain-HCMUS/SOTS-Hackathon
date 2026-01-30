import { Component, JSX } from 'solid-js';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import FloatingChatbot from '../components/FloatingChatbot';

interface LayoutProps {
  children: JSX.Element;
}

const Layout: Component<LayoutProps> = (props) => {
  return (
    <div class="flex h-screen w-full bg-slate-50 dark:bg-slate-950 transition-colors duration-300 overflow-hidden font-sans antialiased">
      {/* Permanent Sidebar */}
      <Sidebar />
      
      <div class="flex-1 flex flex-col relative min-w-0 overflow-hidden">
        {/* Sticky Header with Backdrop Blur */}
        <Header />
        
        {/* Main Content Area */}
        <main class="flex-1 overflow-y-auto overflow-x-hidden relative bg-slate-50/50 dark:bg-slate-900/20 scroll-smooth">
          {/* Internal wrapper for consistent padding and max-width control */}
          <div class="min-h-full">
            {props.children}
          </div>
        </main>
      </div>

      {/* Persistent Overlay Elements */}
      <FloatingChatbot />
    </div>
  );
};

export default Layout;