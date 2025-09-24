import React, { useState, useEffect } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';
import apiService from '../../../../services/api';

interface ReferenceStrain extends AutocompleteOption {
  id: number;
  display_name: string;
  short_code: string;
  identifier: string;
}

interface StrainAutocompleteProps {
  value?: number;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
  required?: boolean;
}

export const StrainAutocomplete: React.FC<StrainAutocompleteProps> = ({
  value,
  onChange,
  disabled = false,
  required = false
}) => {
  const [strains, setStrains] = useState<ReferenceStrain[]>([]);
  const [loading, setLoading] = useState(false);

  // Загрузка штаммов при поиске
  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      setStrains([]);
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.getStrains({ search: searchTerm, limit: 50 });
      const strainsData = response.strains || [];
      
      const formattedStrains: ReferenceStrain[] = strainsData.map((strain: any) => ({
        id: strain.id,
        display_name: `${strain.short_code} - ${strain.identifier}`,
        short_code: strain.short_code,
        identifier: strain.identifier,
        secondary_text: strain.rrna_taxonomy || strain.name_alt
      }));
      
      setStrains(formattedStrains);
    } catch (error) {
      console.error('Ошибка при поиске штаммов:', error);
      setStrains([]);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка начальных данных
  useEffect(() => {
    handleSearch('');
  }, []);

  const filterStrains = (strains: ReferenceStrain[], searchTerm: string) => {
    return strains.filter(strain =>
      strain.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      strain.short_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      strain.identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (strain.secondary_text && strain.secondary_text.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  };

  return (
    <Autocomplete
      value={value}
      onChange={onChange}
      options={strains}
      onSearch={handleSearch}
      placeholder="Введите код или название штамма..."
      disabled={disabled}
      required={required}
      loading={loading}
      emptyMessage="Штаммы не найдены"
      filterOptions={filterStrains}
      renderOption={(strain) => (
        <div>
          <div className="font-medium text-gray-900">{strain.display_name}</div>
          {strain.secondary_text && (
            <div className="text-sm text-gray-500">{strain.secondary_text}</div>
          )}
        </div>
      )}
    />
  );
};