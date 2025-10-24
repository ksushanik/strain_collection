import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Loader2 } from 'lucide-react';

export interface AutocompleteOption {
  id: number | string;
  display_name: string;
  secondary_text?: string;
}

interface AutocompleteProps<T extends AutocompleteOption> {
  value?: T['id'];
  onChange: (value: T['id'] | undefined) => void;
  options: T[];
  onSearch?: (searchTerm: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  loading?: boolean;
  emptyMessage?: string;
  renderOption?: (option: T) => React.ReactNode;
  getDisplayValue?: (option: T) => string;
  filterOptions?: (options: T[], searchTerm: string) => T[];
}

export function Autocomplete<T extends AutocompleteOption>({
  value,
  onChange,
  options,
  onSearch,
  placeholder = "Начните вводить...",
  disabled = false,
  required = false,
  loading = false,
  emptyMessage = "Ничего не найдено",
  renderOption,
  getDisplayValue,
  filterOptions
}: AutocompleteProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredOptions, setFilteredOptions] = useState<T[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Фильтрация опций
  useEffect(() => {
    if (!searchTerm) {
      setFilteredOptions(options.slice(0, 50));
    } else {
      const filtered = filterOptions 
        ? filterOptions(options, searchTerm)
        : options.filter(option =>
            option.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (option.secondary_text && option.secondary_text.toLowerCase().includes(searchTerm.toLowerCase()))
          ).slice(0, 50);
      setFilteredOptions(filtered);
    }
  }, [searchTerm, options]);

  // Обновление отображаемого значения при изменении value
  useEffect(() => {
    if (value !== undefined) {
      const option = options.find(opt => opt.id === value);
      if (option) {
        const displayValue = getDisplayValue ? getDisplayValue(option) : option.display_name;
        // Проверяем, нужно ли обновлять searchTerm, чтобы избежать лишних ре-рендеров
        setSearchTerm(prevTerm => {
          if (prevTerm !== displayValue) {
            return displayValue;
          }
          return prevTerm;
        });
      }
    } else {
      setSearchTerm(prevTerm => prevTerm !== '' ? '' : prevTerm);
    }
  }, [value, options]);

  // Загружаем опции при открытии
  useEffect(() => {
    if (isOpen) {
      setFilteredOptions(options.slice(0, 50));
    }
  }, [isOpen, options]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: T) => {
    console.log('🎯 Autocomplete: handleSelect called with option:', option);
    setSearchTerm(getDisplayValue ? getDisplayValue(option) : option.display_name);
    console.log('🎯 Autocomplete: Calling onChange with option.id:', option.id);
    onChange(option.id);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    console.log('🎯 Autocomplete: handleInputChange called with:', newSearchTerm);
    setSearchTerm(newSearchTerm);
    
    if (!newSearchTerm) {
      console.log('🎯 Autocomplete: Empty search term, calling onChange with undefined');
      onChange(undefined);
    }
    
    setIsOpen(true);
    onSearch?.(newSearchTerm);
  };

  const defaultRenderOption = (option: T) => (
    <div>
      <div className="font-medium text-gray-900">{option.display_name}</div>
      {option.secondary_text && (
        <div className="text-sm text-gray-500">{option.secondary_text}</div>
      )}
    </div>
  );

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder={placeholder}
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          disabled={disabled}
          required={required}
        />
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
      </div>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center p-4">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              <span className="text-sm text-gray-500">Загрузка...</span>
            </div>
          ) : filteredOptions.length > 0 ? (
            filteredOptions.map(option => (
              <div
                key={option.id}
                onClick={() => handleSelect(option)}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                {renderOption ? renderOption(option) : defaultRenderOption(option)}
              </div>
            ))
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">
              {emptyMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}