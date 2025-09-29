import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  Home, 
  Microscope, 
  TestTube, 
  Package, 
  BarChart3,
  Settings
} from 'lucide-react';

const Layout: React.FC = () => {
  const navItems = [
    { to: '/', icon: Home, label: 'Главная' },
    { to: '/strains', icon: Microscope, label: 'Штаммы' },
    { to: '/samples', icon: TestTube, label: 'Образцы' },
    { to: '/storage', icon: Package, label: 'Хранилище' },
    { to: '/analytics', icon: BarChart3, label: 'Аналитика' },
    { to: '/stats', icon: BarChart3, label: 'Статистика' },
  ];

  const handleAdminClick = () => {
    // Открываем админ-панель Django в новой вкладке
    // Используем относительный путь для всех режимов (nginx проксирует к backend)
    const adminUrl = '/admin/';
    window.open(adminUrl, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Microscope className="w-8 h-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">
                Система учета штаммов микроорганизмов
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">v1.0.0</span>
              <div 
                className="cursor-pointer transition-colors duration-200"
                onClick={handleAdminClick}
                title="Админ-панель"
              >
                <Settings className="w-5 h-5 text-gray-400 hover:text-blue-600" />
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
          <div className="p-4">
            <div className="space-y-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                      isActive
                        ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-600'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;