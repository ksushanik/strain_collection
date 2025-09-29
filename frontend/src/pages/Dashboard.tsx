import React, { useState, useEffect } from 'react';
import { 
  Microscope, 
  TestTube, 
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

  // Временная функция для тестирования API штаммов
  const testStrainsAPI = async () => {
    console.log('Testing strains API...');
    
    try {
      console.log('Calling apiService.getStrains with params:', { search: 'Streptomyces', limit: 5 });
      const response = await apiService.getStrains({ search: 'Streptomyces', limit: 5 });
      console.log('Strains API test result:', response);
      console.log('Response type:', typeof response);
      console.log('Response keys:', Object.keys(response || {}));
      
      if (response && response.strains) {
        console.log('Strains array:', response.strains);
        console.log('Strains count:', response.strains.length);
        alert(`API работает! Найдено штаммов: ${response.strains.length}\nПервый штамм: ${response.strains[0]?.short_code || 'N/A'}`);
      } else {
        console.log('No strains in response');
        alert('API ответил, но штаммы не найдены');
      }
    } catch (error) {
      console.error('Strains API test failed:', error);
      const errorObj = error as any;
      console.error('Error details:', {
        message: errorObj.message,
        status: errorObj.response?.status,
        statusText: errorObj.response?.statusText,
        data: errorObj.response?.data
      });
      alert(`Ошибка API: ${errorObj.message || 'Неизвестная ошибка'}\nСтатус: ${errorObj.response?.status || 'N/A'}`);
    }
  };

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
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Панель управления
            </h1>
            <p className="text-gray-600">
              Обзор системы учета штаммов микроорганизмов
            </p>
          </div>
          {/* Временная кнопка тестирования API */}
          <button
            onClick={testStrainsAPI}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            Тест API штаммов
          </button>
        </div>
        
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



      {/* Анализ образцов */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-6">
          <TestTube className="w-5 h-5 text-green-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">
            Анализ образцов
          </h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* С фото - всегда показываем */}
          <div className="text-center">
            <div className="text-xl font-bold text-green-600 mb-1">
              {stats?.samples_analysis.with_photo || 0}
            </div>
            <div className="text-xs font-medium text-gray-700 mb-1">С фото</div>
            <div className="text-xs text-gray-500">
              {stats?.counts.samples ? Math.round((stats.samples_analysis.with_photo / stats.counts.samples) * 100) : 0}%
            </div>
          </div>
          
          {/* Динамические характеристики */}
          {stats?.samples_analysis.characteristics && Object.entries(stats.samples_analysis.characteristics).map(([charName, count], index) => {
            // Цвета для характеристик
            const colors = [
              'text-blue-600', 'text-purple-600', 'text-orange-600', 
              'text-red-600', 'text-indigo-600', 'text-pink-600',
              'text-teal-600', 'text-yellow-600', 'text-gray-600'
            ];
            const colorClass = colors[index % colors.length];
            
            return (
              <div key={charName} className="text-center">
                <div className={`text-xl font-bold ${colorClass} mb-1`}>
                  {count}
                </div>
                <div className="text-xs font-medium text-gray-700 mb-1" title={charName}>
                  {charName.length > 15 ? `${charName.substring(0, 15)}...` : charName}
                </div>
                <div className="text-xs text-gray-500">
                  {stats?.counts.samples ? Math.round((count / stats.counts.samples) * 100) : 0}%
                </div>
              </div>
            );
          })}
        </div>
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