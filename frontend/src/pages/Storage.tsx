import React, { useState, useEffect, useCallback } from 'react';
import { 
  Package, 
  Search, 
  Grid3X3,
  MapPin,
  TestTube,
  Plus,
  Loader2,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import apiService from '../services/api';
import type { StorageListResponse } from '../types';

interface StorageBoxState {
  box_id: string;
  cells?: Array<{
    cell_id: string;
    storage_id: number;
    occupied: boolean;
    sample_id?: number;
    strain_code?: string;
    is_free_cell?: boolean;
  }>;
  occupied: number;
  total: number;
  loading?: boolean;
  expanded?: boolean;
}

const Storage: React.FC = () => {
  const [storageData, setStorageData] = useState<StorageBoxState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    total_boxes: 0,
    total_cells: 0,
    occupied_cells: 0
  });

  // Загружаем сначала только краткую информацию
  useEffect(() => {
    const fetchStorageSummary = async () => {
      try {
        setLoading(true);
        const response: StorageListResponse = await apiService.getStorageSummary();
        
        // Инициализируем боксы без деталей ячеек
        const boxesWithState: StorageBoxState[] = response.boxes.map(box => ({
          box_id: box.box_id,
          occupied: box.occupied,
          total: box.total,
          expanded: false,
          loading: false,
          cells: undefined
        }));
        
        setStorageData(boxesWithState);
        setStats({
          total_boxes: response.total_boxes,
          total_cells: response.total_cells,
          occupied_cells: response.occupied_cells
        });
      } catch (err) {
        setError('Ошибка загрузки информации о хранилище');
        console.error('Error fetching storage summary:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStorageSummary();
  }, []);

  // Ленивая загрузка деталей бокса
  const loadBoxDetails = useCallback(async (boxId: string) => {
    try {
      // Устанавливаем состояние загрузки для конкретного бокса
      setStorageData(prev => prev.map(box => 
        box.box_id === boxId 
          ? { ...box, loading: true }
          : box
      ));

      const boxDetails = await apiService.getBoxDetails(boxId);
      
      // Обновляем данные бокса
      setStorageData(prev => prev.map(box => 
        box.box_id === boxId 
          ? { 
              ...box, 
              cells: boxDetails.cells,
              loading: false,
              expanded: true
            }
          : box
      ));
    } catch (err) {
      console.error(`Error loading box ${boxId} details:`, err);
      // Убираем состояние загрузки при ошибке
      setStorageData(prev => prev.map(box => 
        box.box_id === boxId 
          ? { ...box, loading: false }
          : box
      ));
    }
  }, []);

  // Переключение разворачивания бокса
  const toggleBoxExpansion = useCallback(async (boxId: string) => {
    const box = storageData.find(b => b.box_id === boxId);
    if (!box) return;

    if (!box.expanded && !box.cells) {
      // Загружаем детали при первом разворачивании
      await loadBoxDetails(boxId);
    } else {
      // Просто переключаем состояние
      setStorageData(prev => prev.map(b => 
        b.box_id === boxId 
          ? { ...b, expanded: !b.expanded }
          : b
      ));
    }
  }, [storageData, loadBoxDetails]);

  const filteredBoxes = storageData.filter(box => 
    searchTerm === '' || box.box_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getCellVisual = (cell: { cell_id: string; storage_id: number; occupied: boolean; sample_id?: number; strain_code?: string; is_free_cell?: boolean }) => {
    if (cell.occupied) {
      return (
        <div 
          className="w-8 h-8 bg-blue-500 border-2 border-blue-600 rounded flex items-center justify-center cursor-pointer hover:bg-blue-600 transition-colors"
          title={`${cell.cell_id}: ${cell.strain_code || 'Занята'}`}
        >
          <TestTube className="w-4 h-4 text-white" />
        </div>
      );
    }
    if (cell.is_free_cell) {
      return (
        <div 
          className="w-8 h-8 bg-yellow-100 border-2 border-yellow-300 rounded flex items-center justify-center cursor-pointer hover:bg-yellow-200 transition-colors"
          title={`${cell.cell_id}: Помечена как свободная`}
        >
          <span className="text-xs text-yellow-600">{cell.cell_id}</span>
        </div>
      );
    }
    return (
      <div 
        className="w-8 h-8 bg-gray-100 border-2 border-gray-300 rounded flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors"
        title={`${cell.cell_id}: Пустая`}
      >
        <span className="text-xs text-gray-400">{cell.cell_id}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Загрузка хранилища...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
            <Package className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Хранилище</h1>
            <p className="text-gray-600">
              Управление системой хранения образцов
              <span className="ml-2 text-sm">
                ({stats.occupied_cells} из {stats.total_cells} ячеек заняты)
              </span>
            </p>
          </div>
        </div>
        <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2 transition-colors">
          <Plus className="w-4 h-4" />
          <span>Добавить ячейку</span>
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Package className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-500">Всего боксов</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_boxes}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <Grid3X3 className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-500">Всего ячеек</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_cells}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <TestTube className="w-8 h-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-500">Занятые ячейки</p>
              <p className="text-2xl font-bold text-gray-900">{stats.occupied_cells}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <MapPin className="w-8 h-8 text-orange-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-500">Заполненность</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.total_cells > 0 ? Math.round((stats.occupied_cells / stats.total_cells) * 100) : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Performance Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по ID бокса..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <div className="text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
            ⚡ Быстрая загрузка: детали по клику
          </div>
        </div>
      </div>

      {/* Boxes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredBoxes.map((box) => {
          const occupancyPercentage = box.total > 0 ? (box.occupied / box.total) * 100 : 0;
          
          return (
            <div key={box.box_id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {/* Box Header */}
              <div 
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleBoxExpansion(box.box_id)}
            >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Бокс {box.box_id}</h3>
                      <p className="text-sm text-gray-600">
                        {box.occupied}/{box.total} ячеек
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {box.loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                    {box.expanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
              </div>

                {/* Occupancy Bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Заполненность</span>
                    <span>{Math.round(occupancyPercentage)}%</span>
              </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        occupancyPercentage === 0 ? 'bg-gray-300' :
                        occupancyPercentage < 30 ? 'bg-green-500' :
                        occupancyPercentage < 70 ? 'bg-yellow-500' :
                        occupancyPercentage < 100 ? 'bg-orange-500' : 'bg-red-500'
                      }`}
                  style={{ width: `${occupancyPercentage}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Box Details (только если развернут и загружен) */}
              {box.expanded && box.cells && (
                <div className="border-t border-gray-200 p-4">
                  <div className="grid grid-cols-9 gap-1">
                    {box.cells.map((cell) => (
                      <div key={cell.cell_id} className="flex justify-center">
                        {getCellVisual(cell)}
                      </div>
                    ))}
                  </div>
                  
                  {/* Legend для развернутого бокса */}
                  <div className="mt-4 flex flex-wrap gap-4 text-xs">
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-blue-500 rounded"></div>
                      <span>Занятые</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded"></div>
                      <span>Свободные</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-gray-100 border border-gray-300 rounded"></div>
                      <span>Пустые</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredBoxes.length === 0 && (
        <div className="text-center py-12">
          <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Боксы не найдены</h3>
          <p className="text-gray-600">
            Попробуйте изменить критерии поиска или добавить новый бокс.
          </p>
        </div>
      )}
    </div>
  );
};

export default Storage; 