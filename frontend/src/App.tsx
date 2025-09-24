import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ScrollToTop from './components/ScrollToTop';
import Dashboard from './pages/Dashboard';
import { StrainsPage } from './features/strains';
import { SamplesPage } from './features/samples';
import StrainDetail from './pages/StrainDetail';
import AddStrain from './pages/AddStrain';
import SampleDetail from './pages/SampleDetail';
import AddSample from './pages/AddSample';
import Storage from './pages/Storage';
import Analytics from './pages/Analytics';
import './App.css';

function App() {
  return (
    <Router>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="/strains" element={<StrainsPage />} />
          <Route path="strains/add" element={<AddStrain />} />
          <Route path="strains/:id" element={<StrainDetail />} />
          <Route path="strains/:id/edit" element={<AddStrain />} />
          <Route path="samples" element={<SamplesPage />} />
          <Route path="samples/add" element={<AddSample />} />
          <Route path="samples/:id" element={<SampleDetail />} />
          <Route path="samples/:id/edit" element={<AddSample />} />
          <Route path="storage" element={<Storage />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="stats" element={<Dashboard />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
