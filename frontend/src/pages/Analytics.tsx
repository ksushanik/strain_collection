import React, { useState, useEffect } from 'react';
import { BarChart3, PieChart, TrendingUp, Users, Beaker, Database, MapPin, Calendar } from 'lucide-react';
import apiService from '../services/api';
import type { AxiosError } from 'axios';


interface AnalyticsData {
  totalSamples: number;
  totalStrains: number;
  totalStorage: number;
  sourceTypeDistribution: { [key: string]: number };
  strainDistribution: { [key: string]: number };
  monthlyTrends: { month: string; count: number }[];
  characteristicsStats: {
    has_photo: number;
    [key: string]: number; // Динамические характеристики прямо в characteristicsStats
  };
  storageUtilization: {
    occupied: number;
    free: number;
    total: number;
  };
}

const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Используем новый оптимизированный endpoint для аналитики
      const analyticsData = await apiService.getAnalytics();
      
      setData({
        totalSamples: analyticsData.totalSamples,
        totalStrains: analyticsData.totalStrains,
        totalStorage: analyticsData.totalStorage,
        sourceTypeDistribution: analyticsData.sourceTypeDistribution,
        strainDistribution: analyticsData.strainDistribution,
        monthlyTrends: analyticsData.monthlyTrends,
        characteristicsStats: analyticsData.characteristicsStats,
        storageUtilization: analyticsData.storageUtilization
      });

    } catch (err: unknown) {
      console.error('Ошибка загрузки аналитики:', err);
      const axErr = err as AxiosError<{ message?: string; error?: string }>; 
      setError(axErr.response?.data?.message || axErr.response?.data?.error || axErr.message || 'Ошибка загрузки данных аналитики');
    } finally {
      setLoading(false);
    }
  };



  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-6 h-6 animate-pulse text-blue-600" />
          <span className="text-gray-600">Загрузка аналитики...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
        <button 
          onClick={loadAnalyticsData}
          className="mt-2 text-red-700 hover:text-red-900 underline"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (!data || data.totalSamples === undefined || data.totalStrains === undefined || data.totalStorage === undefined) {
    return <div>Нет данных для отображения</div>;
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Аналитика</h1>
            <p className="text-gray-600">
              Статистика и анализ коллекции штаммов
              <span className="ml-2 text-sm">
                ({data.totalSamples} образцов, {data.totalStrains} штаммов)
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Образцы</p>
              <p className="text-2xl font-bold">{(data.totalSamples || 0).toLocaleString()}</p>
            </div>
            <Beaker className="w-8 h-8 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Штаммы</p>
              <p className="text-2xl font-bold">{(data.totalStrains || 0).toLocaleString()}</p>
            </div>
            <Database className="w-8 h-8 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Ячейки хранения</p>
              <p className="text-2xl font-bold">{(data.totalStorage || 0).toLocaleString()}</p>
            </div>
            <MapPin className="w-8 h-8 text-purple-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">Заполненность</p>
              <p className="text-2xl font-bold">
                {Math.round(((data.storageUtilization?.occupied || 0) / (data.storageUtilization?.total || 1)) * 100)}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-200" />
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Source Types Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <PieChart className="w-5 h-5 mr-2 text-blue-600" />
            Распределение по типам источников
          </h3>
          <div className="space-y-3">
            {Object.entries(data.sourceTypeDistribution || {})
              .sort(([,a], [,b]) => b - a)
              .slice(0, 8)
              .map(([sourceType, count], index) => {
                const percentage = (count / (data.totalSamples || 1) * 100).toFixed(1);
                const colors = [
                  'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-red-500',
                  'bg-yellow-500', 'bg-indigo-500', 'bg-pink-500', 'bg-gray-500'
                ];
                return (
                  <div key={sourceType} className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded ${colors[index % colors.length]}`}></div>
                    <div className="flex-1 flex justify-between">
                      <span className="text-sm text-gray-700">{sourceType}</span>
                      <span className="text-sm font-medium text-gray-900">
                        {count} ({percentage}%)
                      </span>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Top Strains */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2 text-green-600" />
            Топ 10 штаммов по образцам
          </h3>
          <div className="space-y-3">
            {Object.entries(data.strainDistribution || {}).map(([strain, count]) => {
              const maxCount = Math.max(...Object.values(data.strainDistribution || {}));
              const percentage = (count / maxCount * 100);
              return (
                <div key={strain} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700 truncate">{strain}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-purple-600" />
            Создание образцов по месяцам
          </h3>
          <div className="space-y-3">
            {(data.monthlyTrends || []).map(({ month, count }) => {
              const maxCount = Math.max(...(data.monthlyTrends || []).map(t => t.count));
              const percentage = maxCount > 0 ? (count / maxCount * 100) : 0;
              return (
                <div key={month} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">{month}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full" 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Characteristics Stats */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2 text-orange-600" />
            Характеристики образцов
          </h3>
          <div className="space-y-3">
            {/* Photos statistics */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-lg">📷</span>
                <span className="text-sm text-gray-700">С фото</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">{data.characteristicsStats?.has_photo || 0}</div>
                <div className="text-xs text-gray-500">{((data.characteristicsStats?.has_photo || 0) / (data.totalSamples || 1) * 100).toFixed(0)}%</div>
              </div>
            </div>

            {/* Dynamic characteristics */}
            {data.characteristicsStats && Object.entries(data.characteristicsStats)
              .filter(([key]) => key !== 'has_photo') // Исключаем has_photo из динамических характеристик
              .map(([key, count]) => {
                const percentage = (count / (data.totalSamples || 1) * 100).toFixed(0);
                return (
                  <div key={key} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">🔬</span>
                      <span className="text-sm text-gray-700" title={key}>
                        {key.length > 15 ? `${key.substring(0, 15)}...` : key}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">{count}</div>
                      <div className="text-xs text-gray-500">{percentage}%</div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* Storage Utilization */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <MapPin className="w-5 h-5 mr-2 text-indigo-600" />
          Использование хранилища
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{data.storageUtilization?.occupied || 0}</div>
            <div className="text-sm text-gray-600">Занятые ячейки</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{data.storageUtilization?.free || 0}</div>
            <div className="text-sm text-gray-600">Свободные ячейки</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-600">{data.storageUtilization?.total || 0}</div>
            <div className="text-sm text-gray-600">Всего ячеек</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div 
              className="bg-blue-500 h-4 rounded-full flex items-center justify-center text-white text-xs font-medium"
              style={{ 
                width: `${((data.storageUtilization?.occupied || 0) / (data.storageUtilization?.total || 1)) * 100}%` 
              }}
            >
              {Math.round(((data.storageUtilization?.occupied || 0) / (data.storageUtilization?.total || 1)) * 100)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;