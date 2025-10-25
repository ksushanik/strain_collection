import React, { useState, useEffect, useMemo } from 'react';
import { X, Plus, Loader2, Beaker, Dna } from 'lucide-react';
import { isAxiosError } from 'axios';
import apiService from '../../../../services/api';
import type { 
  CreateSampleData, 
  ReferenceLocation,
  ReferenceIndexLetter,
  Strain,
  IUKColor,
  AmylaseVariant,
  GrowthMedium
} from '../../../../types';
import {
  StrainAutocomplete,
  SourceAutocomplete,
  PhotoUpload,
  CreateStrainForm} from '../index';
import { StorageManager, type StorageCell } from '../StorageManager';
import { Select, Input, Textarea, Autocomplete } from '../../../../shared/components';

type SimpleReferenceSource = {
  id: number;
  name: string;
};

interface AddSampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  preSelectedStrainId?: number;
}

interface AddSampleReferenceData {
  sources: SimpleReferenceSource[];
  locations: ReferenceLocation[];
  index_letters: ReferenceIndexLetter[];
  iuk_colors: IUKColor[];
  amylase_variants: AmylaseVariant[];
  growth_media: GrowthMedium[];
}

export const AddSampleForm: React.FC<AddSampleFormProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess,
  preSelectedStrainId 
}) => {
  const [loading, setLoading] = useState(false);
  const [loadingReferences, setLoadingReferences] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ strain_id?: string; storage_id?: string }>({});
  
  // Справочные данные
  const [referenceData, setReferenceData] = useState<AddSampleReferenceData | null>(null);
  
  // Новые состояния для выбора штамма
  const [strainSelectionMode, setStrainSelectionMode] = useState<'existing' | 'new'>('existing');
  const [showCreateStrainForm, setShowCreateStrainForm] = useState(false);
  
  // Данные формы
  const [formData, setFormData] = useState<CreateSampleData>({
    strain_id: preSelectedStrainId,
    index_letter_id: undefined,
    storage_id: undefined,
    original_sample_number: '',
    source_id: undefined,
    location_id: undefined,
    appendix_note: '',
    comment: '',
    iuk_color_id: undefined,
    amylase_variant_id: undefined,
    growth_media_ids: [],
  });
  
  // Состояние для управления ячейками хранения
  const [storageCells, setStorageCells] = useState<StorageCell[]>([]);
  
  // Фотографии
  const [newPhotos, setNewPhotos] = useState<File[]>([]);

  const sourceOptions = useMemo(() => (
    (referenceData?.sources || []).map((source) => ({
      id: source.id,
      display_name: source.name,
      secondary_text: source.name,
    }))
  ), [referenceData?.sources]);

  const locationOptions = useMemo(() => (
    (referenceData?.locations || []).map((location) => ({
      id: location.id,
      display_name: location.name,
    }))
  ), [referenceData?.locations]);

  const indexLetterOptions = useMemo(() => (
    (referenceData?.index_letters || []).map((letter) => ({
      id: letter.id,
      display_name: letter.letter_value,
    }))
  ), [referenceData?.index_letters]);

  const currentSourceName = useMemo(() => {
    if (!formData.source_id || !referenceData) {
      return undefined;
    }

    return referenceData.sources.find(source => source.id === formData.source_id)?.name;
  }, [formData.source_id, referenceData]);

  // Загрузка справочных данных
  useEffect(() => {
    if (isOpen) {
      loadReferenceData();
    }
  }, [isOpen]);

  const loadReferenceData = async () => {
    setLoadingReferences(true);
    setError(null);
    
    try {
      const referenceData = await apiService.getReferenceData();

      setReferenceData({
        sources: referenceData.sources || [],
        locations: referenceData.locations || [],
        index_letters: referenceData.index_letters || [],
        iuk_colors: referenceData.iuk_colors || [],
        amylase_variants: referenceData.amylase_variants || [],
        growth_media: referenceData.growth_media || [],
      });
    } catch (error) {
      console.error('Ошибка при загрузке справочных данных:', error);
      setError('Не удалось загрузить справочные данные');
    } finally {
      setLoadingReferences(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setFieldErrors({});

    if (!formData.strain_id) {
      setFieldErrors(prev => ({ ...prev, strain_id: 'Требуется выбрать штамм' }));
      setError('Выберите штамм');
      return;
    }

    // Проверяем, что выбрана хотя бы одна ячейка хранения
    if (storageCells.length === 0) {
      setFieldErrors(prev => ({ ...prev, storage_id: 'Требуется выбрать место хранения' }));
      setError('Выберите место хранения');
      return;
    }

    // Устанавливаем основную ячейку как storage_id
    const primaryCell = storageCells[0];
    const updatedFormData = {
      ...formData,
      storage_id: primaryCell.id
    };

    setLoading(true);
    setError(null);

    try {
      // Создаем образец
      const result = await apiService.createSample(updatedFormData);

      // Загружаем фотографии, если есть
      if (newPhotos.length > 0) {
        await apiService.uploadSamplePhotos(result.id, newPhotos);
      }

      onSuccess();
    } catch (error: unknown) {
      console.error('Ошибка при создании образца:', error);
      if (isAxiosError(error)) {
        setError(error.response?.data?.message ?? 'Не удалось создать образец');
      } else {
        setError('Не удалось создать образец');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = <K extends keyof CreateSampleData>(field: K, value: CreateSampleData[K]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const resolveApiErrorMessage = (error: unknown, fallback: string) => {
    if (isAxiosError(error)) {
      const data = error.response?.data as { error?: unknown; message?: unknown } | undefined;
      const message =
        (typeof data?.error === 'string' && data.error.trim()) ? data.error :
        (typeof data?.message === 'string' && data.message.trim()) ? data.message :
        null;
      if (message) {
        return message;
      }
    }
    return fallback;
  };

  const handleCreateSourceInline = async (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) {
      throw new Error('Введите название источника');
    }

    try {
      const created = await apiService.createSource({ name: trimmed });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.sources.some(source => source.id === created.id);
        return exists ? prev : { ...prev, sources: [...prev.sources, created] };
      });

      return created;
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Не удалось создать источник'));
    }
  };

  const handleCreateLocationInline = async (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) {
      throw new Error('Введите название локации');
    }

    try {
      const created = await apiService.createLocation({ name: trimmed });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.locations.some(location => location.id === created.id);
        return exists ? prev : { ...prev, locations: [...prev.locations, created] };
      });

      return {
        id: created.id,
        display_name: created.name,
      };
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Не удалось создать локацию'));
    }
  };

  const handleCreateIndexLetterInline = async (letter: string) => {
    const trimmed = letter.trim();
    if (!trimmed) {
      throw new Error('Введите индексную букву');
    }

    const normalized = trimmed.toUpperCase();

    try {
      const created = await apiService.createIndexLetter({ letter_value: normalized });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.index_letters.some(item => item.id === created.id);
        return exists ? prev : { ...prev, index_letters: [...prev.index_letters, created] };
      });

      return {
        id: created.id,
        display_name: created.letter_value,
      };
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Не удалось создать индексную букву'));
    }
  };



  // Обработчик успешного создания штамма
  const handleStrainCreated = (newStrain: Strain) => {
    setFormData(prev => ({
      ...prev,
      strain_id: newStrain.id
    }));
    setShowCreateStrainForm(false);
    setStrainSelectionMode('existing');
  };

  if (!isOpen) return null;

  return (
    <>
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
                    <span className="text-blue-700 text-sm">Загрузка справочных данных...</span>
                  </div>
                </div>
              )}

              {/* Основная информация */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Выбор штамма */}
                <div className="space-y-4 md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Штамм <span className="text-red-500">*</span>
                  </label>
                  
                  {/* Переключатель режима выбора штамма */}
                  <div className="flex space-x-4 mb-4">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="strainMode"
                        value="existing"
                        checked={strainSelectionMode === 'existing'}
                        onChange={(e) => setStrainSelectionMode(e.target.value as 'existing' | 'new')}
                        className="mr-2"
                        disabled={loadingReferences}
                      />
                      <span className="text-sm text-gray-700">Выбрать существующий штамм</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="strainMode"
                        value="new"
                        checked={strainSelectionMode === 'new'}
                        onChange={(e) => setStrainSelectionMode(e.target.value as 'existing' | 'new')}
                        className="mr-2"
                        disabled={loadingReferences}
                      />
                      <span className="text-sm text-gray-700">Создать новый штамм</span>
                    </label>
                  </div>

                  {/* Выбор существующего штамма */}
                  {strainSelectionMode === 'existing' && (
                    <>
                      <StrainAutocomplete
                        value={formData.strain_id}
                        onChange={(value) => handleFieldChange('strain_id', value)}
                        disabled={loadingReferences}
                        required
                      />
                      {fieldErrors.strain_id && (
                        <p className="mt-1 text-sm text-red-600">{fieldErrors.strain_id}</p>
                      )}
                    </>
                  )}

                  {/* Кнопка создания нового штамма */}
                  {strainSelectionMode === 'new' && (
                    <div className="space-y-3">
                      {formData.strain_id ? (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                          <p className="text-green-700 text-sm">
                            ✓ Штамм создан и выбран
                          </p>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowCreateStrainForm(true)}
                          className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 flex items-center justify-center space-x-2"
                          disabled={loadingReferences}
                        >
                          <Dna className="w-4 h-4" />
                          <span>Создать новый штамм</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Номер образца */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Номер образца
                  </label>
                  <Input
                    type="text"
                    value={formData.original_sample_number || ''}
                    onChange={(e) => handleFieldChange('original_sample_number', e.target.value)}
                    placeholder="Введите номер образца"
                    disabled={loadingReferences}
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
                    sources={sourceOptions}
                    currentSourceName={currentSourceName}
                    disabled={loadingReferences}
                    onCreate={handleCreateSourceInline}
                  />
                </div>

                {/* Локация */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Локация
                  </label>
                  <Autocomplete
                    value={formData.location_id}
                    onChange={(value) => handleFieldChange('location_id', typeof value === 'number' ? value : undefined)}
                    options={locationOptions}
                    placeholder="Выберите локацию"
                    disabled={loadingReferences}
                    allowCreate
                    onCreateOption={handleCreateLocationInline}
                    createOptionLabel={(term) => `Добавить локацию «${term}»`}
                  />
                </div>

                {/* Индексная буква */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Индексная буква
                  </label>
                  <Autocomplete
                    value={formData.index_letter_id}
                    onChange={(value) => handleFieldChange('index_letter_id', typeof value === 'number' ? value : undefined)}
                    options={indexLetterOptions}
                    placeholder="Выберите букву"
                    disabled={loadingReferences}
                    allowCreate
                    onCreateOption={handleCreateIndexLetterInline}
                    createOptionLabel={(term) => `Добавить индексную букву «${term.toUpperCase()}»`}
                  />
                </div>
              </div>

              {/* Хранение */}
              <StorageManager
                value={storageCells}
                onChange={setStorageCells}
                disabled={loadingReferences}
                required
              />
              {fieldErrors.storage_id && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.storage_id}</p>
              )}

              {/* Дополнительные характеристики */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Цвет ИУК */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Цвет ИУК (если вырабатывает)
                  </label>
                  <Select
                    value={formData.iuk_color_id ?? ''}
                    onChange={(value) => handleFieldChange('iuk_color_id', value ? Number(value) : undefined)}
                    options={(referenceData?.iuk_colors || []).map(color => ({ value: color.id, label: color.name }))}
                    placeholder="Не выбрано"
                    disabled={loadingReferences}
                  />
                </div>

                {/* Вариант амилазы */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Вариант амилазы (если вырабатывает)
                  </label>
                  <Select
                    value={formData.amylase_variant_id ?? ''}
                    onChange={(value) => handleFieldChange('amylase_variant_id', value ? Number(value) : undefined)}
                    options={(referenceData?.amylase_variants || []).map(variant => ({ value: variant.id, label: variant.name }))}
                    placeholder="Не выбрано"
                    disabled={loadingReferences}
                  />
                </div>
              </div>

              {/* Комментарии */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Комментарий */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Комментарий
                  </label>
                  <Textarea
                    value={formData.comment || ''}
                    onChange={(e) => handleFieldChange('comment', e.target.value)}
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
                  <Textarea
                    value={formData.appendix_note || ''}
                    onChange={(e) => handleFieldChange('appendix_note', e.target.value)}
                    rows={4}
                    placeholder="Введите примечание"
                    disabled={loadingReferences}
                  />
                </div>
              </div>

              {/* Фотографии */}
              <PhotoUpload
                photos={newPhotos}
                onChange={setNewPhotos}
                disabled={loadingReferences}
              />
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

      {/* Модальное окно создания штамма */}
      <CreateStrainForm
        isOpen={showCreateStrainForm}
        onClose={() => setShowCreateStrainForm(false)}
        onSuccess={handleStrainCreated}
      />
    </>
  );
};
