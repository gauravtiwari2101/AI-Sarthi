import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import Overview from './pages/Overview';
import ChatWorkspace from './pages/ChatWorkspace';
import DistrictDashboard from './pages/DistrictDashboard';
import DistrictDetail from './pages/DistrictDetail';
import AllocationStudio from './pages/AllocationStudio';
import Analytics from './pages/Analytics';
import SourceExplorer from './pages/SourceExplorer';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app-container">
          <Navbar />
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/overview" element={<Navigate to="/" replace />} />
            <Route path="/chat" element={<ChatWorkspace />} />
            <Route path="/districts" element={<DistrictDashboard />} />
            <Route path="/districts/:id" element={<DistrictDetail />} />
            <Route path="/allocations" element={<AllocationStudio />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/sources" element={<SourceExplorer />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
