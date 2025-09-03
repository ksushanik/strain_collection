import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Beaker } from 'lucide-react';
import apiService from '../services/api';
import type { 
  Sample,
  UpdateSampleData, 
  ReferenceData,
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
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [currentSample, setCurrentSample] = useState<Sample | null>(null);
  
  // Данные формы
  const [formData, setFormData] = useState<UpdateSampleData>({
    strain_id: undefined,
    index_letter_id: undefined,
    storage_id: undefined,
    original_sample_number: '',
    source_id: undefined,
    location_id: undefined,
    appendix_note: '',
    comment: '',
    has_photo: false,
    is_identified: false,
    has_antibiotic_activity: false,
    has_genome: false,
    has_biochemistry: false,
    seq_status: false,
    // Новые характеристики
    mobilizes_phosphates: false,
    stains_medium: false,
    produces_siderophores: false,
    iuk_color_id: undefined,
    amylase_variant_id: undefined,
    growth_medium_ids: [],
  });

  // Поиск в выпадающих списках (отключен)
  const [searchTerms] = useState({
    strain: '',
    source: '',
    location: '',
    storage: ''
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
        const [sampleData, referenceData] = await Promise.all([
          apiService.getSample(sampleId),
          apiService.getReferenceData()
        ]);

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
          appendix_note: sampleData.appendix_note || '',
          comment: sampleData.comment || '',
          has_photo: sampleData.has_photo,
          is_identified: sampleData.is_identified,
          has_antibiotic_activity: sampleData.has_antibiotic_activity,
          has_genome: sampleData.has_genome,
          has_biochemistry: sampleData.has_biochemistry,
          seq_status: sampleData.seq_status,
          // Новые характеристики
          mobilizes_phosphates: sampleData.mobilizes_phosphates,
          stains_medium: sampleData.stains_medium,
          produces_siderophores: sampleData.produces_siderophores,
          iuk_color_id: sampleData.iuk_color?.id,
          amylase_variant_id: sampleData.amylase_variant?.id,
          growth_medium_ids: sampleData.growth_media?.map(m => m.id) || [],
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

  // Фильтрация справочных данных по поиску
  const getFilteredStrains = (): ReferenceStrain[] => {
    if (!referenceData) return [];

    // Начальный список
    let strains = [...referenceData.strains];

    // Гарантируем наличие текущего штамма в списке
    if (currentSample?.strain) {
      // Проверяем, есть ли уже этот штамм в списке
      const existingIndex = strains.findIndex(s => s.id === currentSample.strain!.id);
      if (existingIndex >= 0) {
        // Обновляем существующий штамм, добавляя "(текущий)"
        const displayNameBase = currentSample.strain.short_code || currentSample.strain.identifier || `ID ${currentSample.strain.id}`;
        strains[existingIndex] = {
          ...strains[existingIndex],
          display_name: `${displayNameBase} (текущий)`
        };
        // Перемещаем в начало списка
        const currentStrain = strains.splice(existingIndex, 1)[0];
        strains.unshift(currentStrain);
      } else {
        // Добавляем новый штамм в начало списка
        const displayNameBase = currentSample.strain.short_code || currentSample.strain.identifier || `ID ${currentSample.strain.id}`;
        strains.unshift({
          id: currentSample.strain.id,
          short_code: currentSample.strain.short_code,
          identifier: currentSample.strain.identifier,
          display_name: `${displayNameBase} (текущий)`
        });
      }
    }

    // Если задан поисковый термин – фильтруем
    if (searchTerms.strain) {
      strains = strains.filter(strain =>
        strain.display_name.toLowerCase().includes(searchTerms.strain.toLowerCase()) ||
        strain.short_code.toLowerCase().includes(searchTerms.strain.toLowerCase())
      );
    }

    return strains.slice(0, 50);
  };

  const getFilteredSources = (): ReferenceSource[] => {
    if (!referenceData) return [];
    let sources = [...referenceData.sources];

    // Добавляем текущий источник в начало списка
    if (currentSample?.source) {
      const existingIndex = sources.findIndex(s => s.id === currentSample.source!.id);
      if (existingIndex >= 0) {
        // Обновляем существующий источник, добавляя "(текущий)"
        sources[existingIndex] = {
          ...sources[existingIndex],
          display_name: `${currentSample.source.organism_name} (текущий)`
        };
        // Перемещаем в начало списка
        const currentSource = sources.splice(existingIndex, 1)[0];
        sources.unshift(currentSource);
      } else {
        // Добавляем новый источник в начало списка
        sources.unshift({
          ...currentSample.source,
          display_name: `${currentSample.source.organism_name} (текущий)`
        } as ReferenceSource);
      }
    }

    if (searchTerms.source) {
      sources = sources.filter(source =>
        source.display_name.toLowerCase().includes(searchTerms.source.toLowerCase()) ||
        source.organism_name.toLowerCase().includes(searchTerms.source.toLowerCase())
      );
    }

    return sources.slice(0, 50);
  };

  const getFilteredLocations = (): ReferenceLocation[] => {
    if (!referenceData) return [];
    let locations = [...referenceData.locations];

    // Гарантируем наличие текущего местоположения
    if (currentSample?.location) {
      const existingIndex = locations.findIndex(l => l.id === currentSample.location!.id);
      if (existingIndex >= 0) {
        // Обновляем существующее местоположение, добавляя "(текущее)"
        locations[existingIndex] = {
          ...locations[existingIndex],
          name: `${currentSample.location.name} (текущее)`
        };
        // Перемещаем в начало списка
        const currentLocation = locations.splice(existingIndex, 1)[0];
        locations.unshift(currentLocation);
      } else {
        // Добавляем новое местоположение в начало списка
        locations.unshift({
          id: currentSample.location.id,
          name: `${currentSample.location.name} (текущее)`
        });
      }
    }

    if (searchTerms.location) {
      locations = locations.filter(location =>
        location.name.toLowerCase().includes(searchTerms.location.toLowerCase())
      );
    }

    return locations.slice(0, 50);
  };

  const getFilteredStorage = (): ReferenceStorage[] => {
    if (!referenceData) return [];
    
    // Добавляем текущее место хранения в список доступных, если оно есть
    let availableStorage = [...referenceData.free_storage];
    if (currentSample?.storage && !availableStorage.find(s => s.id === currentSample.storage?.id)) {
      availableStorage.unshift({
        id: currentSample.storage.id,
        box_id: currentSample.storage.box_id,
        cell_id: currentSample.storage.cell_id,
        display_name: `${currentSample.storage.box_id} - ${currentSample.storage.cell_id} (текущее)`
      });
    }

    if (!searchTerms.storage) return availableStorage.slice(0, 50);
    
    return availableStorage.filter(storage =>
      storage.display_name.toLowerCase().includes(searchTerms.storage.toLowerCase()) ||
      storage.box_id.toLowerCase().includes(searchTerms.storage.toLowerCase()) ||
      storage.cell_id.toLowerCase().includes(searchTerms.storage.toLowerCase())
    ).slice(0, 50);
  };

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
                  <select
                    value={formData.strain_id || ''}
                    onChange={(e) => handleFieldChange('strain_id', e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                    required
                  >
                    <option value="">Выберите штамм</option>
                    {getFilteredStrains().map(strain => (
                      <option key={strain.id} value={strain.id}>
                        {strain.display_name}
                      </option>
                    ))}
                  </select>
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
                    {getFilteredStorage().map(storage => (
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
                  <select
                    value={formData.source_id || ''}
                    onChange={(e) => handleFieldChange('source_id', e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Выберите источник</option>
                    {getFilteredSources().map(source => (
                      <option key={source.id} value={source.id}>
                        {source.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Местоположение */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Местоположение
                  </label>
                  <select
                    value={formData.location_id || ''}
                    onChange={(e) => handleFieldChange('location_id', e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Выберите местоположение</option>
                    {getFilteredLocations().map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
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
                  {/* Старые характеристики */}
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
                      className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-700">Мобилизирует фосфаты</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.stains_medium}
                      onChange={(e) => handleFieldChange('stains_medium', e.target.checked)}
                      className="w-4 h-4 text-pink-600 border-gray-300 rounded focus:ring-pink-500"
                    />
                    <span className="text-sm text-gray-700">Окрашивает среду</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.produces_siderophores}
                      onChange={(e) => handleFieldChange('produces_siderophores', e.target.checked)}
                      className="w-4 h-4 text-cyan-600 border-gray-300 rounded focus:ring-cyan-500"
                    />
                    <span className="text-sm text-gray-700">Вырабатывает сидерофоры</span>
                  </label>
                </div>

                {/* Дополнительные поля для новых характеристик */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                  {/* ИУК цвет */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Цвет ИУК (если вырабатывает)
                    </label>
                    <select
                      value={formData.iuk_color_id || ''}
                      onChange={(e) => handleFieldChange('iuk_color_id', e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      disabled={loadingReferences}
                    >
                      <option value="">Не выбрано</option>
                      <option value="1">Синий</option>
                      <option value="2">Красный</option>
                      <option value="3">Желтый</option>
                      <option value="4">Зеленый</option>
                      <option value="5">Фиолетовый</option>
                    </select>
                  </div>

                  {/* Вариант амилазы */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Вариант амилазы (если вырабатывает)
                    </label>
                    <select
                      value={formData.amylase_variant_id || ''}
                      onChange={(e) => handleFieldChange('amylase_variant_id', e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500 focus:border-transparent"
                      disabled={loadingReferences}
                    >
                      <option value="">Не выбрано</option>
                      <option value="1">Высокая активность</option>
                      <option value="2">Средняя активность</option>
                      <option value="3">Низкая активность</option>
                      <option value="4">Отсутствует</option>
                    </select>
                  </div>
                </div>

                {/* Среды роста */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Среды роста (выберите несколько)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      { id: 1, name: 'LB-агар' },
                      { id: 2, name: 'ТСА' },
                      { id: 3, name: 'МПА' },
                      { id: 4, name: 'Сабуро' },
                      { id: 5, name: 'Чапека' },
                      { id: 6, name: 'Картофельно-глюкозный агар' },
                    ].map((medium) => (
                      <label key={medium.id} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.growth_medium_ids?.includes(medium.id) || false}
                          onChange={(e) => {
                            const currentIds = formData.growth_medium_ids || [];
                            if (e.target.checked) {
                              handleFieldChange('growth_medium_ids', [...currentIds, medium.id]);
                            } else {
                              handleFieldChange('growth_medium_ids', currentIds.filter(id => id !== medium.id));
                            }
                          }}
                          className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">{medium.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Дополнительные поля */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Комментарий */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Комментарий
                  </label>
                  <textarea
                    value={formData.comment || ''}
                    onChange={(e) => handleFieldChange('comment', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={4}
                    placeholder="Введите комментарий"
                    disabled={loadingReferences}
                  />
                </div>

                {/* Примечание */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Примечание
                  </label>
                  <textarea
                    value={formData.appendix_note || ''}
                    onChange={(e) => handleFieldChange('appendix_note', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={4}
                    placeholder="Введите примечание"
                    disabled={loadingReferences}
                  />
                </div>
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