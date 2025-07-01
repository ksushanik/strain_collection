import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Plus } from 'lucide-react';
import apiService from '../services/api';
import type { Strain, StrainFilters, StrainsListResponse, PaginationInfo } from '../types';
import AddStrainForm from '../components/AddStrainForm';
import Pagination from '../components/Pagination';
import AdvancedFilters from '../components/AdvancedFilters';
import BulkOperationsPanel from '../components/BulkOperationsPanel';
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
  const [filters, setFilters] = useState<StrainFilters>({
    page: 1,
    limit: 50
  });
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    total_pages: 1,
    has_next: false,
    has_previous: false,
    total: 0,
    shown: 0,
    limit: 50,
    offset: 0
  });
  const [selectedStrainIds, setSelectedStrainIds] = useState<number[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [advancedFilterGroups, setAdvancedFilterGroups] = useState<FilterGroup[]>([]);

  // Отладочные логи
  console.log('Component render - pagination:', pagination);
  console.log('Component render - filters:', filters);

  const fetchStrains = useCallback(async () => {
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
  }, [searchTerm, filters, advancedFilterGroups]);

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
  }, [fetchStrains]);

  const handleFilterChange = useCallback((key: keyof StrainFilters, value: string) => {
    const newFilters = { ...filters, [key]: value || undefined, page: 1 };
    setFilters(newFilters);
  }, [filters]);

  const clearFilters = useCallback(() => {
    setSearchTerm('');
    setFilters({});
    setAdvancedFilterGroups([]);
  }, []);

  // Обработчики для расширенных фильтров
  const handleAdvancedFiltersChange = useCallback((filterGroups: FilterGroup[]) => {
    setAdvancedFilterGroups(filterGroups);
    // Автоматически сохраняем фильтры
    saveFiltersToStorage(filterGroups, 'strains');
    // Сбрасываем пагинацию на первую страницу только если изменились сами фильтры
    setFilters(prev => {
      if (prev.page !== 1) {
        return { ...prev, page: 1 };
      }
      return prev;
    });
  }, []);

  const handleAdvancedFiltersReset = useCallback(() => {
    setAdvancedFilterGroups([]);
    saveFiltersToStorage([], 'strains');
  }, []);

  const handlePageChange = useCallback((page: number) => {
    console.log('handlePageChange called with page:', page);
    const newFilters = { ...filters, page };
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page }));
    
    // Напрямую вызываем fetchStrains с обновленными фильтрами
    const fetchStrainsWithPage = async () => {
      console.log('fetchStrainsWithPage started');
      setLoading(true);
      try {
        // Объединяем обычные фильтры с расширенными
        const advancedFilters = convertAdvancedFiltersToAPI(advancedFilterGroups, 'strains');
        console.log('advancedFilters:', advancedFilters);
        const currentFilters = { 
          ...newFilters, 
          ...advancedFilters,
          search: searchTerm || undefined 
        };
        console.log('currentFilters:', currentFilters);
        
        const response: StrainsListResponse = await apiService.getStrains(currentFilters);
        console.log('API response:', response);
        setStrains(response.strains);
        setPagination(response.pagination);
      } catch (err) {
        console.error('Error in fetchStrainsWithPage:', err);
        setError('Ошибка загрузки штаммов');
        console.error('Error fetching strains:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStrainsWithPage();
  }, [filters, advancedFilterGroups, searchTerm]);

  // Обработчики для массовых операций
  const handleSelectStrain = useCallback((strainId: number) => {
    setSelectedStrainIds(prev => 
      prev.includes(strainId)
        ? prev.filter(id => id !== strainId)
        : [...prev, strainId]
    );
  }, []);

  const handleSelectAllStrains = useCallback(() => {
    if (selectedStrainIds.length === strains.length) {
      setSelectedStrainIds([]);
    } else {
      setSelectedStrainIds(strains.map(strain => strain.id));
    }
  }, [selectedStrainIds, strains]);

  const handleClearSelection = useCallback(() => {
    setSelectedStrainIds([]);
  }, []);

  const handleAddStrain = useCallback(() => {
    setShowAddForm(true);
  }, []);

  const handleAddStrainSuccess = useCallback((_newStrain: any) => {
    // Обновляем список штаммов
    fetchStrains();
    // Закрываем форму после успешного создания
    setTimeout(() => {
      setShowAddForm(false);
    }, 2000); // Даем время показать сообщение об успехе
  }, [fetchStrains]);

  const handleAddStrainCancel = useCallback(() => {
    setShowAddForm(false);
  }, []);

  const handleRowClick = useCallback((strainId: number, event: React.MouseEvent) => {
    // Предотвращаем переход если кликнули по кнопкам действий или чекбоксу
    if ((event.target as HTMLElement).closest('button') || 
        (event.target as HTMLElement).closest('input[type="checkbox"]')) {
      return;
    }
    // Используем navigate для перехода на страницу штамма
    navigate(`/strains/${strainId}`);
  }, [navigate]);

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
          onFiltersChange={handleAdvancedFiltersChange}
          onReset={handleAdvancedFiltersReset}
        />
      </div>

      {/* Bulk Operations Panel */}
      {selectedStrainIds.length > 0 && (
        <BulkOperationsPanel
          selectedIds={selectedStrainIds}
          allSamples={[]} // Не используется для штаммов
          allStrains={strains}
          entityType="strains"
          onClearSelection={handleClearSelection}
          onRefresh={fetchStrains}
          filters={filters}
          totalCount={pagination.total}
        />
      )}

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
            {selectedStrainIds.length > 0 && (
              <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                Выбрано: {selectedStrainIds.length}
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
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedStrainIds.length === strains.length && strains.length > 0}
                    onChange={handleSelectAllStrains}
                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                </th>
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
                  <td colSpan={6} className="px-6 py-12 text-center">
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
                      <input
                        type="checkbox"
                        checked={selectedStrainIds.includes(strain.id)}
                        onChange={() => handleSelectStrain(strain.id)}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
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