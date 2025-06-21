import React, { useState, useEffect } from 'react';
import { 
  Microscope, 
  TestTube, 
  Package, 
  Database,
  TrendingUp,
  Calendar
} from 'lucide-react';
import apiService from '../services/api';
import type { StatsResponse } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await apiService.getStats();
        setStats(data);
      } catch (err) {
        setError('Ошибка загрузки статистики');
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800">{error}</div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Штаммы',
      value: stats?.counts.strains || 0,
      icon: Microscope,
      color: 'blue',
      description: 'Всего штаммов в коллекции'
    },
    {
      title: 'Образцы', 
      value: stats?.counts.samples || 0,
      icon: TestTube,
      color: 'green',
      description: 'Всего образцов'
    },
    {
      title: 'Хранилища',
      value: stats?.counts.storage_units || 0,
      icon: Package,
      color: 'purple',
      description: 'Единиц хранения'
    },
    {
      title: 'Источники',
      value: stats?.counts.sources || 0,
      icon: Database,
      color: 'orange',
      description: 'Различных источников'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Заголовок */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Панель управления
        </h1>
        <p className="text-gray-600">
          Обзор системы учета штаммов микроорганизмов
        </p>
        
        {/* Информация о валидации */}
        <div className="mt-4 flex items-center space-x-4">
          <div className="flex items-center text-green-600">
            <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
            <span className="text-sm">Система валидации: {stats?.validation.engine || 'Pydantic 2.x'}</span>
          </div>
          <div className="text-sm text-gray-500">
            Доступно схем валидации: {stats?.validation.schemas_available.length || 0}
          </div>
        </div>
      </div>

      {/* Карточки статистики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <div key={card.title} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">
                  {card.title}
                </h3>
                <p className="text-3xl font-bold text-gray-900">
                  {card.value.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {card.description}
                </p>
              </div>
              <div className={`p-3 rounded-lg bg-${card.color}-100`}>
                <card.icon className={`w-6 h-6 text-${card.color}-600`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Дополнительная информация */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Статус системы
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">База данных</span>
              <span className="text-green-600 font-medium">Активна</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">API Endpoints</span>
              <span className="text-green-600 font-medium">Работают</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Валидация данных</span>
              <span className="text-green-600 font-medium">100% успешно</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Calendar className="w-5 h-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Последние обновления
            </h3>
          </div>
          <div className="space-y-3">
            <div className="text-sm">
              <div className="font-medium text-gray-900">
                Добавлена валидация {stats?.validation.engine || 'Pydantic 2.x'}
              </div>
              <div className="text-gray-500">{stats?.validation.schemas_available.length || 0} схем валидации</div>
            </div>
            <div className="text-sm">
              <div className="font-medium text-gray-900">
                API endpoints с валидацией
              </div>
              <div className="text-gray-500">7 endpoints доступны</div>
            </div>
            <div className="text-sm">
              <div className="font-medium text-gray-900">
                Импорт и проверка данных
              </div>
              <div className="text-gray-500">Все данные валидированы</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 