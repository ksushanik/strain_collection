import React, { useMemo, useCallback } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';

interface ReferenceSourceOption extends AutocompleteOption {
  id: number;
  display_name: string;
  secondary_text?: string;
}

interface SourceAutocompleteProps {
  value?: number;
  onChange: (value: number | undefined) => void;
  sources: ReferenceSourceOption[];
  currentSourceName?: string;
  disabled?: boolean;
  required?: boolean;
  onCreate?: (name: string) => Promise<{ id: number; name: string } | null> | { id: number; name: string } | null;
}

export const SourceAutocomplete: React.FC<SourceAutocompleteProps> = ({
  value,
  onChange,
  sources,
  currentSourceName,
  disabled = false,
  required = false,
  onCreate,
}) => {
  const extendedSources = useMemo(() => {
    if (!value || !currentSourceName) {
      return sources;
    }

    const exists = sources.some(source => source.id === value);
    if (exists) {
      return sources;
    }

    const currentSource: ReferenceSourceOption = {
      id: value,
      display_name: currentSourceName,
      secondary_text: currentSourceName,
    };

    return [currentSource, ...sources];
  }, [currentSourceName, sources, value]);

  const filterSources = useCallback((items: ReferenceSourceOption[], searchTerm: string) => {
    const normalized = searchTerm.toLowerCase();
    return items.filter(source =>
      source.display_name.toLowerCase().includes(normalized) ||
      (source.secondary_text && source.secondary_text.toLowerCase().includes(normalized))
    );
  }, []);

  const handleCreate = useCallback(async (name: string) => {
    if (!onCreate) {
      return null;
    }

    const created = await onCreate(name.trim());
    if (!created) {
      return null;
    }

    return {
      id: created.id,
      display_name: created.name,
      secondary_text: created.name,
    } satisfies ReferenceSourceOption;
  }, [onCreate]);

  return (
    <Autocomplete
      value={value}
      onChange={onChange}
      options={extendedSources}
      placeholder="Найдите или создайте источник..."
      disabled={disabled}
      required={required}
      emptyMessage="Источник не найден"
      filterOptions={filterSources}
      allowCreate={Boolean(onCreate)}
      onCreateOption={handleCreate}
      createOptionLabel={(term) => `Добавить источник «${term}»`}
      renderOption={(source) => (
        <div>
          <div className="font-medium text-gray-900">{source.display_name}</div>
          {source.secondary_text && (
            <div className="text-sm text-gray-500">{source.secondary_text}</div>
          )}
        </div>
      )}
    />
  );
};

