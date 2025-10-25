import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter, Plus, FlaskConical } from 'lucide-react';
import apiService from '../services/api';
import type { Sample, SampleFilters, SamplesListResponse, PaginationInfo, ReferenceData, StorageBox } from '../types';
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

const Samples: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<SampleFilters>({ page: 1, limit: 50 });
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
  const [selectedSampleIds, setSelectedSampleIds] = useState<number[]>([]);
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [boxesList, setBoxesList] = useState<StorageBox[]>([]);
  const [sourceTypes, setSourceTypes] = useState<{ value: string; label: string }[]>([]);
  const [organismNames, setOrganismNames] = useState<{ value: string; label: string }[]>([]);

  const fetchSamples = useCallback(async () => {
    setLoading(true);
    try {
      // Объединяем обычные фильтры с расширенными
      const advancedFilters = convertAdvancedFiltersToAPI(advancedFilterGroups, 'samples');
      const currentFilters = { 
        ...filters, 
        ...advancedFilters,
        search: searchTerm || undefined
      };
      
      console.log('📡 Fetching samples with filters:', currentFilters);
      const response: SamplesListResponse = await apiService.getSamples(currentFilters);
      console.log('📦 Received pagination:', response.pagination);
      setSamples(response.samples);
      setPagination(response.pagination);
    } catch (err) {
      setError('Ошибка загрузки образцов');
      console.error('Error fetching samples:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, advancedFilterGroups, searchTerm]);

  // Загрузка сохраненных фильтров при инициализации
  useEffect(() => {
    const savedFilters = loadFiltersFromStorage('samples');
    if (savedFilters.length > 0) {
      setAdvancedFilterGroups(savedFilters);
    }
  }, []);

  // Обработка URL параметров при загрузке компонента
  useEffect(() => {
    const strainId = searchParams.get('strain_id');
    if (strainId) {
      setFilters(prev => ({ ...prev, strain_id: parseInt(strainId) }));
    }
  }, [searchParams]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchSamples();
    }, 300);
    
    return () => clearTimeout(timeoutId);
  }, [fetchSamples]);

  const handleFilterChange = (key: keyof SampleFilters, value: string | boolean | number | undefined) => {
    const newFilters = { 
      ...filters, 
      [key]: value === '' || value === null ? undefined : value, 
      page: 1 
    };
    setFilters(newFilters);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters({ page: 1, limit: 50 });
    setAdvancedFilterGroups([]);
  };

  // Обработчики для расширенных фильтров
  const handleAdvancedFiltersChange = useCallback((filterGroups: FilterGroup[]) => {
    setAdvancedFilterGroups(filterGroups);
    // Автоматически сохраняем фильтры
    saveFiltersToStorage(filterGroups, 'samples');
    // Сбрасываем пагинацию на первую страницу только если она не равна 1
    setFilters(prev => prev.page !== 1 ? ({ ...prev, page: 1 }) : prev);
  }, []);

  const handleAdvancedFiltersReset = () => {
    setAdvancedFilterGroups([]);
    saveFiltersToStorage([], 'samples');
  };

  const handlePageChange = useCallback((page: number) => {
    console.log('🔄 Changing page to:', page);
    const newFilters = { ...filters, page };
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page }));
    
    // Напрямую вызываем fetchSamples с обновленными фильтрами - БЕЗ DEBOUNCE!
    const fetchSamplesWithPage = async () => {
      console.log('fetchSamplesWithPage started');
      setLoading(true);
      try {
        // Объединяем обычные фильтры с расширенными
        const advancedFilters = convertAdvancedFiltersToAPI(advancedFilterGroups, 'samples');
        console.log('advancedFilters:', advancedFilters);
        const currentFilters = { 
          ...newFilters, 
          ...advancedFilters,
          search: searchTerm || undefined 
        };
        console.log('currentFilters:', currentFilters);
        
        const response: SamplesListResponse = await apiService.getSamples(currentFilters);
        console.log('API response:', response);
        setSamples(response.samples);
        setPagination(response.pagination);
      } catch (err) {
        console.error('Error in fetchSamplesWithPage:', err);
        setError('Ошибка загрузки образцов');
        console.error('Error fetching samples:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSamplesWithPage();
  }, [filters, advancedFilterGroups, searchTerm]);

  // Обработчики выбора для массовых операций
  const handleSelectSample = (sampleId: number) => {
    setSelectedSampleIds(prev =>
      prev.includes(sampleId) ? prev.filter(id => id !== sampleId) : [...prev, sampleId]
    );
  };

  const handleSelectAllSamples = () => {
    if (selectedSampleIds.length === (samples?.length || 0)) {
      setSelectedSampleIds([]);
    } else {
      setSelectedSampleIds(samples?.map(s => s.id) || []);
    }
  };

  const handleClearSelection = () => {
    setSelectedSampleIds([]);
  };

  const handleRowClick = (sampleId: number, event: React.MouseEvent) => {
    // Предотвращаем переход если кликнули по кнопкам действий
    if ((event.target as HTMLElement).closest('button')) {
      return;
    }
    // Используем navigate для перехода на страницу образца
    navigate(`/samples/${sampleId}`);
  };

  // Fetch reference data and boxes once
  useEffect(() => {
    const fetchReference = async () => {
      try {
        const data = await apiService.getReferenceData();
        setReferenceData(data);
        const boxesResp = await apiService.getBoxes();
        setBoxesList(boxesResp.boxes);
        const sourceTypesResp = await apiService.getSourceTypes();
        setSourceTypes(sourceTypesResp.source_types);
        const organismNamesResp = await apiService.getOrganismNames();
        setOrganismNames(organismNamesResp.organism_names);
      } catch (e) {
        console.error('Ошибка загрузки справочных данных', e);
      }
    };
    fetchReference();
  }, []);

  if (loading && samples.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Загрузка образцов...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <FlaskConical className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Образцы</h1>
            <p className="text-gray-600">
              Управление образцами коллекции
              <span className="ml-2 text-sm">
                ({pagination?.shown || 0} из {pagination?.total || 0} образцов)
              </span>
            </p>
          </div>
        </div>
        <button 
          onClick={() => navigate('/samples/add')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить образец</span>
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
              placeholder="Поиск образцов..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Штамм
              </label>
              <select
                value={filters.strain_id || ''}
                onChange={(e) => handleFilterChange('strain_id', e.target.value === '' ? undefined : parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все</option>
                {referenceData?.strains.map((s) => (
                  <option key={s.id} value={s.id}>{s.display_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Бокс
              </label>
              <select
                value={filters.box_id || ''}
                onChange={(e) => handleFilterChange('box_id', e.target.value === '' ? undefined : e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все</option>
                {boxesList.map((b) => (
                  <option key={b.box_id} value={b.box_id}>{b.box_id}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип источника
              </label>
              <select
                value={filters.source_type || ''}
                onChange={(e) => handleFilterChange('source_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все типы источников</option>
                {sourceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Организм
              </label>
              <select
                value={filters.organism_name || ''}
                onChange={(e) => handleFilterChange('organism_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все организмы</option>
                {organismNames.map((organism) => (
                  <option key={organism.value} value={organism.value}>
                    {organism.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Лимит результатов
              </label>
              <select
                value={filters.limit || '50'}
                onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="25">25 записей</option>
                <option value="50">50 записей</option>
                <option value="100">100 записей</option>
                <option value="500">500 записей</option>
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                С фото
              </label>
              <select
                value={filters.has_photo === undefined ? '' : filters.has_photo ? 'true' : 'false'}
                onChange={(e) => handleFilterChange('has_photo', 
                  e.target.value === '' ? undefined : e.target.value === 'true'
                )}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="">Все</option>
                <option value="true">Да</option>
                <option value="false">Нет</option>
              </select>
            </div>
            {/* Динамические характеристики будут доступны через расширенные фильтры */}
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
          entityType="samples"
          filters={advancedFilterGroups}
          onFiltersChange={handleAdvancedFiltersChange}
          onReset={handleAdvancedFiltersReset}
        />
      </div>

      {/* Results Count and Active Filters */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Найдено образцов: <span className="font-medium">{pagination?.total || 0}</span>
            {(pagination?.total || 0) !== (pagination?.shown || 0) && (
              <span className="text-gray-500 ml-1">
                (показано {pagination?.shown || 0})
              </span>
            )}
            {countActiveFilters(advancedFilterGroups) > 0 && (
              <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                {countActiveFilters(advancedFilterGroups)} активных фильтров
              </span>
            )}
          </p>
          {(samples?.length || 0) > 0 && (
            <p className="text-sm text-blue-600">
              💡 Нажмите на строку для просмотра деталей
            </p>
          )}
        </div>
        
        {/* Описание активных фильтров */}
        {(advancedFilterGroups?.length || 0) > 0 && (
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded-lg border">
            <span className="font-medium">Активные фильтры:</span> {getFiltersDescription(advancedFilterGroups)}
          </div>
        )}
      </div>

      {/* Bulk Operations Panel */}
      {selectedSampleIds.length > 0 && (
        <BulkOperationsPanel
          selectedIds={selectedSampleIds}
          allSamples={samples}
          onClearSelection={handleClearSelection}
          onRefresh={fetchSamples}
          filters={filters}
          entityType="samples"
          totalCount={pagination?.total || 0}
        />
      )}

      {/* Samples Table */}
      <div className="w-full max-w-full bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedSampleIds.length === (samples?.length || 0) && (samples?.length || 0) > 0}
                    onChange={handleSelectAllSamples}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Штамм
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Номер
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Хранение
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Источник
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                  Характеристики
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(samples?.length || 0) === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <FlaskConical className="w-12 h-12 text-gray-300" />
                      <p className="text-gray-500">
                        {loading ? 'Загрузка образцов...' : 'Нет образцов'}
                      </p>
                      {!loading && (
                        <button
                          onClick={() => navigate('/samples/add')}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Добавить первый образец
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                (samples || []).map((sample) => (
                  <tr 
                    key={sample.id} 
                    className="hover:bg-blue-50 cursor-pointer transition-colors duration-150"
                    onClick={(e) => handleRowClick(sample.id, e)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedSampleIds.includes(sample.id)}
                        onChange={() => handleSelectSample(sample.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      #{sample.id}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {sample.strain ? (
                        <div>
                          <div className="font-medium text-gray-900">
                            {sample.strain.short_code}
                          </div>
                          <div className="text-gray-500 text-xs">
                            ID: {sample.strain.id}
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">Не назначен</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {sample.original_sample_number || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {sample.storage ? (
                        <div className="flex items-center space-x-1">
                          <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                            {sample.storage.box_id}
                          </span>
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            {sample.storage.cell_id}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">Не назначено</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {sample.source ? (
                        <div>
                          <div className="text-sm text-gray-900">
                            {sample.source.name ?? sample.source.organism_name ?? 'Нет источника'}
                          </div>
                          {sample.source.source_type && (
                            <div className="text-gray-500 text-xs">
                              {sample.source.source_type}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">Не указан</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex flex-wrap gap-1">
                        {sample.photos && sample.photos.length > 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                            📷
                          </span>
                        )}
                        {/* Dynamic characteristics will be shown based on the characteristics array or object */}
                        {sample.characteristics && (
                          Array.isArray(sample.characteristics) 
                            ? sample.characteristics.length > 0
                            : Object.keys(sample.characteristics).length > 0
                        ) && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                            ⚡ {Array.isArray(sample.characteristics) 
                                ? sample.characteristics.length 
                                : Object.keys(sample.characteristics).length}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {(pagination?.total || 0) > 0 && (
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
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

export default Samples;
