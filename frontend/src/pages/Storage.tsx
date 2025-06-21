import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Search, 
  Filter, 
  Grid3X3,
  MapPin,
  TestTube,
  Plus,
  Info
} from 'lucide-react';
import apiService from '../services/api';

interface StorageBox {
  box_id: string;
  cells: Array<{
    cell_id: string;
    storage_id: number;
    occupied: boolean;
    sample_id?: number;
    strain_code?: string;
    is_free_cell?: boolean;
  }>;
  occupied: number;
  total: number;
}

interface StorageResponse {
  boxes: StorageBox[];
  total_boxes: number;
  total_cells: number;
  occupied_cells: number;
}

const Storage: React.FC = () => {
  const [storageData, setStorageData] = useState<StorageBox[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBox, setSelectedBox] = useState<string | null>(null);
  const [stats, setStats] = useState({
    total_boxes: 0,
    total_cells: 0,
    occupied_cells: 0
  });

  useEffect(() => {
    const fetchStorageData = async () => {
      try {
        setLoading(true);
        const response: StorageResponse = await apiService.getStorage();
        setStorageData(response.boxes);
        setStats({
          total_boxes: response.total_boxes,
          total_cells: response.total_cells,
          occupied_cells: response.occupied_cells
        });
      } catch (err) {
        setError('Ошибка загрузки информации о хранилище');
        console.error('Error fetching storage:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStorageData();
  }, []);

  const filteredBoxes = storageData.filter(box => 
    searchTerm === '' || box.box_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getOccupancyColor = (percentage: number) => {
    if (percentage === 0) return 'bg-gray-100 text-gray-600';
    if (percentage < 30) return 'bg-green-100 text-green-800';
    if (percentage < 70) return 'bg-yellow-100 text-yellow-800';
    if (percentage < 100) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const getCellVisual = (cell: StorageBox['cells'][0]) => {
    if (cell.occupied) {
      return (
        <div className="w-8 h-8 bg-blue-500 border-2 border-blue-600 rounded flex items-center justify-center">
          <TestTube className="w-4 h-4 text-white" />
        </div>
      );
    }
    if (cell.is_free_cell) {
      return (
        <div className="w-8 h-8 bg-yellow-100 border-2 border-yellow-300 rounded flex items-center justify-center">
          <span className="text-xs text-yellow-600">{cell.cell_id}</span>
        </div>
      );
    }
    return (
      <div className="w-8 h-8 bg-gray-100 border-2 border-gray-300 rounded flex items-center justify-center">
        <span className="text-xs text-gray-400">{cell.cell_id}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
        <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2">
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

      {/* Search and Filters */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex gap-4">
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
          <button className="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center space-x-2">
            <Filter className="w-4 h-4" />
            <span>Фильтры</span>
          </button>
        </div>
      </div>

      {/* Storage Boxes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredBoxes.map((box) => {
          const occupancyPercentage = box.total > 0 ? Math.round((box.occupied / box.total) * 100) : 0;
          
          return (
            <div 
              key={box.box_id} 
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedBox(selectedBox === box.box_id ? null : box.box_id)}
            >
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-semibold text-gray-900">
                  Бокс {box.box_id}
                </h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getOccupancyColor(occupancyPercentage)}`}>
                  {occupancyPercentage}%
                </span>
              </div>

              <div className="flex justify-between text-sm text-gray-600 mb-3">
                <span>Занято: {box.occupied}/{box.total}</span>
                <span>Свободно: {box.total - box.occupied}</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${occupancyPercentage}%` }}
                ></div>
              </div>

              {/* Cell Grid Preview */}
              {selectedBox === box.box_id && (
                <div className="mt-4 border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <Grid3X3 className="w-4 h-4 mr-1" />
                    Раскладка ячеек
                  </h4>
                  <div className="grid grid-cols-9 gap-1">
                    {box.cells.map((cell) => (
                      <div 
                        key={cell.cell_id}
                        className="relative group"
                        title={`Ячейка ${cell.cell_id}${
                          cell.occupied 
                            ? ` - Образец #${cell.sample_id}` 
                            : cell.is_free_cell 
                              ? ' - Помечена как свободная' 
                              : ' - Свободна'
                        }`}
                      >
                        {getCellVisual(cell)}
                        {cell.occupied && (
                          <div className="absolute -top-2 -right-2 w-3 h-3 bg-green-500 rounded-full"></div>
                        )}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-blue-500 rounded mr-1"></div>
                      <span>Занятые</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded mr-1"></div>
                      <span>Помечены свободные</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-gray-100 border rounded mr-1"></div>
                      <span>Свободные</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filteredBoxes.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-500">
          <Package className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>Боксы не найдены</p>
          <p className="text-sm">Попробуйте изменить поисковый запрос</p>
        </div>
      )}

      {/* Legend */}
      <div className="card">
        <div className="flex items-center mb-3">
          <Info className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Условные обозначения</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded mr-2"></div>
            <span className="text-gray-600">0-30% заполнено</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded mr-2"></div>
            <span className="text-gray-600">30-70% заполнено</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-orange-100 border border-orange-300 rounded mr-2"></div>
            <span className="text-gray-600">70-100% заполнено</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-100 border border-red-300 rounded mr-2"></div>
            <span className="text-gray-600">100% заполнено</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Storage; 