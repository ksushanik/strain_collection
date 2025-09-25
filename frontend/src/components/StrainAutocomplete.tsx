import React, { useState, useEffect, useRef } from 'react';
import apiService from '../services/api';
import type { Strain } from '../types';

interface StrainAutocompleteProps {
  value?: number | null;
  onChange: (strainId: number | null) => void;
  placeholder?: string;
}

const StrainAutocomplete: React.FC<StrainAutocompleteProps> = ({ value, onChange, placeholder }) => {
  const [inputValue, setInputValue] = useState<string>('');
  const [options, setOptions] = useState<Strain[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Загрузка имени выбранного штамма при полученном value
  useEffect(() => {
    const fetchStrain = async () => {
      if (value) {
        try {
          const strain = await apiService.getStrain(value);
          setInputValue(`${strain.short_code} (${strain.identifier})`);
        } catch {
          // ignore
        }
      }
    };
    fetchStrain();
  }, [value]);

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setOptions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.getStrains({ search: searchTerm, limit: 50 });
      const strains = response.strains || [];
      setOptions(strains);
    } catch (error) {
      console.error('Error searching strains:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка вариантов при вводе
  useEffect(() => {
    if (inputValue.trim().length < 2) {
      setOptions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      handleSearch(inputValue);
    }, 300);
  }, [inputValue]);

  // Обработчики
  const handleSelect = (strain: Strain) => {
    setInputValue(`${strain.short_code} (${strain.identifier})`);
    setIsOpen(false);
    onChange(strain.id);
  };

  return (
    <div className="relative w-60">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => {
          setInputValue(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder={placeholder || 'Введите название штамма'}
        className="px-3 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      {isOpen && (
        <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg max-h-60 overflow-auto shadow-lg">
          {loading ? (
            <li className="px-3 py-2 text-gray-500">Загрузка...</li>
          ) : options.length > 0 ? (
            options.map((strain) => (
              <li
                key={strain.id}
                onClick={() => handleSelect(strain)}
                className="px-3 py-2 cursor-pointer hover:bg-blue-100"
              >
                <span className="font-medium">{strain.short_code}</span>{' '}
                <span className="text-gray-600">({strain.identifier})</span>
              </li>
            ))
          ) : (
            <li className="px-3 py-2 text-gray-500">Нет результатов</li>
          )}
        </ul>
      )}
    </div>
  );
};

export default StrainAutocomplete;

