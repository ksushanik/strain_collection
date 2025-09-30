import React, { useState, useEffect } from 'react';
import { X, Plus, Loader2, Beaker, Dna } from 'lucide-react';
import { isAxiosError } from 'axios';
import apiService from '../../../../services/api';
import type { 
  CreateSampleData, 
  ReferenceSource,
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
  StorageAutocomplete,
  SampleCharacteristics,
  PhotoUpload,
  CreateStrainForm,
  GrowthMediaSelector
} from '../index';

interface AddSampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  preSelectedStrainId?: number;
}

interface AddSampleReferenceData {
  sources: ReferenceSource[];
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
  
  // Состояние для двухэтапного выбора хранения
  const [selectedBoxId, setSelectedBoxId] = useState<string | undefined>(undefined);
  
  // Фотографии
  const [newPhotos, setNewPhotos] = useState<File[]>([]);

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
    
    if (!formData.strain_id) {
      setError('Выберите штамм');
      return;
    }

    if (!formData.storage_id) {
      setError('Выберите место хранения');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Создаем образец
      const result = await apiService.createSample(formData);

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
                    <StrainAutocomplete
                      value={formData.strain_id}
                      onChange={(value) => handleFieldChange('strain_id', value)}
                      disabled={loadingReferences}
                      required
                    />
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
                  <input
                    type="text"
                    value={formData.original_sample_number || ''}
                    onChange={(e) => handleFieldChange('original_sample_number', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                    sources={referenceData?.sources || []}
                    disabled={loadingReferences}
                  />
                </div>

                {/* Локация */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Локация
                  </label>
                  <select
                    value={formData.location_id || ''}
                    onChange={(e) => handleFieldChange('location_id', e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Выберите локацию</option>
                    {referenceData?.locations.map(location => (
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
                    onChange={(e) => handleFieldChange('index_letter_id', e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Выберите букву</option>
                    {referenceData?.index_letters.map(letter => (
                      <option key={letter.id} value={letter.id}>
                        {letter.letter_value}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Хранение */}
              <StorageAutocomplete
                boxValue={selectedBoxId}
                cellValue={formData.storage_id}
                onBoxChange={(boxId) => setSelectedBoxId(boxId)}
                onCellChange={(cellId) => handleFieldChange('storage_id', cellId)}
                disabled={loadingReferences}
                required
              />

              {/* Дополнительные характеристики */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Цвет ИУК */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Цвет ИУК (если вырабатывает)
                  </label>
                  <select
                    value={formData.iuk_color_id || ''}
                    onChange={(e) => handleFieldChange('iuk_color_id', e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Не выбрано</option>
                    {referenceData?.iuk_colors?.map(color => (
                      <option key={color.id} value={color.id}>
                        {color.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Вариант амилазы */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Вариант амилазы (если вырабатывает)
                  </label>
                  <select
                    value={formData.amylase_variant_id || ''}
                    onChange={(e) => handleFieldChange('amylase_variant_id', e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loadingReferences}
                  >
                    <option value="">Не выбрано</option>
                    {referenceData?.amylase_variants?.map(variant => (
                      <option key={variant.id} value={variant.id}>
                        {variant.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Среды роста */}
              <GrowthMediaSelector
                selectedIds={formData.growth_media_ids || []}
                onChange={(selectedIds) => handleFieldChange('growth_media_ids', selectedIds)}
                disabled={loadingReferences}
              />

              {/* Характеристики образца */}
              <SampleCharacteristics
                data={formData}
                onChange={handleFieldChange}
                disabled={loadingReferences}
              />

              {/* Комментарии */}
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
