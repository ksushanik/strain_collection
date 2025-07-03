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
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Загрузка имени выбранного штамма при полученном value
  useEffect(() => {
    const fetchStrain = async () => {
      if (value) {
        try {
          const strain = await apiService.getStrain(value);
          setInputValue(`${strain.short_code} (${strain.identifier})`);
        } catch (e) {
          // ignore
        }
      }
    };
    fetchStrain();
  }, [value]);

  // Загрузка вариантов при вводе
  useEffect(() => {
    if (inputValue.trim().length < 2) {
      setOptions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const resp = await apiService.getStrains({ search: inputValue, limit: 10 });
        setOptions(resp.strains);
      } catch (e) {
        console.error('Ошибка загрузки штаммов для автодополнения', e);
      }
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
      {isOpen && options.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg max-h-60 overflow-auto shadow-lg">
          {options.map((strain) => (
            <li
              key={strain.id}
              onClick={() => handleSelect(strain)}
              className="px-3 py-2 cursor-pointer hover:bg-blue-100"
            >
              <span className="font-medium">{strain.short_code}</span>{' '}
              <span className="text-gray-600">({strain.identifier})</span>
            </li>
          ))}
          {options.length === 0 && (
            <li className="px-3 py-2 text-gray-500">Нет результатов</li>
          )}
        </ul>
      )}
    </div>
  );
};

export default StrainAutocomplete; 