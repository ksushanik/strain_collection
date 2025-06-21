import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus, Trash2 } from 'lucide-react';
import apiService from '../services/api';
import type { Strain, StrainFilters, StrainsListResponse, PaginationInfo } from '../types';
import AddStrainForm from '../components/AddStrainForm';
import EditStrainForm from '../components/EditStrainForm';
import Pagination from '../components/Pagination';
import AdvancedFilters from '../components/AdvancedFilters';
import type { FilterGroup } from '../components/AdvancedFilters';
import { 
  convertAdvancedFiltersToAPI, 
  saveFiltersToStorage, 
  loadFiltersFromStorage,
  getFiltersDescription,
  countActiveFilters
} from '../utils/advancedFilters';

const Strains: React.FC = () => {
  const navigate = useNavigate();
  const [strains, setStrains] = useState<Strain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<StrainFilters>({});
  const [advancedFilterGroups, setAdvancedFilterGroups] = useState<FilterGroup[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({
    total: 0,
    shown: 0,
    page: 1,
    limit: 50,
    total_pages: 0,
    has_next: false,
    has_previous: false,
    offset: 0
  });
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingStrainId, setEditingStrainId] = useState<number | null>(null);
  const [deletingStrain, setDeletingStrain] = useState<{ id: number; short_code: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchStrains = async () => {
    setLoading(true);
    try {
      // Объединяем обычные фильтры с расширенными
      const advancedFilters = convertAdvancedFiltersToAPI(advancedFilterGroups, 'strains');
      const currentFilters = { 
        ...filters, 
        ...advancedFilters,
        search: searchTerm || undefined 
      };
      
      const response: StrainsListResponse = await apiService.getStrains(currentFilters);
      setStrains(response.strains);
      setPagination(response.pagination);
    } catch (err) {
      setError('Ошибка загрузки штаммов');
      console.error('Error fetching strains:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка сохраненных фильтров при инициализации
  useEffect(() => {
    const savedFilters = loadFiltersFromStorage('strains');
    if (savedFilters.length > 0) {
      setAdvancedFilterGroups(savedFilters);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchStrains();
    }, 300); // Debounce 300ms
    
    return () => clearTimeout(timeoutId);
  }, [searchTerm, filters, advancedFilterGroups]);

  const handleFilterChange = (key: keyof StrainFilters, value: string) => {
    const newFilters = { ...filters, [key]: value || undefined, page: 1 };
    setFilters(newFilters);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters({});
    setAdvancedFilterGroups([]);
  };

  // Обработчики для расширенных фильтров
  const handleAdvancedFiltersChange = (filterGroups: FilterGroup[]) => {
    setAdvancedFilterGroups(filterGroups);
    // Автоматически сохраняем фильтры
    saveFiltersToStorage(filterGroups, 'strains');
    // Сбрасываем пагинацию на первую страницу
    setFilters(prev => ({ ...prev, page: 1 }));
  };

  const handleAdvancedFiltersReset = () => {
    setAdvancedFilterGroups([]);
    saveFiltersToStorage([], 'strains');
  };

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page });
  };

  const handleAddStrain = () => {
    setShowAddForm(true);
  };

  const handleAddStrainSuccess = (_newStrain: any) => {
    // Обновляем список штаммов
    fetchStrains();
    // Закрываем форму после успешного создания
    setTimeout(() => {
      setShowAddForm(false);
    }, 2000); // Даем время показать сообщение об успехе
  };

  const handleAddStrainCancel = () => {
    setShowAddForm(false);
  };

  const handleEditStrain = (strainId: number) => {
    setEditingStrainId(strainId);
  };

  const handleEditStrainSuccess = (_updatedStrain: Strain) => {
    // Обновляем список штаммов
    fetchStrains();
    // Закрываем форму после успешного обновления
    setTimeout(() => {
      setEditingStrainId(null);
    }, 2000); // Даем время показать сообщение об успехе
  };

  const handleEditStrainCancel = () => {
    setEditingStrainId(null);
  };

  const handleDeleteStrain = (strain: Strain) => {
    setDeletingStrain({ id: strain.id, short_code: strain.short_code });
  };

  const confirmDeleteStrain = async () => {
    if (!deletingStrain) return;

    setIsDeleting(true);
    try {
      await apiService.deleteStrain(deletingStrain.id);
      // Обновляем список штаммов
      fetchStrains();
      // Закрываем модальное окно
      setDeletingStrain(null);
    } catch (err: any) {
      setError(err.message || 'Ошибка при удалении штамма');
      console.error('Error deleting strain:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDeleteStrain = () => {
    setDeletingStrain(null);
  };

  const handleRowClick = (strainId: number, event: React.MouseEvent) => {
    // Предотвращаем переход если кликнули по кнопкам действий
    if ((event.target as HTMLElement).closest('button')) {
      return;
    }
    // Используем navigate для перехода на страницу штамма
    navigate(`/strains/${strainId}`);
  };

  if (loading && strains.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Загрузка штаммов...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Add Strain Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-w-4xl w-full max-h-screen overflow-y-auto">
            <AddStrainForm 
              onSuccess={handleAddStrainSuccess}
              onCancel={handleAddStrainCancel}
            />
          </div>
        </div>
      )}

      {/* Edit Strain Form Modal */}
      {editingStrainId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-w-4xl w-full max-h-screen overflow-y-auto">
            <EditStrainForm 
              strainId={editingStrainId}
              onSuccess={handleEditStrainSuccess}
              onCancel={handleEditStrainCancel}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingStrain && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0 w-10 h-10 mx-auto bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Подтвердите удаление
                </h3>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-sm text-gray-600">
                Вы уверены, что хотите удалить штамм <strong>"{deletingStrain.short_code}"</strong>?
              </p>
              <p className="text-sm text-red-600 mt-2">
                Это действие нельзя отменить.
              </p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={cancelDeleteStrain}
                disabled={isDeleting}
                className="btn-secondary"
              >
                Отмена
              </button>
              <button
                onClick={confirmDeleteStrain}
                disabled={isDeleting}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Удаление...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Удалить
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
            <Search className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Штаммы</h1>
            <p className="text-gray-600">
              Управление штаммами микроорганизмов
              <span className="ml-2 text-sm">
                ({pagination.shown} из {pagination.total} штаммов)
              </span>
            </p>
          </div>
        </div>
        <button 
          onClick={handleAddStrain}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить штамм</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Search and Filters */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по названию, коду, таксономии..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                RCAM ID
              </label>
              <input
                type="text"
                placeholder="Фильтр по RCAM ID"
                value={filters.rcam_id || ''}
                onChange={(e) => handleFilterChange('rcam_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Таксономия
              </label>
              <input
                type="text"
                placeholder="Фильтр по таксономии"
                value={filters.taxonomy || ''}
                onChange={(e) => handleFilterChange('taxonomy', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Лимит результатов
              </label>
              <select
                value={filters.limit || '50'}
                onChange={(e) => handleFilterChange('limit', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="25">25 записей</option>
                <option value="50">50 записей</option>
                <option value="100">100 записей</option>
                <option value="500">500 записей</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>Сбросить фильтры</span>
            </button>
          </div>
        </div>

        {/* Расширенные фильтры */}
        <AdvancedFilters
          entityType="strains"
          availableFields={[]}
          onFiltersChange={handleAdvancedFiltersChange}
          onReset={handleAdvancedFiltersReset}
        />
      </div>

      {/* Results Count and Active Filters */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Найдено штаммов: <span className="font-medium">{pagination.total}</span>
            {pagination.total !== pagination.shown && (
              <span className="text-gray-500 ml-1">
                (показано {pagination.shown})
              </span>
            )}
            {countActiveFilters(advancedFilterGroups) > 0 && (
              <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                {countActiveFilters(advancedFilterGroups)} активных фильтров
              </span>
            )}
          </p>
          {strains.length > 0 && (
            <p className="text-sm text-green-600">
              💡 Нажмите на строку для просмотра деталей
            </p>
          )}
        </div>
        
        {/* Описание активных фильтров */}
        {advancedFilterGroups.length > 0 && (
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded-lg border">
            <span className="font-medium">Активные фильтры:</span> {getFiltersDescription(advancedFilterGroups)}
          </div>
        )}
      </div>

      {/* Strains Table */}
      <div className="w-full max-w-full bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Код
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Идентификатор
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Таксономия rRNA
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  RCAM ID
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Альтернативное название
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {strains.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <Search className="w-12 h-12 text-gray-300" />
                      <p className="text-gray-500">
                        {loading ? 'Загрузка штаммов...' : 'Штаммы не найдены'}
                      </p>
                      {!loading && (
                        <button
                          onClick={handleAddStrain}
                          className="text-green-600 hover:text-green-800 text-sm"
                        >
                          Добавить первый штамм
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                strains.map((strain) => (
                  <tr 
                    key={strain.id} 
                    className="hover:bg-blue-50 cursor-pointer transition-colors duration-150"
                    onClick={(e) => handleRowClick(strain.id, e)}
                    title="Нажмите для просмотра деталей штамма"
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {strain.short_code}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900 max-w-40 truncate" title={strain.identifier}>
                        {strain.identifier}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900 max-w-48 truncate" title={strain.rrna_taxonomy}>
                        {strain.rrna_taxonomy}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {strain.rcam_collection_id || '-'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900 max-w-40 truncate" title={strain.name_alt || '-'}>
                        {strain.name_alt || '-'}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {pagination.total > pagination.limit && (
          <div className="bg-gray-50 border-t border-gray-200 px-4 py-3">
            <Pagination
              pagination={pagination}
              onPageChange={handlePageChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Strains; 