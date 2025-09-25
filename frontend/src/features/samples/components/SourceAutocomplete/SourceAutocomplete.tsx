import React, { useMemo } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';

interface ReferenceSource extends AutocompleteOption {
  id: number;
  display_name: string;
  organism_name: string;
}

interface SourceAutocompleteProps {
  value?: number;
  onChange: (value: number | undefined) => void;
  sources: ReferenceSource[];
  currentSourceName?: string; // Название текущего источника из данных образца
  disabled?: boolean;
  required?: boolean;
}

export const SourceAutocomplete: React.FC<SourceAutocompleteProps> = ({
  value,
  onChange,
  sources,
  currentSourceName,
  disabled = false,
  required = false
}) => {
  // Создаем расширенный список источников, включая текущий источник если он не найден
  const extendedSources = useMemo(() => {
    if (!value || !currentSourceName) {
      return sources;
    }

    // Проверяем, есть ли текущий источник в списке
    const currentSourceExists = sources.some(source => source.id === value);
    
    if (currentSourceExists) {
      return sources;
    }

    // Если текущий источник не найден, добавляем его в список
    const currentSource: ReferenceSource = {
      id: value,
      display_name: currentSourceName,
      organism_name: currentSourceName
    };

    return [currentSource, ...sources];
  }, [sources, value, currentSourceName]);

  const filterSources = (sources: ReferenceSource[], searchTerm: string) => {
    return sources.filter(source =>
      source.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.organism_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  return (
    <Autocomplete
      value={value}
      onChange={onChange}
      options={extendedSources}
      placeholder="Введите название источника..."
      disabled={disabled}
      required={required}
      emptyMessage="Источники не найдены"
      filterOptions={filterSources}
      renderOption={(source) => (
        <div>
          <div className="font-medium text-gray-900">{source.display_name}</div>
          <div className="text-sm text-gray-500">{source.organism_name}</div>
        </div>
      )}
    />
  );
};