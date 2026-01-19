/**
 * Shadow Hubble - Fraud Detection MLOps Platform
 * Main Application Component
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntApp } from 'antd';
import { MainLayout } from './components/Layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { DataRegistry } from './pages/DataRegistry';
import { Training } from './pages/Training';
import { ModelRegistry } from './pages/ModelRegistry';
import { ModelComparison } from './pages/ModelComparison';
import { Inference } from './pages/Inference';
import { Monitoring } from './pages/Monitoring';
import { Jobs } from './pages/Jobs';
import { Retraining } from './pages/Retraining';
import { ABTesting } from './pages/ABTesting';
import { Alerts } from './pages/Alerts';

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 30000, // 30 seconds
            refetchOnWindowFocus: false,
        },
    },
});

// Theme configuration
const theme = {
    token: {
        colorPrimary: '#2563EB',
        colorSuccess: '#059669',
        colorWarning: '#D97706',
        colorError: '#DC2626',
        borderRadius: 8,
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    },
};

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <ConfigProvider theme={theme}>
                <AntApp>
                    <BrowserRouter>
                        <MainLayout>
                            <Routes>
                                <Route path="/" element={<Dashboard />} />
                                <Route path="/data" element={<DataRegistry />} />
                                <Route path="/training" element={<Training />} />
                                <Route path="/models" element={<ModelRegistry />} />
                                <Route path="/models/compare" element={<ModelComparison />} />
                                <Route path="/inference" element={<Inference />} />
                                <Route path="/monitoring" element={<Monitoring />} />
                                <Route path="/jobs" element={<Jobs />} />
                                <Route path="/retraining" element={<Retraining />} />
                                <Route path="/ab-testing" element={<ABTesting />} />
                                <Route path="/alerts" element={<Alerts />} />
                                <Route path="*" element={<Navigate to="/" replace />} />
                            </Routes>
                        </MainLayout>
                    </BrowserRouter>
                </AntApp>
            </ConfigProvider>
        </QueryClientProvider>
    );
}

export default App;



