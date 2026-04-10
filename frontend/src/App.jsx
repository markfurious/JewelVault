import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StockPage from './pages/StockPage';
import SalesPage from './pages/SalesPage';
import CreateSalePage from './pages/CreateSalePage';
import ReorderSuggestionsPage from './pages/ReorderSuggestionsPage';
import AdminUsersPage from './pages/AdminUsersPage';
import AdminReturnsPage from './pages/AdminReturnsPage';
import ProductsPage from './pages/ProductsPage';
import InventoryPage from './pages/InventoryPage';
import ARTryOnPage from './pages/ar/ARTryOnPage';
import Generate3DModelsPage from './pages/admin/Generate3DModelsPage';
import MetalPricesPage from './pages/admin/MetalPricesPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Layout><DashboardPage /></Layout>} />
      <Route path="/stock" element={<Layout><StockPage /></Layout>} />
      <Route path="/products" element={<Layout><ProductsPage /></Layout>} />
      <Route path="/inventory" element={<Layout><InventoryPage /></Layout>} />
      <Route path="/sales" element={<Layout><SalesPage /></Layout>} />
      <Route path="/sales/create" element={<Layout><CreateSalePage /></Layout>} />
      <Route path="/reorder" element={<Layout><ReorderSuggestionsPage /></Layout>} />
      <Route path="/admin/users" element={<Layout><AdminUsersPage /></Layout>} />
      <Route path="/admin/returns" element={<Layout><AdminReturnsPage /></Layout>} />
      <Route path="/admin/generate-3d" element={<Layout><Generate3DModelsPage /></Layout>} />
      <Route path="/admin/metal-prices" element={<Layout><MetalPricesPage /></Layout>} />
      <Route path="/ar-tryon" element={<Layout><ARTryOnPage /></Layout>} />
    </Routes>
  );
}
