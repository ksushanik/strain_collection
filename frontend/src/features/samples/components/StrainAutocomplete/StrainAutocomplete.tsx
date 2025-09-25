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
  const [currentStrain, setCurrentStrain] = useState<ReferenceStrain | null>(null);

  // Загрузка текущего штамма по ID
  useEffect(() => {
    const loadCurrentStrain = async () => {
      if (value && !currentStrain) {
        try {
          const strain = await apiService.getStrain(value);
          const formattedStrain: ReferenceStrain = {
            id: strain.id,
            display_name: `${strain.short_code} - ${strain.identifier}`,
            short_code: strain.short_code,
            identifier: strain.identifier,
            secondary_text: strain.rrna_taxonomy || strain.name_alt
          };
          setCurrentStrain(formattedStrain);
          // Добавляем текущий штамм в список опций, если его там нет
          setStrains(prev => {
            const exists = prev.some(s => s.id === strain.id);
            return exists ? prev : [formattedStrain, ...prev];
          });
        } catch (error) {
          console.error('Ошибка при загрузке штамма:', error);
        }
      } else if (!value) {
        setCurrentStrain(null);
      }
    };

    loadCurrentStrain();
  }, [value]);

  // Загрузка штаммов при поиске
  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      // Если есть текущий штамм, показываем его
      if (currentStrain) {
        setStrains([currentStrain]);
      } else {
        setStrains([]);
      }
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
      
      // Добавляем текущий штамм в начало списка, если его нет среди результатов поиска
      let finalStrains = formattedStrains;
      if (currentStrain && !formattedStrains.some(s => s.id === currentStrain.id)) {
        finalStrains = [currentStrain, ...formattedStrains];
      }
      
      setStrains(finalStrains);
    } catch (error) {
      console.error('Ошибка при поиске штаммов:', error);
      // В случае ошибки показываем текущий штамм, если он есть
      if (currentStrain) {
        setStrains([currentStrain]);
      } else {
        setStrains([]);
      }
    } finally {
      setLoading(false);
    }
  };

  // Загрузка начальных данных
  useEffect(() => {
    handleSearch('');
  }, [currentStrain]);

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