import React, { useState, useEffect, useCallback } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';
import apiService from '../../../../services/api';
import type { Strain } from '../../../../types';

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
  const handleChange = (selectedId: number | string | undefined) => {
    console.log('🧬 StrainAutocomplete: handleChange called with:', selectedId);
    console.log('🧬 StrainAutocomplete: Calling onChange with:', selectedId as number | undefined);
    onChange(selectedId as number | undefined);
  };
  console.log('🧬 StrainAutocomplete: Component initialized with props:', { value, disabled });
  
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
  }, [value, currentStrain]);

  // Загрузка всех штаммов при монтировании
  useEffect(() => {
    const loadAllStrains = async () => {
      console.log('🔍 StrainAutocomplete: Loading all strains on mount');
      try {
        const response = await apiService.getStrains({ limit: 50 });
        const strainsData = response.strains || [];
        
        const formattedStrains: ReferenceStrain[] = strainsData.map((strain: Strain) => ({
          id: strain.id,
          display_name: `${strain.short_code} - ${strain.identifier}`,
          short_code: strain.short_code,
          identifier: strain.identifier,
          secondary_text: strain.rrna_taxonomy || strain.name_alt
        }));
        
        setStrains(formattedStrains);
        console.log('🔍 StrainAutocomplete: Loaded initial strains:', formattedStrains.length);
      } catch (error) {
        console.error('🔍 StrainAutocomplete: Error loading initial strains:', error);
        setStrains([]);
      }
    };

    loadAllStrains();
  }, []);

  // Загрузка штаммов при поиске
  const handleSearch = useCallback(async (searchTerm: string) => {
    console.log('🔍 StrainAutocomplete: handleSearch called with:', searchTerm);
    
    if (!searchTerm) {
      console.log('🔍 StrainAutocomplete: Empty search term, loading all strains');
      // Загружаем все штаммы при пустом поиске
      try {
        const response = await apiService.getStrains({ limit: 50 });
        const strainsData = response.strains || [];
        
        const formattedStrains: ReferenceStrain[] = strainsData.map((strain: Strain) => ({
          id: strain.id,
          display_name: `${strain.short_code} - ${strain.identifier}`,
          short_code: strain.short_code,
          identifier: strain.identifier,
          secondary_text: strain.rrna_taxonomy || strain.name_alt
        }));
        
        setStrains(formattedStrains);
      } catch (error) {
        console.error('🔍 StrainAutocomplete: Error loading all strains:', error);
        setStrains([]);
      }
      return;
    }

    console.log('🔍 StrainAutocomplete: Starting search...');
    setLoading(true);
    console.log('🔍 StrainAutocomplete: Starting strain search for:', searchTerm);
    
    try {
      const response = await apiService.getStrains({ search: searchTerm, limit: 50 });
      console.log('🔍 StrainAutocomplete: API response:', response);
      
      const strainsData = response.strains || [];
      console.log('🔍 StrainAutocomplete: Strains data:', strainsData);
      
      const formattedStrains: ReferenceStrain[] = strainsData.map((strain: Strain) => ({
        id: strain.id,
        display_name: `${strain.short_code} - ${strain.identifier}`,
        short_code: strain.short_code,
        identifier: strain.identifier,
        secondary_text: strain.rrna_taxonomy || strain.name_alt
      }));
      
      console.log('🔍 StrainAutocomplete: Formatted strains:', formattedStrains);
      
      // Добавляем текущий штамм в начало списка, если его нет среди результатов поиска
      let finalStrains = formattedStrains;
      if (currentStrain && !formattedStrains.some(s => s.id === currentStrain.id)) {
        finalStrains = [currentStrain, ...formattedStrains];
      }
      
      console.log('🔍 StrainAutocomplete: Final strains list:', finalStrains);
      setStrains(finalStrains);
    } catch (error) {
      console.error('🔍 StrainAutocomplete: Error searching strains:', error);
      // В случае ошибки показываем текущий штамм, если он есть
      if (currentStrain) {
        setStrains([currentStrain]);
      } else {
        setStrains([]);
      }
    } finally {
      setLoading(false);
    }
  }, [currentStrain]);

  // Загрузка начальных данных
  useEffect(() => {
    console.log('StrainAutocomplete initial load, currentStrain:', currentStrain);
    handleSearch('');
  }, [currentStrain, handleSearch]);

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
      onChange={handleChange}
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