import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Download, Trash2, Filter } from 'lucide-react';
import { useSamples } from '../hooks/useSamples';
import { Pagination } from '../../../shared/components/Pagination';
import { SearchInput } from '../../../shared/components/SearchInput';
import { SampleCard } from '../components';
import type { SampleFilters } from '../types';

const SamplesPage: React.FC = () => {
  const [filters, setFilters] = useState<SampleFilters>({
    search: '',
    page: 1,
    limit: 20
  });
  const [selectedSamples, setSelectedSamples] = useState<number[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  const { data, loading, error, refetch } = useSamples({
    filters,
    page: filters.page,
    limit: filters.limit
  });

  const handleSearchChange = useCallback((search: string) => {
    setFilters(prev => ({ ...prev, search, page: 1 }));
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);

  const handleLimitChange = useCallback((limit: number) => {
    setFilters(prev => ({ ...prev, limit, page: 1 }));
  }, []);

  const handleSampleSelect = (sampleId: number, selected: boolean) => {
    if (selected) {
      setSelectedSamples(prev => [...prev, sampleId]);
    } else {
      setSelectedSamples(prev => prev.filter(id => id !== sampleId));
    }
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected && data?.samples) {
      setSelectedSamples(data.samples.map(sample => sample.id));
    } else {
      setSelectedSamples([]);
    }
  };

  const handleDeleteSample = useCallback(async (sampleId: number) => {
    try {
      // TODO: Реализовать delete API
      console.log('Delete sample:', sampleId);
      // Обновить данные после удаления
      // refetch();
    } catch (error) {
      console.error('Ошибка при удалении образца:', error);
    }
  }, []);

  const handleBulkDelete = useCallback(async () => {
    if (selectedSamples.length === 0) return;
    
    if (window.confirm(`Вы уверены, что хотите удалить ${selectedSamples.length} образцов?`)) {
      try {
        // TODO: Реализовать bulk delete API
        console.log('Bulk delete:', selectedSamples);
        setSelectedSamples([]);
        // Обновить данные после удаления
        // refetch();
      } catch (error) {
        console.error('Ошибка при удалении образцов:', error);
      }
    }
  }, [selectedSamples]);

  const handleExport = useCallback(async () => {
    try {
      // TODO: Реализовать export API
      console.log('Export samples with filters:', filters);
    } catch (error) {
      console.error('Ошибка при экспорте образцов:', error);
    }
  }, [filters]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Ошибка загрузки
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={() => refetch()}
                className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200"
              >
                Попробовать снова
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Образцы</h1>
          <p className="mt-1 text-sm text-gray-500">
            Управление коллекцией образцов
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Filter className="h-4 w-4 mr-2" />
            Фильтры
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Download className="h-4 w-4 mr-2" />
            Экспорт
          </button>
          <Link
            to="/samples/add"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Добавить образец
          </Link>
        </div>
      </div>

      {/* Поиск и массовые операции */}
      <div className="flex justify-between items-center">
        <div className="flex-1 max-w-lg">
          <SearchInput
            value={filters.search || ''}
            onChange={handleSearchChange}
            placeholder="Поиск образцов..."
            debounceMs={300}
          />
        </div>
        
        {selectedSamples.length > 0 && (
          <div className="flex items-center space-x-3">
            <span className="text-sm text-gray-500">
              Выбрано: {selectedSamples.length}
            </span>
            <button
              onClick={handleBulkDelete}
              className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Удалить выбранные
            </button>
          </div>
        )}
      </div>

      {/* Фильтры (если показаны) */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* TODO: Добавить фильтры по штамму, источнику, местоположению и т.д. */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Штамм
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Номер штамма"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Источник
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Все источники</option>
                {/* TODO: Загрузить список источников */}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Местоположение
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Все местоположения</option>
                {/* TODO: Загрузить список местоположений */}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Список образцов */}
      {data?.samples && data.samples.length > 0 ? (
        <>
          {/* Заголовок таблицы с чекбоксом "Выбрать все" */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedSamples.length === data.samples.length}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-3 text-sm font-medium text-gray-700">
                  Выбрать все ({data.samples.length})
                </span>
              </div>
            </div>

            {/* Список образцов */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
              {data.samples.map((sample) => (
                <SampleCard
                  key={sample.id}
                  sample={sample}
                  isSelected={selectedSamples.includes(sample.id)}
                  onSelect={handleSampleSelect}
                  onDelete={handleDeleteSample}
                />
              ))}
            </div>
          </div>

          {/* Пагинация */}
          {data.pagination && (
            <Pagination
              pagination={data.pagination}
              onPageChange={handlePageChange}
              onLimitChange={handleLimitChange}
              showLimitSelector={true}
            />
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">
            {filters.search ? 'Образцы не найдены' : 'Нет образцов'}
          </div>
          <div className="mt-4">
            <Link
              to="/samples/add"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Добавить первый образец
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default SamplesPage;