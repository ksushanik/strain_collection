import React, { useState, useEffect, useRef, useMemo } from 'react';
import { X, Save, Loader2, Beaker, Search, ChevronDown } from 'lucide-react';
import apiService from '../services/api';
import { API_ENDPOINTS, buildSearchUrl } from '../config/api';
import type {
  Sample,
  UpdateSampleData,
  ReferenceStrain,
  ReferenceSource,
  ReferenceLocation,
  ReferenceStorage
} from '../types';

interface EditSampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  sampleId: number;
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

interface ReferenceGrowthMedium {
  id: number;
  name: string;
  description?: string;
}

interface EditSampleReferenceData {
  strains: ReferenceStrain[];
  sources: ReferenceSource[];
  locations: ReferenceLocation[];
  free_storage: ReferenceStorage[];
  index_letters: ReferenceIndexLetter[];
  comments: ReferenceComment[];
  appendix_notes: ReferenceAppendixNote[];
  growth_media: ReferenceGrowthMedium[];
}

// Компонент для выбора сред роста с множественным выбором
const GrowthMediaSelector: React.FC<{
  value: number[];
  onChange: (value: number[]) => void;
  growthMedia: ReferenceGrowthMedium[];
  disabled?: boolean;
}> = ({ value, onChange, growthMedia, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Фильтрация сред роста
  const filteredMedia = useMemo(() => {
    if (!searchTerm) return growthMedia;
    return growthMedia.filter(media =>
      media.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (media.description && media.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [growthMedia, searchTerm]);

  const handleToggle = (mediaId: number) => {
    const newValue = value.includes(mediaId)
      ? value.filter(id => id !== mediaId)
      : [...value, mediaId];
    onChange(newValue);
  };

  const handleRemove = (mediaId: number) => {
    onChange(value.filter(id => id !== mediaId));
  };

  const selectedMedia = growthMedia.filter(media => value.includes(media.id));

  return (
    <div className="relative">
      <div className="relative">
        <div
          className="w-full min-h-[40px] px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer bg-white"
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          {selectedMedia.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {selectedMedia.map(media => (
                <span
                  key={media.id}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                >
                  {media.name}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(media.id);
                    }}
                    className="ml-1 hover:text-blue-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <span className="text-gray-500">Выберите среды роста...</span>
          )}
        </div>
        <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-gray-400" />
      </div>

      {/* Выпадающий список */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {/* Поле поиска */}
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              placeholder="Поиск сред роста..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {/* Список сред роста */}
          <div className="p-1">
            {filteredMedia.length > 0 ? (
              filteredMedia.map(media => (
                <label
                  key={media.id}
                  className="flex items-center px-2 py-1 hover:bg-gray-100 cursor-pointer rounded"
                >
                  <input
                    type="checkbox"
                    checked={value.includes(media.id)}
                    onChange={() => handleToggle(media.id)}
                    className="mr-2 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{media.name}</div>
                    {media.description && (
                      <div className="text-xs text-gray-500">{media.description}</div>
                    )}
                  </div>
                </label>
              ))
            ) : (
              <div className="px-2 py-1 text-sm text-gray-500">
                Среды роста не найдены
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Автокомплит компонент для штаммов
const StrainAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  strains: ReferenceStrain[];
  disabled?: boolean;
  required?: boolean;
}> = ({ value, onChange, strains, disabled, required }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Найти текущий выбранный штамм
  const selectedStrain = strains.find(s => s.id === value);

  // Фильтрация штаммов
  const filteredStrains = useMemo(() => {
    if (!searchTerm) return strains.slice(0, 50);
    return strains.filter(strain =>
      strain.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      strain.short_code.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 50);
  }, [strains, searchTerm]);

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);

    // Сбросить выбранный штамм если пользователь редактирует поле
    if (selectedStrain && !newValue.includes(selectedStrain.short_code)) {
      onChange(undefined);
    }
  };

  const handleSelectStrain = (strain: ReferenceStrain) => {
    setSearchTerm(`${strain.short_code} - ${strain.display_name}`);
    onChange(strain.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  // Установить начальное значение при изменении value
  useEffect(() => {
    if (selectedStrain) {
      setSearchTerm(`${selectedStrain.short_code} - ${selectedStrain.display_name}`);
    } else if (!value) {
      setSearchTerm('');
    }
  }, [selectedStrain, value]);

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
      </div>

      {/* Выпадающий список */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredStrains.length > 0 ? (
            filteredStrains.map(strain => (
              <div
                key={strain.id}
                onClick={() => handleSelectStrain(strain)}
                className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-sm">{strain.display_name}</div>
                {strain.short_code !== strain.display_name.split(' - ')[0] && (
                  <div className="text-xs text-gray-500">Код: {strain.short_code}</div>
                )}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-gray-500">
              Штаммы не найдены
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит компонент для источников
const SourceAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  sources: ReferenceSource[];
  disabled?: boolean;
}> = ({ value, onChange, sources, disabled }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Найти текущий выбранный источник
  const selectedSource = sources.find(s => s.id === value);

  // Фильтрация источников
  const filteredSources = useMemo(() => {
    if (!searchTerm) return sources.slice(0, 50);
    return sources.filter(source =>
      source.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.organism_name.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 50);
  }, [sources, searchTerm]);

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);

    // Сбросить выбранный источник если пользователь редактирует поле
    if (selectedSource && !newValue.includes(selectedSource.organism_name)) {
      onChange(undefined);
    }
  };

  const handleSelectSource = (source: ReferenceSource) => {
    setSearchTerm(source.display_name);
    onChange(source.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  // Установить начальное значение при изменении value
  useEffect(() => {
    if (selectedSource) {
      setSearchTerm(selectedSource.display_name);
    } else if (!value) {
      setSearchTerm('');
    }
  }, [selectedSource, value]);

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Выберите источник..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-sm">{source.display_name}</div>
                <div className="text-xs text-gray-500">{source.source_type}</div>
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-gray-500">
              Источники не найдены
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Автокомплит компонент для местоположений
const LocationAutocomplete: React.FC<{
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  locations: ReferenceLocation[];
  disabled?: boolean;
}> = ({ value, onChange, locations, disabled }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Найти текущее выбранное местоположение
  const selectedLocation = locations.find(l => l.id === value);

  // Фильтрация местоположений
  const filteredLocations = useMemo(() => {
    if (!searchTerm) return locations.slice(0, 50);
    return locations.filter(location =>
      location.name.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 50);
  }, [locations, searchTerm]);

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);

    // Сбросить выбранное местоположение если пользователь редактирует поле
    if (selectedLocation && !newValue.includes(selectedLocation.name)) {
      onChange(undefined);
    }
  };

  const handleSelectLocation = (location: ReferenceLocation) => {
    setSearchTerm(location.name);
    onChange(location.id);
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  // Установить начальное значение при изменении value
  useEffect(() => {
    if (selectedLocation) {
      setSearchTerm(selectedLocation.name);
    } else if (!value) {
      setSearchTerm('');
    }
  }, [selectedLocation, value]);

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder="Выберите местоположение..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <div className="font-medium text-sm">{location.name}</div>
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-gray-500">
              Местоположения не найдены
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const EditSampleForm: React.FC<EditSampleFormProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  sampleId 
}) => {
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [loadingReferences, setLoadingReferences] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Справочные данные
  const [referenceData, setReferenceData] = useState<EditSampleReferenceData | null>(null);
  const [currentSample, setCurrentSample] = useState<Sample | null>(null);

  // Данные формы
  const [formData, setFormData] = useState<UpdateSampleData>({
    strain_id: undefined,
    index_letter_id: undefined,
    storage_id: undefined,
    original_sample_number: '',
    source_id: undefined,
    location_id: undefined,
    appendix_note_text: '',
    comment_text: '',
    has_photo: false,
    is_identified: false,
    has_antibiotic_activity: false,
    has_genome: false,
    has_biochemistry: false,
    seq_status: false,
    mobilizes_phosphates: false,
    stains_medium: false,
    produces_siderophores: false,
    produces_iuk: false,
    produces_amylase: false,
    iuk_color: '',
    amylase_variant: '',
    growth_media_ids: [],
  });



  // Фотографии
  const [newPhotos, setNewPhotos] = useState<File[]>([]);
  const handlePhotoSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setNewPhotos(prev => [...prev, ...files]);
    }
  };

  // Загрузка данных образца и справочной информации
  useEffect(() => {
    const loadData = async () => {
      if (!isOpen || !sampleId) return;
      
      setLoadingData(true);
      setLoadingReferences(true);
      setError(null);

      try {
        // Загружаем данные параллельно
        const [sampleData, referenceDataResponse] = await Promise.all([
          apiService.getSample(sampleId),
          apiService.getReferenceData()
        ]);

        // Обработка справочных данных
        const referenceData: EditSampleReferenceData = {
          strains: referenceDataResponse.strains || [],
          sources: referenceDataResponse.sources || [],
          locations: referenceDataResponse.locations || [],
          free_storage: referenceDataResponse.free_storage || [],
          index_letters: referenceDataResponse.index_letters || [],
          comments: referenceDataResponse.comments || [],
          appendix_notes: referenceDataResponse.appendix_notes || [],
          growth_media: referenceDataResponse.growth_media || [],
        };

        setCurrentSample(sampleData);
        setReferenceData(referenceData);

        // Заполняем форму данными образца
        setFormData({
          strain_id: sampleData.strain?.id,
          index_letter_id: sampleData.index_letter?.id,
          storage_id: sampleData.storage?.id,
          original_sample_number: sampleData.original_sample_number || '',
          source_id: sampleData.source?.id,
          location_id: sampleData.location?.id,
          appendix_note_text: sampleData.appendix_note_text || '',
          comment_text: sampleData.comment_text || '',
          has_photo: sampleData.has_photo,
          is_identified: sampleData.is_identified,
          has_antibiotic_activity: sampleData.has_antibiotic_activity,
          has_genome: sampleData.has_genome,
          has_biochemistry: sampleData.has_biochemistry,
          seq_status: sampleData.seq_status,
          mobilizes_phosphates: sampleData.mobilizes_phosphates,
          stains_medium: sampleData.stains_medium,
          produces_siderophores: sampleData.produces_siderophores,
          produces_iuk: sampleData.produces_iuk,
          produces_amylase: sampleData.produces_amylase,
          iuk_color: sampleData.iuk_color || '',
          amylase_variant: sampleData.amylase_variant || '',
          growth_media_ids: sampleData.growth_media?.map(media => media.id) || [],
        });

      } catch (err: any) {
        console.error('Ошибка загрузки данных:', err);
        setError(err.response?.data?.error || err.message || 'Ошибка загрузки данных');
      } finally {
        setLoadingData(false);
        setLoadingReferences(false);
      }
    };

    loadData();
  }, [isOpen, sampleId]);



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
      await apiService.updateSample(sampleId, formData);

      // Загружаем фотографии, если выбраны
      if (newPhotos.length > 0) {
        try {
          await apiService.uploadSamplePhotos(sampleId, newPhotos);
        } catch (uploadErr) {
          console.error('Ошибка загрузки фотографий:', uploadErr);
        }
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Ошибка при обновлении образца');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof UpdateSampleData, value: any) => {
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
            <h2 className="text-lg font-semibold text-gray-900">
              Редактировать образец #{sampleId}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Loading State */}
        {loadingData && (
          <div className="p-6">
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <p className="text-gray-600">Загрузка данных образца...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loadingData && (
          <div className="p-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Form */}
        {!loadingData && !error && currentSample && (
          <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(95vh-140px)]">
            <div className="p-6 space-y-6">
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
                {/* Штамм (обязательное поле) */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Штамм <span className="text-red-500">*</span>
                  </label>
                  <StrainAutocomplete
                    value={formData.strain_id}
                    onChange={(value) => handleFieldChange('strain_id', value)}
                    strains={referenceData?.strains || []}
                    disabled={loadingReferences}
                    required
                  />
                </div>

                {/* Место хранения */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Место хранения
                  </label>
                  <select
                    value={formData.storage_id || ''}
                    onChange={(e) => handleFieldChange('storage_id', e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Выберите ячейку</option>
                    {/* Добавляем текущее место хранения, если оно есть */}
                    {currentSample?.storage && !referenceData?.free_storage.find(s => s.id === currentSample.storage?.id) && (
                      <option key={currentSample.storage.id} value={currentSample.storage.id}>
                        {`${currentSample.storage.box_id} - ${currentSample.storage.cell_id} (текущее)`}
                      </option>
                    )}
                    {referenceData?.free_storage.map(storage => (
                      <option key={storage.id} value={storage.id}>
                        {storage.display_name}
                      </option>
                    ))}
                  </select>
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
                    {referenceData?.index_letters.map(letter => (
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

                  {/* Новые характеристики */}
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.mobilizes_phosphates}
                      onChange={(e) => handleFieldChange('mobilizes_phosphates', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Мобилизует фосфаты</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.stains_medium}
                      onChange={(e) => handleFieldChange('stains_medium', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Окрашивает среду</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.produces_siderophores}
                      onChange={(e) => handleFieldChange('produces_siderophores', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Вырабатывает сидерофоры</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.produces_iuk}
                      onChange={(e) => handleFieldChange('produces_iuk', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Вырабатывает ИУК</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.produces_amylase}
                      onChange={(e) => handleFieldChange('produces_amylase', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Вырабатывает амилазу</span>
                  </label>
                </div>

                {/* Условные поля для ИУК и амилазы */}
                {(formData.produces_iuk || formData.produces_amylase) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                    {formData.produces_iuk && (
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700">
                          Цвет окраски ИУК
                        </label>
                        <input
                          type="text"
                          value={formData.iuk_color || ''}
                          onChange={(e) => handleFieldChange('iuk_color', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Введите цвет окраски"
                        />
                      </div>
                    )}

                    {formData.produces_amylase && (
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700">
                          Вариант амилазы
                        </label>
                        <input
                          type="text"
                          value={formData.amylase_variant || ''}
                          onChange={(e) => handleFieldChange('amylase_variant', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Введите вариант амилазы"
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Комментарий и примечание */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Комментарий */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Комментарий
                  </label>
                  <textarea
                    value={formData.comment_text || ''}
                    onChange={(e) => handleFieldChange('comment_text', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Введите комментарий к образцу"
                  />
                </div>

                {/* Примечание */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Примечание
                  </label>
                  <textarea
                    value={formData.appendix_note_text || ''}
                    onChange={(e) => handleFieldChange('appendix_note_text', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Введите примечание к образцу"
                  />
                </div>
              </div>

              {/* Среды роста */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Среды роста
                </label>
                <GrowthMediaSelector
                  value={formData.growth_media_ids || []}
                  onChange={(value) => handleFieldChange('growth_media_ids', value)}
                  growthMedia={referenceData?.growth_media || []}
                  disabled={loadingReferences}
                />
              </div>

              {/* Фотографии */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Фотографии
                </label>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png"
                  onChange={handlePhotoSelection}
                />
                {newPhotos.length > 0 && (
                  <div className="grid grid-cols-4 gap-2 mt-2">
                    {newPhotos.map((file, idx) => (
                      <img
                        key={`${file.name}-${file.size}-${idx}`}
                        src={URL.createObjectURL(file)}
                        alt="preview"
                        className="w-full h-20 object-cover rounded"
                      />
                    ))}
                  </div>
                )}
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
                    <span>Сохранение...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Сохранить изменения</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default EditSampleForm; 