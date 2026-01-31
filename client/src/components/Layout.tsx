import { Component, JSX } from 'solid-js';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: JSX.Element;
}

const Layout: Component<LayoutProps> = (props) => {
  return (
    <div class="flex h-screen bg-slate-50 dark:bg-slate-950">
      <Sidebar />
      <div class="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main class="flex-1 overflow-hidden">
          {props.children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
