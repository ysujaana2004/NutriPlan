import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/Layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { MealPlans } from './pages/MealPlans';
import { Recipes } from './pages/Recipes';
import { ShoppingList } from './pages/ShoppingList';
import { Analytics } from './pages/Analytics';
import { Budget } from './pages/Budget';
import { Settings } from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="meal-plans" element={<MealPlans />} />
          <Route path="recipes" element={<Recipes />} />
          <Route path="shopping-list" element={<ShoppingList />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="budget" element={<Budget />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
