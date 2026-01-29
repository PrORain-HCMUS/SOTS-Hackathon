import { Component, JSX } from 'solid-js';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import FloatingChatbot from '../components/FloatingChatbot';

interface LayoutProps {
  children: JSX.Element;
}

const Layout: Component<LayoutProps> = (props) => {
  return (
    <div class="flex h-screen bg-space-50 dark:bg-space-950 overflow-hidden transition-colors duration-200">
      <Sidebar />
      
      <div class="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main class="flex-1 overflow-y-auto">
          {props.children}
        </main>
      </div>

      <FloatingChatbot />
    </div>
  );
};

export default Layout;
