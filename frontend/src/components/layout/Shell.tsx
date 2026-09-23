import React, { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useSidebar } from '../../context/SidebarContext';

interface ShellProps {
  children: ReactNode;
}

export const Shell: React.FC<ShellProps> = ({ children }) => {
  const { isCollapsed } = useSidebar();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex transition-colors duration-200">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className={`flex flex-col flex-1 min-h-screen w-full transition-all duration-300 ${isCollapsed ? 'pl-16' : 'pl-64'}`}>
        <Header />
        <main className="pt-14 p-4 sm:p-6 min-h-[calc(100vh-3.5rem)] w-full">
          {children}
        </main>
      </div>
    </div>
  );
};
