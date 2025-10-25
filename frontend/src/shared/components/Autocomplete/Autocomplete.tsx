import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Loader2, Plus } from 'lucide-react';

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
  allowCreate?: boolean;
  onCreateOption?: (value: string) => Promise<T | null> | T | null;
  createOptionLabel?: (value: string) => string;
}

export function Autocomplete<T extends AutocompleteOption>({
  value,
  onChange,
  options,
  onSearch,
  placeholder = "Найдите значение...",
  disabled = false,
  required = false,
  loading = false,
  emptyMessage = "Ничего не найдено",
  renderOption,
  getDisplayValue,
  filterOptions,
  allowCreate = false,
  onCreateOption,
  createOptionLabel,
}: AutocompleteProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredOptions, setFilteredOptions] = useState<T[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [creationError, setCreationError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const normalizedSearch = searchTerm.trim();
  const normalizedSearchLower = normalizedSearch.toLowerCase();

  useEffect(() => {
    if (!searchTerm) {
      setFilteredOptions(options.slice(0, 50));
      return;
    }

    const result = filterOptions
      ? filterOptions(options, searchTerm)
      : options
          .filter(option => {
            const label = (getDisplayValue ? getDisplayValue(option) : option.display_name).toLowerCase();
            const secondary = option.secondary_text?.toLowerCase() ?? '';
            return label.includes(normalizedSearchLower) || secondary.includes(normalizedSearchLower);
          });

    setFilteredOptions(result.slice(0, 50));
  }, [filterOptions, getDisplayValue, normalizedSearchLower, options, searchTerm]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setFilteredOptions(options.slice(0, 50));
  }, [isOpen, options]);

  useEffect(() => {
    if (value === undefined || value === null) {
      setSearchTerm('');
      return;
    }

    const current = options.find(option => option.id === value);
    if (current) {
      const label = getDisplayValue ? getDisplayValue(current) : current.display_name;
      setSearchTerm(label);
    }
  }, [getDisplayValue, options, value]);

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
    const displayValue = getDisplayValue ? getDisplayValue(option) : option.display_name;
    setSearchTerm(displayValue);
    onChange(option.id);
    setIsOpen(false);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextValue = event.target.value;
    setSearchTerm(nextValue);
    setIsOpen(true);
    setCreationError(null);

    if (!nextValue) {
      onChange(undefined);
    }

    onSearch?.(nextValue);
  };

  const defaultRenderOption = (option: T) => (
    <div>
      <div className="font-medium text-gray-900">{option.display_name}</div>
      {option.secondary_text ? (
        <div className="text-sm text-gray-500">{option.secondary_text}</div>
      ) : null}
    </div>
  );

  const hasExactMatch = options.some(option => {
    const label = getDisplayValue ? getDisplayValue(option) : option.display_name;
    return label.toLowerCase() === normalizedSearchLower;
  });

  const canCreate = allowCreate && !!normalizedSearch && !hasExactMatch && !!onCreateOption;

  const handleCreateOption = async () => {
    if (!canCreate || !onCreateOption || isCreating) {
      return;
    }

    setIsCreating(true);
    setCreationError(null);

    try {
      const created = await onCreateOption(normalizedSearch);
      if (created) {
        const displayValue = getDisplayValue ? getDisplayValue(created) : created.display_name;
        setSearchTerm(displayValue);
        onChange(created.id);
        setIsOpen(false);
      }
    } catch (error) {
      console.error('Autocomplete: creation error', error);
      setCreationError(
        error instanceof Error ? error.message : 'Не удалось создать новое значение. Попробуйте снова.'
      );
    } finally {
      setIsCreating(false);
    }
  };

  const handleKeyDown = async (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && canCreate) {
      event.preventDefault();
      await handleCreateOption();
    }
  };

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
          onKeyDown={handleKeyDown}
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
          ) : isCreating ? (
            <div className="flex items-center justify-center p-4 text-sm text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              <span>Создание...</span>
            </div>
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">
              {canCreate
                ? (createOptionLabel ? createOptionLabel(normalizedSearch) : `Нажмите Enter, чтобы добавить «${normalizedSearch}»`)
                : emptyMessage}
            </div>
          )}

          {canCreate && !isCreating && (
            <div
              onClick={handleCreateOption}
              className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 cursor-pointer border-t border-gray-100 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>{createOptionLabel ? createOptionLabel(normalizedSearch) : `Добавить «${normalizedSearch}»`}</span>
            </div>
          )}
        </div>
      )}

      {creationError && (
        <p className="mt-1 text-sm text-red-600">{creationError}</p>
      )}
    </div>
  );
}
