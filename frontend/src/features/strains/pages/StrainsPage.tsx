import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Filter, Download } from 'lucide-react';
import { useStrains } from '../hooks/useStrains';
import { Pagination, SearchInput } from '../../../shared/components';
import { StrainCard } from '../components';
import type { StrainFilters } from '../types';

const StrainsPage: React.FC = () => {
  const navigate = useNavigate();
  const [showFilters, setShowFilters] = useState(false);
  const [selectedStrainIds, setSelectedStrainIds] = useState<number[]>([]);
  
  const {
    strains,
    loading,
    error,
    pagination,
    refetch,
    setFilters,
    filters
  } = useStrains();

  const handleSearch = (searchTerm: string) => {
    setFilters({
      ...filters,
      search: searchTerm,
      page: 1 // Сбрасываем на первую страницу при поиске
    });
  };

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page });
  };

  const handleLimitChange = (limit: number) => {
    setFilters({ ...filters, limit, page: 1 });
  };

  const handleDeleteStrain = useCallback(async (strainId: number) => {
    try {
      // TODO: Реализовать delete API
      console.log('Delete strain:', strainId);
      // Обновить данные после удаления
      // refetch();
    } catch (error) {
      console.error('Ошибка при удалении штамма:', error);
    }
  }, []);

  const handleStrainSelect = (strainId: number, selected: boolean) => {
    if (selected) {
      setSelectedStrainIds(prev => [...prev, strainId]);
    } else {
      setSelectedStrainIds(prev => prev.filter(id => id !== strainId));
    }
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedStrainIds(strains?.map(strain => strain.id) || []);
    } else {
      setSelectedStrainIds([]);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Ошибка загрузки</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Штаммы микроорганизмов</h1>
          <p className="mt-2 text-gray-600">
            Управление коллекцией штаммов микроорганизмов
          </p>
        </div>

        {/* Панель управления */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              {/* Поиск */}
              <div className="flex-1 max-w-md">
                <SearchInput
                  value={filters.search || ''}
                  onChange={handleSearch}
                  placeholder="Поиск по коду, идентификатору, таксономии..."
                />
              </div>

              {/* Кнопки действий */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Фильтры
                </button>
                
                <button
                  onClick={() => {/* TODO: Implement export */}}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Экспорт
                </button>
                
                <button
                  onClick={() => navigate('/strains/add')}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Добавить штамм
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Таблица штаммов */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Загрузка штаммов...</p>
            </div>
          ) : (strains?.length || 0) === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Штаммы не найдены</p>
              {filters.search && (
                <button
                  onClick={() => setFilters({ page: 1, limit: filters.limit })}
                  className="mt-2 text-blue-600 hover:text-blue-800"
                >
                  Сбросить фильтры
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                {strains?.map((strain) => (
                  <StrainCard
                    key={strain.id}
                    strain={strain}
                    isSelected={selectedStrainIds.includes(strain.id)}
                    onSelect={handleStrainSelect}
                  />
                ))}
              </div>
              
              <Pagination
                pagination={pagination}
                onPageChange={handlePageChange}
                onLimitChange={handleLimitChange}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrainsPage;