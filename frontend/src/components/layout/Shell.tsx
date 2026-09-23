import React, { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface ShellProps {
  children: ReactNode;
}

export const Shell: React.FC<ShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-surface text-on-surface flex">
      {/* 288px Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="pl-72 flex flex-col flex-1 min-h-screen w-full">
        <Header />
        <main className="pt-16 p-6 min-h-[calc(100vh-4rem)] w-full">
          {children}
        </main>
      </div>
    </div>
  );
};
