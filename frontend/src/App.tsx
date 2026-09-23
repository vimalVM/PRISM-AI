import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Shell } from './components/layout/Shell';
import { RoleGuard } from './components/layout/RoleGuard';
import { LoginPage } from './pages/LoginPage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { VisionPage } from './pages/VisionPage';
import { ReviewPage } from './pages/ReviewPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { ArtifactsPage } from './pages/ArtifactsPage';
import { ModelsPage } from './pages/ModelsPage';
import { AuditPage } from './pages/AuditPage';
import { SovereigntyPage } from './pages/SovereigntyPage';
import { UsersPage } from './pages/UsersPage';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            {/* Authenticated Application Shell */}
            <Route
              path="/"
              element={
                <RoleGuard allowedRoles={['admin', 'engineer', 'reviewer']}>
                  <Shell>
                    <WorkbenchPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/vision"
              element={
                <RoleGuard allowedRoles={['admin', 'engineer', 'reviewer']}>
                  <Shell>
                    <VisionPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/review"
              element={
                <RoleGuard allowedRoles={['admin', 'reviewer', 'engineer']}>
                  <Shell>
                    <ReviewPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/kb"
              element={
                <RoleGuard>
                  <Shell>
                    <KnowledgeBasePage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/artifacts"
              element={
                <RoleGuard>
                  <Shell>
                    <ArtifactsPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/models"
              element={
                <RoleGuard>
                  <Shell>
                    <ModelsPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/audit"
              element={
                <RoleGuard allowedRoles={['admin', 'auditor']}>
                  <Shell>
                    <AuditPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/sovereignty"
              element={
                <RoleGuard>
                  <Shell>
                    <SovereigntyPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route
              path="/users"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <Shell>
                    <UsersPage />
                  </Shell>
                </RoleGuard>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};
