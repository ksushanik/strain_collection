import React, { useState, useEffect, useCallback } from 'react';
import {
  Package,
  Search,
  Plus,
  Loader2,
  ChevronDown,
  ChevronRight,
  X,
  AlertTriangle,
  MoreVertical,
  Edit3,
  Trash2,
  LayoutGrid,
  CheckSquare,
  Percent
} from 'lucide-react';
import apiService from '../services/api';
import type { StorageCell, BoxDetailResponse, UpdateBoxData, StorageSummaryResponse } from '../types';

interface StorageBoxState {
  box_id: string;
  rows: number;
  cols: number;
  description?: string;
  cells?: StorageCell[];
  occupied: number;
  total: number;
  loading?: boolean;
  expanded?: boolean;
  showMenu?: boolean;
  detailData?: BoxDetailResponse;
}

interface NewBoxData {
  rows: number;
  cols: number;
  description?: string;
}

const Storage: React.FC = () => {
  const [storageData, setStorageData] = useState<StorageBoxState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddBox, setShowAddBox] = useState(false);
  const [newBox, setNewBox] = useState<NewBoxData>({ rows: 10, cols: 10 });
  const [summary, setSummary] = useState<StorageSummaryResponse | null>(null);

  // Состояния для редактирования бокса
  const [editingBox, setEditingBox] = useState<string | null>(null);
  const [editBoxData, setEditBoxData] = useState<UpdateBoxData>({ description: '' });
  const [editBoxLoading, setEditBoxLoading] = useState(false);
  const [editBoxError, setEditBoxError] = useState<string | null>(null);

  // Состояния для удаления бокса
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ boxId: string; force: boolean } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleBoxClick = async (boxId: string) => {
    setStorageData(prev => prev.map(box => {
      if (box.box_id === boxId) {
        const newExpanded = !box.expanded;
        if (newExpanded && !box.detailData) {
          // Загружаем детальную информацию
          loadBoxDetail(boxId);
          return { ...box, expanded: newExpanded, loading: true };
        }
        return { ...box, expanded: newExpanded };
      }
      return box;
    }));
  };

  const loadBoxDetail = async (boxId: string) => {
    try {
      const detailData = await apiService.getBoxDetail(boxId);
      setStorageData(prev => prev.map(box =>
        box.box_id === boxId
          ? { ...box, detailData, loading: false }
          : box
      ));
    } catch (error) {
      console.error('Error loading box detail:', error);
      setStorageData(prev => prev.map(box =>
        box.box_id === boxId
          ? { ...box, loading: false }
          : box
      ));
    }
  };

  const refreshStorageData = useCallback(async () => {
    try {
      setLoading(true);
      // параллельно загружаем сводную статистику
      const [boxesResp, summaryResp] = await Promise.all([
        apiService.getBoxes(),
        apiService.getStorageSummary()
      ]);

      setSummary(summaryResp);
      const response = boxesResp;
      
      const boxesWithState: StorageBoxState[] = response.boxes.map(box => ({
        box_id: box.box_id,
        rows: box.rows || 8,
        cols: box.cols || 12,
        description: box.description || '',
        occupied: box.occupied || 0,
        total: box.total || 0,
        expanded: false,
        loading: false,
        cells: undefined,
        showMenu: false
      }));
      
      setStorageData(boxesWithState);
      setError(null);
    } catch (err) {
      console.error('Error fetching storage data:', err);
      setError('Ошибка загрузки данных о хранении');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshStorageData();
  }, [refreshStorageData]);

  // Закрыть все меню при клике вне них
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.relative')) {
        setStorageData(prev => prev.map(box => ({ ...box, showMenu: false })));
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleCreateBox = async () => {
    try {
      await apiService.createBox(newBox);
      setShowAddBox(false);
      setNewBox({ rows: 10, cols: 10 });
      await refreshStorageData();
    } catch (err) {
      console.error('Error creating box:', err);
      alert('Ошибка создания бокса');
    }
  };

  // Переключение контекстного меню
  const toggleBoxMenu = useCallback((boxId: string) => {
    setStorageData(prev => prev.map(box =>
      box.box_id === boxId
        ? { ...box, showMenu: !box.showMenu }
        : { ...box, showMenu: false } // Закрываем другие меню
    ));
  }, []);

  // Начать редактирование бокса
  const startEditBox = useCallback(async (boxId: string) => {
    try {
      const boxDetails = await apiService.getBoxDetails(boxId);
      setEditingBox(boxId);
      setEditBoxData({ description: boxDetails.description || '' });
      setEditBoxError(null);
      // Закрываем меню
      setStorageData(prev => prev.map(box => ({ ...box, showMenu: false })));
    } catch (err) {
      console.error('Error loading box details for editing:', err);
      setEditBoxError('Ошибка загрузки данных бокса');
    }
  }, []);

  // Сохранить изменения бокса
  const saveBoxEdit = useCallback(async () => {
    if (!editingBox) return;

    try {
      setEditBoxLoading(true);
      setEditBoxError(null);
      
      await apiService.updateBox(editingBox, editBoxData);
      
      // Обновляем локальные данные
      setStorageData(prev => prev.map(box =>
        box.box_id === editingBox
          ? { ...box, description: editBoxData.description }
          : box
      ));
      
      setEditingBox(null);
      setEditBoxData({ description: '' });
    } catch (err: any) {
      console.error('Error updating box:', err);
      setEditBoxError(err.response?.data?.error || 'Ошибка обновления бокса');
    } finally {
      setEditBoxLoading(false);
    }
  }, [editingBox, editBoxData]);

  // Отменить редактирование
  const cancelBoxEdit = useCallback(() => {
    setEditingBox(null);
    setEditBoxData({ description: '' });
    setEditBoxError(null);
  }, []);

  // Начать удаление бокса
  const startDeleteBox = useCallback((boxId: string) => {
    setDeleteConfirmation({ boxId, force: false });
    // Закрываем меню
    setStorageData(prev => prev.map(box => ({ ...box, showMenu: false })));
  }, []);

  // Подтвердить удаление бокса
  const confirmDeleteBox = useCallback(async () => {
    if (!deleteConfirmation) return;

    try {
      setDeleteLoading(true);
      
      await apiService.deleteBox(deleteConfirmation.boxId, deleteConfirmation.force);

      // После успешного удаления перезагружаем данные и статистику
      await refreshStorageData();

      setDeleteConfirmation(null);
    } catch (err: any) {
      console.error('Error deleting box:', err);
      if (err.response?.status === 400 && err.response?.data?.error?.includes('занятые ячейки')) {
        // Предлагаем принудительное удаление
        setDeleteConfirmation(prev => prev ? { ...prev, force: true } : null);
      } else {
        alert(err.response?.data?.error || 'Ошибка удаления бокса');
        setDeleteConfirmation(null);
      }
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteConfirmation, refreshStorageData]);

  const filteredBoxes = storageData.filter(box =>
    box.box_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (box.description && box.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Загрузка данных о хранении...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Ошибка загрузки</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={refreshStorageData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Хранилище</h1>
          {summary && (
            <p className="text-sm text-gray-500 mt-1">
              Управление системой хранения образцов ({summary.occupied_cells} из {summary.total_cells} ячеек заняты)
            </p>
          )}
        </div>
        <button
          onClick={() => setShowAddBox(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 self-start sm:self-auto"
        >
          <Plus className="w-5 h-5 mr-2" />
          Добавить бокс
        </button>
      </div>

      {summary && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white shadow rounded-lg p-4 text-center flex flex-col items-center">
              <Package className="w-6 h-6 text-blue-500 mb-1" />
              <div className="text-sm text-gray-500">Всего боксов</div>
              <div className="text-2xl font-bold text-gray-800">{summary.total_boxes}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4 text-center flex flex-col items-center">
              <LayoutGrid className="w-6 h-6 text-indigo-500 mb-1" />
              <div className="text-sm text-gray-500">Всего ячеек</div>
              <div className="text-2xl font-bold text-gray-800">{summary.total_cells}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4 text-center flex flex-col items-center">
              <CheckSquare className="w-6 h-6 text-emerald-500 mb-1" />
              <div className="text-sm text-gray-500">Занятые ячейки</div>
              <div className="text-2xl font-bold text-gray-800">{summary.occupied_cells}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4 text-center flex flex-col items-center">
              <Percent className="w-6 h-6 text-orange-500 mb-1" />
              <div className="text-sm text-gray-500">Заполненность</div>
              <div className="text-2xl font-bold text-gray-800">
                {Math.round((summary.occupied_cells / summary.total_cells) * 1000) / 10}%
              </div>
            </div>
          </div>
          {/* Progress bar */}
          <div className="w-full h-3 bg-gray-200 rounded mb-8 overflow-hidden">
            <div
              className="h-full bg-orange-500"
              style={{ width: `${(summary.occupied_cells / summary.total_cells) * 100}%` }}
            ></div>
          </div>
        </>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <input
          type="text"
          placeholder="Поиск по ID бокса или описанию..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Boxes Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredBoxes.map((box) => {
          const title = box.box_id.startsWith('Бокс') ? box.box_id : `Бокс ${box.box_id}`;
          const occupancyPercentage = box.total > 0 ? (box.occupied / box.total) * 100 : 0;
          const colorClass =
            occupancyPercentage === 0 ? 'bg-green-500' :
            occupancyPercentage < 20 ? 'bg-green-400' :
            occupancyPercentage < 40 ? 'bg-lime-400' :
            occupancyPercentage < 60 ? 'bg-yellow-400' :
            occupancyPercentage < 80 ? 'bg-orange-500' :
            occupancyPercentage < 100 ? 'bg-red-500' :
            'bg-red-700';

          return (
            <div key={box.box_id} className="bg-white shadow rounded-lg p-4 relative flex flex-col">
              {/* Card Header */}
              <div className="flex items-center space-x-2 mb-2">
                <Package className="w-6 h-6 text-blue-500" />
                <div className="text-sm font-semibold text-gray-800 truncate max-w-full">{title}</div>
                <div className="text-xs text-gray-500 ml-auto">{box.rows}×{box.cols}</div>
              </div>
              {/* Stats */}
              <div className="flex justify-between text-xs text-gray-600 mb-2">
                <span>Занято: <span className="font-semibold text-gray-800">{box.occupied}</span></span>
                <span>Свободно: <span className="font-semibold text-gray-800">{box.total - box.occupied}</span></span>
              </div>
              {/* Progress */}
              <div className="w-full h-2 bg-gray-200 rounded">
                <div
                  className={`h-full rounded ${colorClass}`}
                  style={{ width: `${Math.round(occupancyPercentage)}%` }}
                ></div>
              </div>
              {/* Expand Button & Menu */}
              <div className="absolute top-2 right-2 flex items-center space-x-1">
                {box.loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                
                {/* Контекстное меню */}
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleBoxMenu(box.box_id);
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                  >
                    <MoreVertical className="w-4 h-4 text-gray-500" />
                  </button>
                  
                  {box.showMenu && (
                    <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[150px]">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditBox(box.box_id);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <Edit3 className="w-4 h-4" />
                        <span>Редактировать</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startDeleteBox(box.box_id);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 text-red-600 flex items-center space-x-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Удалить</span>
                      </button>
                    </div>
                      )}
                    </div>

                  <button
                    onClick={() => handleBoxClick(box.box_id)}
                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    disabled={box.loading}
                  >
                    {box.loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : box.expanded ? (
                      <ChevronDown className="w-5 h-5" />
                    ) : (
                      <ChevronRight className="w-5 h-5" />
                    )}
                  </button>
                </div>

                {/* Expanded Box Detail */}
                {box.expanded && box.detailData && (
                  <div className="mt-6 border-t pt-6">
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-700">Сетка ячеек</h4>
                        <div className="flex items-center space-x-4 text-xs">
                          <div className="flex items-center space-x-1">
                            <div className="w-3 h-3 bg-blue-500 rounded"></div>
                            <span>Занятые</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <div className="w-3 h-3 bg-yellow-400 rounded"></div>
                            <span>Свободные</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Cells Grid */}
                    <div className="grid gap-1 max-w-md mx-auto" style={{
                      gridTemplateColumns: `repeat(${box.detailData.cols || 1}, minmax(0, 1fr))`
                    }}>
                      {box.detailData.cells_grid.flat().map((cell) => (
                        <div
                          key={`${cell.row}-${cell.col}`}
                          className={`
                            aspect-square text-xs flex items-center justify-center rounded border relative group
                            ${cell.is_occupied
                              ? 'bg-blue-500 text-white border-blue-600'
                              : 'bg-yellow-400 text-gray-800 border-yellow-500'
                            }
                            hover:opacity-80 transition-opacity cursor-pointer
                          `}
                          title={`${cell.cell_id}${cell.sample_info ? ` - Штамм ${cell.sample_info.strain_number || cell.sample_info.strain_id}` : ' - Свободно'}`}
                        >
                          {cell.cell_id}
                          
                          {/* Custom Tooltip */}
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                            {cell.cell_id}
                            {cell.sample_info ? ` - Штамм ${cell.sample_info.strain_number || cell.sample_info.strain_id}` : ' - Свободно'}
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Legend and Stats */}
                    <div className="mt-4 text-xs text-gray-600 text-center">
                      <p>
                        Всего ячеек: {box.detailData.total_cells || 0} |
                        Занято: {box.detailData.occupied_cells || 0} |
                        Свободно: {box.detailData.free_cells || 0}
                      </p>
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
            {searchTerm ? 'Попробуйте изменить критерии поиска' : 'Создайте первый бокс для хранения образцов'}
          </p>
        </div>
      )}

      {/* Add Box Modal */}
      {showAddBox && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Создать новый бокс</h3>
              <button
                onClick={() => setShowAddBox(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 text-blue-700 p-3 rounded text-sm">
                <strong>Автоматическая нумерация:</strong> Номер бокса будет присвоен автоматически (Бокс 1, Бокс 2, и т.д.)
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ряды
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="26"
                    value={newBox.rows}
                    onChange={(e) => setNewBox({ ...newBox, rows: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Колонки
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    value={newBox.cols}
                    onChange={(e) => setNewBox({ ...newBox, cols: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Описание (опционально)
                </label>
                <textarea
                  value={newBox.description || ''}
                  onChange={(e) => setNewBox({ ...newBox, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Описание бокса..."
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddBox(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={handleCreateBox}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно редактирования бокса */}
      {editingBox && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md rounded-lg shadow-lg p-6 space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Редактировать бокс {editingBox}</h2>

            {editBoxError && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">
                {editBoxError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
                <textarea
                  value={editBoxData.description || ''}
                  onChange={(e) => setEditBoxData({ description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Введите описание бокса..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={cancelBoxEdit}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Отмена
              </button>
              <button
                disabled={editBoxLoading}
                onClick={saveBoxEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 disabled:opacity-50"
              >
                {editBoxLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>Сохранить</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно подтверждения удаления */}
      {deleteConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md rounded-lg shadow-lg p-6 space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">
              {deleteConfirmation.force ? 'Принудительное удаление' : 'Подтвердите удаление'}
            </h2>
            
            <div className="space-y-3">
              <p className="text-gray-600">
                {deleteConfirmation.force 
                  ? `Бокс ${deleteConfirmation.boxId} содержит занятые ячейки. Принудительное удаление освободит все образцы. Продолжить?`
                  : `Вы уверены, что хотите удалить бокс ${deleteConfirmation.boxId}?`
                }
              </p>
              
              {deleteConfirmation.force && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-sm">
                  <strong>Внимание:</strong> Все образцы в боксе будут освобождены.
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={() => setDeleteConfirmation(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Отмена
              </button>
              <button
                disabled={deleteLoading}
                onClick={confirmDeleteBox}
                className={`px-4 py-2 text-white rounded-lg flex items-center space-x-2 disabled:opacity-50 ${
                  deleteConfirmation.force 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {deleteLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                <span>{deleteConfirmation.force ? 'Принудительно удалить' : 'Удалить'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Storage;