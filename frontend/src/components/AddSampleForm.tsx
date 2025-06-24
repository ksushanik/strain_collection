import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Plus, Loader2, Search, Beaker, ChevronDown } from 'lucide-react';
import apiService from '../services/api';
import { API_ENDPOINTS, buildSearchUrl } from '../config/api';
import type { 
  CreateSampleData, 
  ReferenceStrain,
  ReferenceSource,
  ReferenceLocation,
  ReferenceStorage 
} from '../types';

interface AddSampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  preSelectedStrainId?: number;
}

interface ReferenceIndexLetter {
  id: number;
  letter_value: string;
}

interface ReferenceComment {
  id: number;
  text: string;
}

interface ReferenceAppendixNote {
  id: number;
  text: string;
}

interface AddSampleReferenceData {
  strains: ReferenceStrain[];
  sources: ReferenceSource[];
  locations: ReferenceLocation[];
  free_storage: ReferenceStorage[];
  index_letters: ReferenceIndexLetter[];
  comments: ReferenceComment[];
  appendix_notes: ReferenceAppendixNote[];
}

// Автокомплит компонент для штаммов
const StrainAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
  required?: boolean;
}> = ({ value, onChange, disabled, required }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredStrains, setFilteredStrains] = useState<ReferenceStrain[]>([]);
  const [selectedStrain, setSelectedStrain] = useState<ReferenceStrain | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Загрузка штаммов с сервера (мемоизировано)
  const loadStrains = useCallback(async (search = '') => {
    setLoading(true);
    try {
      const url = buildSearchUrl(API_ENDPOINTS.referenceData, search);
      
      const response = await fetch(url);
      const data = await response.json();
      setFilteredStrains(data.strains || []);
    } catch (err) {
      console.error('Ошибка загрузки штаммов:', err);
      setFilteredStrains([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Загружаем штаммы при изменении поискового запроса
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (searchTerm || isOpen) {
        loadStrains(searchTerm);
      }
    }, 300);

    return () => clearTimeout(delayedSearch);
  }, [searchTerm, isOpen, loadStrains]);

  // Загружаем штаммы при открытии
  useEffect(() => {
    if (isOpen) {
      loadStrains(searchTerm);
    }
  }, [isOpen, searchTerm, loadStrains]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Синхронизация внешнего значения
  useEffect(() => {
    if (value && (!selectedStrain || selectedStrain.id !== value)) {
      // если выбранный штамм ещё не загружен – подгружаем его
      const fetchSelected = async () => {
        try {
          const response = await fetch(`${API_ENDPOINTS.strains}${value}/`);
          const strain: ReferenceStrain = await response.json();
          setSelectedStrain(strain);
          setSearchTerm(`${strain.short_code} - ${strain.display_name}`);
        } catch (e) {
          console.error('Ошибка загрузки выбранного штамма', e);
        }
      };
      fetchSelected();
    }
    if (!value) {
      setSelectedStrain(null);
      setSearchTerm('');
    }
  }, [value, selectedStrain]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Сбросить выбранный штамм если пользователь редактирует поле
    if (selectedStrain && !value.includes(selectedStrain.short_code)) {
      setSelectedStrain(null);
      onChange(undefined);
    }
  };

  const handleSelectStrain = (strain: ReferenceStrain) => {
    setSelectedStrain(strain);
    setSearchTerm(`${strain.short_code} - ${strain.display_name}`);
    onChange(strain.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Beaker className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Введите название штамма..."
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={disabled}
          required={required}
        />
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
        {loading && (
          <Loader2 className="absolute right-8 top-3 w-4 h-4 animate-spin text-blue-600" />
        )}
      </div>

      {/* Выпадающий список */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="p-3 text-center text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
              Поиск штаммов...
            </div>
          ) : filteredStrains.length > 0 ? (
            filteredStrains.map(strain => (
              <div
                key={strain.id}
                onClick={() => handleSelectStrain(strain)}
                className={`p-3 cursor-pointer hover:bg-blue-50 border-b border-gray-100 last:border-b-0 ${
                  selectedStrain?.id === strain.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="font-medium text-gray-900">{strain.short_code}</div>
                <div className="text-sm text-gray-600">{strain.display_name}</div>
              </div>
            ))
          ) : searchTerm ? (
            <div className="p-3 text-center text-gray-500">
              Штаммы не найдены
            </div>
          ) : (
            <div className="p-3 text-center text-gray-500">
              Начните вводить название штамма
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит для источников
const SourceAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  sources: ReferenceSource[];
  disabled?: boolean;
}> = ({ value, onChange, sources, disabled }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSources, setFilteredSources] = useState<ReferenceSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<ReferenceSource | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Фильтрация источников
  useEffect(() => {
    if (!searchTerm) {
      setFilteredSources(sources.slice(0, 50));
    } else {
      const filtered = sources.filter(source =>
        source.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        source.organism_name.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 50);
      setFilteredSources(filtered);
    }
  }, [searchTerm, sources]);

  // Загружаем источники при открытии
  useEffect(() => {
    if (isOpen) {
      setFilteredSources(sources.slice(0, 50));
    }
  }, [isOpen, sources]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Синхронизация внешнего value
  useEffect(() => {
    if (value && (!selectedSource || selectedSource.id !== value)) {
      const src = sources.find((s) => s.id === value);
      if (src) {
        setSelectedSource(src);
        setSearchTerm(`${src.organism_name} (${src.display_name})`);
      }
    }
    if (!value) {
      setSelectedSource(null);
      setSearchTerm('');
    }
  }, [value, sources, selectedSource]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Сбросить выбранный источник если пользователь редактирует поле
    if (selectedSource && !value.includes(selectedSource.organism_name)) {
      setSelectedSource(null);
      onChange(undefined);
    }
  };

  const handleSelectSource = (source: ReferenceSource) => {
    setSelectedSource(source);
    setSearchTerm(`${source.organism_name} (${source.display_name})`);
    onChange(source.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Введите источник..."
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={disabled}
        />
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
      </div>

      {/* Выпадающий список */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredSources.length > 0 ? (
            filteredSources.map(source => (
              <div
                key={source.id}
                onClick={() => handleSelectSource(source)}
                className={`p-3 cursor-pointer hover:bg-blue-50 border-b border-gray-100 last:border-b-0 ${
                  selectedSource?.id === source.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="font-medium text-gray-900">{source.organism_name}</div>
                <div className="text-sm text-gray-600">{source.display_name}</div>
              </div>
            ))
          ) : searchTerm ? (
            <div className="p-3 text-center text-gray-500">
              Источники не найдены
            </div>
          ) : (
            <div className="p-3 text-center text-gray-500">
              Начните вводить название источника
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит для местоположений
const LocationAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  locations: ReferenceLocation[];
  disabled?: boolean;
}> = ({ value, onChange, locations, disabled }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredLocations, setFilteredLocations] = useState<ReferenceLocation[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<ReferenceLocation | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Фильтрация местоположений
  useEffect(() => {
    if (!searchTerm) {
      setFilteredLocations(locations.slice(0, 50));
    } else {
      const filtered = locations.filter(location =>
        location.name.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 50);
      setFilteredLocations(filtered);
    }
  }, [searchTerm, locations]);

  // Загружаем местоположения при открытии
  useEffect(() => {
    if (isOpen) {
      setFilteredLocations(locations.slice(0, 50));
    }
  }, [isOpen, locations]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Синхронизация внешнего value
  useEffect(() => {
    if (value && (!selectedLocation || selectedLocation.id !== value)) {
      const loc = locations.find((l) => l.id === value);
      if (loc) {
        setSelectedLocation(loc);
        setSearchTerm(loc.name);
      }
    }
    if (!value) {
      setSelectedLocation(null);
      setSearchTerm('');
    }
  }, [value, locations, selectedLocation]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Сбросить выбранное местоположение если пользователь редактирует поле
    if (selectedLocation && !value.includes(selectedLocation.name)) {
      setSelectedLocation(null);
      onChange(undefined);
    }
  };

  const handleSelectLocation = (location: ReferenceLocation) => {
    setSelectedLocation(location);
    setSearchTerm(location.name);
    onChange(location.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Введите местоположение..."
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={disabled}
        />
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
      </div>

      {/* Выпадающий список */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredLocations.length > 0 ? (
            filteredLocations.map(location => (
              <div
                key={location.id}
                onClick={() => handleSelectLocation(location)}
                className={`p-3 cursor-pointer hover:bg-blue-50 border-b border-gray-100 last:border-b-0 ${
                  selectedLocation?.id === location.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="font-medium text-gray-900">{location.name}</div>
              </div>
            ))
          ) : searchTerm ? (
            <div className="p-3 text-center text-gray-500">
              Местоположения не найдены
            </div>
          ) : (
            <div className="p-3 text-center text-gray-500">
              Начните вводить название местоположения
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит для выбора бокса
const BoxAutocomplete: React.FC<{
  value: string | undefined;
  onChange: (value: string | undefined) => void;
  onBoxSelect?: (boxId: string) => void;
  disabled?: boolean;
  required?: boolean;
}> = ({ value, onChange, onBoxSelect, disabled, required }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredBoxes, setFilteredBoxes] = useState<{box_id: string, total_cells: number, free_cells: number, display_name: string}[]>([]);
  const [selectedBox, setSelectedBox] = useState<{box_id: string, display_name: string} | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Загрузка боксов с сервера
  const loadBoxes = async (search = '') => {
    setLoading(true);
    try {
      const url = buildSearchUrl(API_ENDPOINTS.boxes, search);
      
      const response = await fetch(url);
      const data = await response.json();
      setFilteredBoxes(data.boxes || []);
    } catch (error) {
      console.error('Ошибка загрузки боксов:', error);
      setFilteredBoxes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadBoxes(searchTerm);
    }
  }, [searchTerm, isOpen]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (value && !selectedBox) {
      // Поиск выбранного бокса в загруженных данных
      const box = filteredBoxes.find(b => b.box_id === value);
      if (box) {
        setSelectedBox({ box_id: box.box_id, display_name: box.display_name });
        setSearchTerm(box.display_name);
      }
    }
  }, [value, filteredBoxes, selectedBox]);

  const handleSelect = (box: {box_id: string, display_name: string}) => {
    setSelectedBox(box);
    setSearchTerm(box.display_name);
    onChange(box.box_id);
    onBoxSelect?.(box.box_id);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    
    if (!newSearchTerm) {
      setSelectedBox(null);
      onChange(undefined);
      onBoxSelect?.('');
    }
    
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Введите номер бокса..."
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              <span className="text-sm text-gray-500">Загрузка боксов...</span>
            </div>
          ) : filteredBoxes.length > 0 ? (
            filteredBoxes.map(box => (
              <div
                key={box.box_id}
                onClick={() => handleSelect({ box_id: box.box_id, display_name: box.display_name })}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-gray-900">Бокс {box.box_id}</div>
                <div className="text-sm text-gray-500">{box.free_cells} свободных из {box.total_cells} ячеек</div>
              </div>
            ))
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">
              Боксы не найдены
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит для выбора ячейки в боксе
const CellAutocomplete: React.FC<{
  boxId: string | undefined;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
  required?: boolean;
}> = ({ boxId, value, onChange, disabled, required }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredCells, setFilteredCells] = useState<{id: number, cell_id: string, display_name: string}[]>([]);
  const [selectedCell, setSelectedCell] = useState<{id: number, cell_id: string, display_name: string} | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Загрузка ячеек с сервера
  const loadCells = useCallback(async (search = '') => {
    if (!boxId) {
      setFilteredCells([]);
      return;
    }
    
    setLoading(true);
    try {
      const url = buildSearchUrl(API_ENDPOINTS.boxCells(parseInt(boxId)), search);
      
      const response = await fetch(url);
      const data = await response.json();
      setFilteredCells(data.cells || []);
    } catch (error) {
      console.error('Ошибка загрузки ячеек:', error);
      setFilteredCells([]);
    } finally {
      setLoading(false);
    }
  }, [boxId]);

  useEffect(() => {
    if (boxId) {
      loadCells(searchTerm);
    } else {
      setFilteredCells([]);
      setSelectedCell(null);
      setSearchTerm('');
      onChange(undefined);
    }
  }, [boxId, searchTerm, loadCells, onChange]);

  // Закрытие при клике вне области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (value && !selectedCell && filteredCells.length > 0) {
      // Поиск выбранной ячейки в загруженных данных
      const cell = filteredCells.find(c => c.id === value);
      if (cell) {
        setSelectedCell(cell);
        setSearchTerm(`Бокс ${boxId}, ${cell.display_name}`);
      }
    }
  }, [value, filteredCells, selectedCell, boxId]);

  const handleSelect = (cell: {id: number, cell_id: string, display_name: string}) => {
    setSelectedCell(cell);
    setSearchTerm(`Бокс ${boxId}, ${cell.display_name}`);
    onChange(cell.id);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    
    if (!newSearchTerm) {
      setSelectedCell(null);
      onChange(undefined);
    }
    
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder={boxId ? "Введите ячейку..." : "Сначала выберите бокс"}
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={() => boxId && setIsOpen(true)}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          disabled={disabled || !boxId}
          required={required}
        />
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
      </div>
      
      {isOpen && boxId && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center p-4">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              <span className="text-sm text-gray-500">Загрузка ячеек...</span>
            </div>
          ) : filteredCells.length > 0 ? (
            filteredCells.map(cell => (
              <div
                key={cell.id}
                onClick={() => handleSelect(cell)}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-gray-900">{cell.display_name}</div>
                <div className="text-sm text-gray-500">Бокс {boxId}</div>
              </div>
            ))
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">
              Свободные ячейки не найдены
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const AddSampleForm: React.FC<AddSampleFormProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  preSelectedStrainId 
}) => {
  const [loading, setLoading] = useState(false);
  const [loadingReferences, setLoadingReferences] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Справочные данные
  const [referenceData, setReferenceData] = useState<AddSampleReferenceData | null>(null);
  
  // Данные формы
  const [formData, setFormData] = useState<CreateSampleData>({
    strain_id: preSelectedStrainId,
    index_letter_id: undefined,
    storage_id: undefined,
    original_sample_number: '',
    source_id: undefined,
    location_id: undefined,
    appendix_note_id: undefined,
    comment_id: undefined,
    has_photo: false,
    is_identified: false,
    has_antibiotic_activity: false,
    has_genome: false,
    has_biochemistry: false,
    seq_status: false,
  });

  // Состояние для двухэтапного выбора хранения
  const [selectedBoxId, setSelectedBoxId] = useState<string | undefined>(undefined);

  // Загрузка справочных данных
  useEffect(() => {
    const loadReferenceData = async () => {
      if (!isOpen) return;
      
      setLoadingReferences(true);
      try {
        const response = await fetch(API_ENDPOINTS.referenceData);
        const data = await response.json();
        setReferenceData(data);
      } catch (err) {
        console.error('Ошибка загрузки справочных данных:', err);
        setError('Не удалось загрузить справочные данные');
      } finally {
        setLoadingReferences(false);
      }
    };

    loadReferenceData();
  }, [isOpen]);

  // Установка предвыбранного штамма
  useEffect(() => {
    if (preSelectedStrainId) {
      setFormData(prev => ({
        ...prev,
        strain_id: preSelectedStrainId
      }));
    }
  }, [preSelectedStrainId]);

  // Обработка клавиши Esc
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && onClose) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Базовая валидация
    if (!formData.strain_id) {
      setError('Необходимо выбрать штамм');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiService.createSample(formData);
      
      // Сброс формы
      setFormData({
        strain_id: preSelectedStrainId || undefined,
        index_letter_id: undefined,
        storage_id: undefined,
        original_sample_number: '',
        source_id: undefined,
        location_id: undefined,
        appendix_note_id: undefined,
        comment_id: undefined,
        has_photo: false,
        is_identified: false,
        has_antibiotic_activity: false,
        has_genome: false,
        has_biochemistry: false,
        seq_status: false,
      });
      
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
      setError(error.response?.data?.error || error.message || 'Ошибка при создании образца');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof CreateSampleData, value: unknown) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[95vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Beaker className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Добавить образец</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(95vh-140px)]">
          <div className="p-6 space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* Loading Reference Data */}
            {loadingReferences && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <p className="text-blue-600 text-sm">Загрузка справочных данных...</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Штамм (обязательное поле) с автокомплитом */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Штамм <span className="text-red-500">*</span>
                </label>
                <StrainAutocomplete
                  value={formData.strain_id}
                  onChange={(value) => handleFieldChange('strain_id', value)}
                  disabled={loadingReferences}
                  required
                />
              </div>

              {/* Место хранения - Выбор бокса */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Бокс хранения
                </label>
                <BoxAutocomplete
                  value={selectedBoxId}
                  onChange={(boxId) => {
                    setSelectedBoxId(boxId);
                    // Сбрасываем выбранную ячейку при смене бокса
                    handleFieldChange('storage_id', undefined);
                  }}
                  onBoxSelect={(boxId) => setSelectedBoxId(boxId)}
                    disabled={loadingReferences}
                  />
                </div>

              {/* Место хранения - Выбор ячейки */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Ячейка в боксе
                </label>
                <CellAutocomplete
                  boxId={selectedBoxId}
                  value={formData.storage_id}
                  onChange={(value) => handleFieldChange('storage_id', value)}
                  disabled={loadingReferences || !selectedBoxId}
                />
              </div>

              {/* Номер образца */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Номер образца
                </label>
                <input
                  type="text"
                  value={formData.original_sample_number || ''}
                  onChange={(e) => handleFieldChange('original_sample_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Введите номер образца"
                />
              </div>

              {/* Источник */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Источник
                </label>
                <SourceAutocomplete
                  value={formData.source_id}
                  onChange={(value) => handleFieldChange('source_id', value)}
                  sources={referenceData?.sources || []}
                  disabled={loadingReferences}
                />
              </div>

              {/* Местоположение */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Местоположение
                </label>
                <LocationAutocomplete
                  value={formData.location_id}
                  onChange={(value) => handleFieldChange('location_id', value)}
                  locations={referenceData?.locations || []}
                  disabled={loadingReferences}
                />
              </div>

              {/* Индексная буква */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Индексная буква
                </label>
                <select
                  value={formData.index_letter_id || ''}
                  onChange={(e) => handleFieldChange('index_letter_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loadingReferences}
                >
                  <option value="">Выберите индексную букву</option>
                  {referenceData?.index_letters.map((letter: ReferenceIndexLetter) => (
                    <option key={letter.id} value={letter.id}>
                      {letter.letter_value}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Характеристики образца */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Характеристики образца</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.has_photo}
                    onChange={(e) => handleFieldChange('has_photo', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Есть фото</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.is_identified}
                    onChange={(e) => handleFieldChange('is_identified', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Идентифицирован</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.has_antibiotic_activity}
                    onChange={(e) => handleFieldChange('has_antibiotic_activity', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Антибиотическая активность</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.has_genome}
                    onChange={(e) => handleFieldChange('has_genome', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Есть геном</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.has_biochemistry}
                    onChange={(e) => handleFieldChange('has_biochemistry', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Есть биохимия</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.seq_status}
                    onChange={(e) => handleFieldChange('seq_status', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Секвенирован</span>
                </label>
              </div>
            </div>

            {/* Дополнительные поля */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Комментарий */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Комментарий
                </label>
                <select
                  value={formData.comment_id || ''}
                  onChange={(e) => handleFieldChange('comment_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loadingReferences}
                >
                  <option value="">Выберите комментарий</option>
                  {referenceData?.comments.map((comment: ReferenceComment) => (
                    <option key={comment.id} value={comment.id}>
                      {comment.text}
                    </option>
                  ))}
                </select>
              </div>

              {/* Примечание */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Примечание
                </label>
                <select
                  value={formData.appendix_note_id || ''}
                  onChange={(e) => handleFieldChange('appendix_note_id', e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loadingReferences}
                >
                  <option value="">Выберите примечание</option>
                  {referenceData?.appendix_notes.map((note: ReferenceAppendixNote) => (
                    <option key={note.id} value={note.id}>
                      {note.text}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || loadingReferences}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Создание...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Создать образец</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddSampleForm; 