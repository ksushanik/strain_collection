import React from 'react';
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
  disabled?: boolean;
  required?: boolean;
}

export const SourceAutocomplete: React.FC<SourceAutocompleteProps> = ({
  value,
  onChange,
  sources,
  disabled = false,
  required = false
}) => {
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
      options={sources}
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