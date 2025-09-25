import React, { useState, useEffect } from 'react';
import { Search, Filter, X } from 'lucide-react';
import type { SampleFilters } from '../types';
import type { Strain } from '../../strains/types';

interface Storage {
  id: number;
  box_id: string;
  cell_id: string;
}

interface SampleFiltersProps {
  filters: SampleFilters;
  onFiltersChange: (filters: SampleFilters) => void;
  onClearFilters: () => void;
}

export const SampleFiltersComponent: React.FC<SampleFiltersProps> = ({
  filters,
  onFiltersChange,
  onClearFilters
}) => {
  const [strains, setStrains] = useState<Strain[]>([]);
  const [storages, setStorages] = useState<Storage[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  // Загрузка штаммов для фильтра
  useEffect(() => {
    const loadStrains = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/strains/?limit=1000');
        if (response.ok) {
          const data = await response.json();
          setStrains(data.strains || []);
        }
      } catch (error) {
        console.error('Ошибка загрузки штаммов:', error);
      }
    };

    const loadStorages = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/storage/storages/?limit=1000');
        if (response.ok) {
          const data = await response.json();
          setStorages(data.results || []);
        }
      } catch (error) {
        console.error('Ошибка загрузки мест хранения:', error);
      }
    };

    loadStrains();
    loadStorages();
  }, []);

  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value });
  };

  const handleStrainChange = (strainId: string) => {
    onFiltersChange({ 
      ...filters, 
      strain_id: strainId ? parseInt(strainId) : undefined 
    });
  };

  const handleStorageChange = (storageId: string) => {
    onFiltersChange({ 
      ...filters, 
      storage_id: storageId ? parseInt(storageId) : undefined 
    });
  };

  const hasActiveFilters = filters.search || filters.strain_id || filters.storage_id;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      {/* Поиск */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Поиск по номеру образца, штамму, комментарию..."
            value={filters.search || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            data-testid="search-input"
          />
        </div>
        
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${
            showFilters || hasActiveFilters
              ? 'bg-blue-50 border-blue-300 text-blue-700'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
          data-testid="filter-button"
        >
          <Filter className="w-4 h-4" />
          Фильтры
          {hasActiveFilters && (
            <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {[filters.strain_id, filters.storage_id].filter(Boolean).length}
            </span>
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            data-testid="clear-filters-button"
          >
            <X className="w-4 h-4" />
            Очистить
          </button>
        )}
      </div>

      {/* Расширенные фильтры */}
      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200" data-testid="advanced-filters">
          {/* Фильтр по штамму */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Штамм
            </label>
            <select
              value={filters.strain_id || ''}
              onChange={(e) => handleStrainChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Все штаммы</option>
              {strains.map((strain) => (
                <option key={strain.id} value={strain.id}>
                  {strain.short_code} - {strain.identifier}
                </option>
              ))}
            </select>
          </div>

          {/* Фильтр по месту хранения */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Место хранения
            </label>
            <select
              value={filters.storage_id || ''}
              onChange={(e) => handleStorageChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Все места хранения</option>
              {storages.map((storage) => (
                <option key={storage.id} value={storage.id}>
                  {storage.box_id}-{storage.cell_id}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
};