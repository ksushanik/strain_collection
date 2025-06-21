import React, { useState, useEffect } from 'react';
import { BarChart3, PieChart, TrendingUp, Users, Beaker, Database, MapPin, Calendar } from 'lucide-react';
import apiService from '../services/api';
import type { Sample, Storage, StorageBox } from '../types';

interface AnalyticsData {
  totalSamples: number;
  totalStrains: number;
  totalStorage: number;
  sourceTypeDistribution: { [key: string]: number };
  strainDistribution: { [key: string]: number };
  monthlyTrends: { month: string; count: number }[];
  characteristicsStats: {
    has_photo: number;
    is_identified: number;
    has_antibiotic_activity: number;
    has_genome: number;
    has_biochemistry: number;
    seq_status: number;
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
      
      // Загружаем данные параллельно
      const [statsResponse, samplesResponse, storageResponse] = await Promise.all([
        apiService.getStats(),
        apiService.getSamples({ limit: 1000 }), // Увеличиваем лимит для более точной аналитики
        apiService.getStorage()
      ]);

      const samples = samplesResponse.samples || [];
      
      // Анализируем распределение по типам источников
      const sourceTypeDistribution: { [key: string]: number } = {};
      samples.forEach(sample => {
        if (sample.source?.source_type) {
          sourceTypeDistribution[sample.source.source_type] = 
            (sourceTypeDistribution[sample.source.source_type] || 0) + 1;
        }
      });

      // Анализируем распределение по штаммам (топ 10)
      const strainCounts: { [key: string]: number } = {};
      samples.forEach(sample => {
        if (sample.strain?.short_code) {
          strainCounts[sample.strain.short_code] = 
            (strainCounts[sample.strain.short_code] || 0) + 1;
        }
      });
      
      const topStrains = Object.entries(strainCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10)
        .reduce((acc, [strain, count]) => ({ ...acc, [strain]: count }), {});

      // Анализируем временные тренды (последние 12 месяцев)
      const monthlyTrends = generateMonthlyTrends(samples);

      // Используем данные из API статистики для характеристик (более точные данные)
      const characteristicsStats = {
        has_photo: statsResponse.samples_analysis?.with_photo || 0,
        is_identified: statsResponse.samples_analysis?.identified || 0,
        has_antibiotic_activity: statsResponse.samples_analysis?.with_antibiotic_activity || 0,
        has_genome: statsResponse.samples_analysis?.with_genome || 0,
        has_biochemistry: statsResponse.samples_analysis?.with_biochemistry || 0,
        seq_status: statsResponse.samples_analysis?.sequenced || 0,
      };

      // Анализируем утилизацию хранилища
      // Извлекаем все ячейки из всех ящиков
      const allCells: Storage[] = [];
      if (storageResponse.boxes) {
        storageResponse.boxes.forEach((box: StorageBox) => {
          if (box.cells) {
            allCells.push(...box.cells);
          }
        });
      }
      
      const occupiedCells = allCells.filter((cell: Storage) => 
        cell.occupied === true && !cell.is_free_cell
      ).length;
      const freeCells = allCells.filter((cell: Storage) => 
        cell.is_free_cell === true || cell.occupied === false
      ).length;
      
      const storageUtilization = {
        occupied: occupiedCells,
        free: freeCells,
        total: allCells.length
      };

      // Получаем значения из статистики с защитой от undefined
      const totalSamples = statsResponse.counts.samples || samples.length;
      const totalStrains = statsResponse.counts.strains || 0;
      const totalStorage = statsResponse.counts.storage_units || allCells.length;

      setData({
        totalSamples,
        totalStrains,
        totalStorage,
        sourceTypeDistribution,
        strainDistribution: topStrains,
        monthlyTrends,
        characteristicsStats,
        storageUtilization
      });

    } catch (err: any) {
      console.error('Ошибка загрузки аналитики:', err);
      setError(err.message || 'Ошибка загрузки данных аналитики');
    } finally {
      setLoading(false);
    }
  };

  const generateMonthlyTrends = (samples: Sample[]) => {
    const months = [];
    const now = new Date();
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthKey = date.toISOString().slice(0, 7); // YYYY-MM
      const monthName = date.toLocaleDateString('ru-RU', { 
        month: 'short', 
        year: 'numeric' 
      });
      
      const count = samples.filter(sample => {
        if (!sample.created_at) return false;
        const sampleDate = new Date(sample.created_at);
        return sampleDate.toISOString().slice(0, 7) === monthKey;
      }).length;
      
      months.push({ month: monthName, count });
    }
    
    return months;
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
            {Object.entries(data.strainDistribution || {}).map(([strain, count], index) => {
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
            {[
              { key: 'has_photo', label: 'С фотографиями', icon: '📷' },
              { key: 'is_identified', label: 'Идентифицированные', icon: '🔍' },
              { key: 'has_antibiotic_activity', label: 'С АБ активностью', icon: '💊' },
              { key: 'has_genome', label: 'С геномными данными', icon: '🧬' },
              { key: 'has_biochemistry', label: 'С биохимией', icon: '⚗️' },
              { key: 'seq_status', label: 'Секвенированные', icon: '🔬' },
            ].map(({ key, label, icon }) => {
              const count = data.characteristicsStats?.[key as keyof typeof data.characteristicsStats] || 0;
              const percentage = (count / (data.totalSamples || 1) * 100).toFixed(1);
              return (
                <div key={key} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{icon}</span>
                    <span className="text-sm text-gray-700">{label}</span>
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