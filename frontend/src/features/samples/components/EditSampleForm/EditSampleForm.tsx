import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Beaker } from 'lucide-react';
import { isAxiosError } from 'axios';
import apiService from '../../../../services/api';
import type {
  Sample,
  UpdateSampleData,
  ReferenceSource,
  ReferenceLocation,
  ReferenceIndexLetter,
  IUKColor,
  AmylaseVariant,
  GrowthMedium,
  SampleCharacteristicValue,
  SampleCharacteristicsUpdate,
} from '../../../../types';
import {
  StrainAutocomplete,
  SourceAutocomplete,
  StorageAutocomplete,
  SampleCharacteristics,
  PhotoUpload,
  GrowthMediaSelector
} from '../index';
import { StorageMultiAssign, type AssignedCell } from '../StorageMultiAssign/StorageMultiAssign';

interface EditSampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  sampleId: number;
}

interface EditSampleReferenceData {
  sources: ReferenceSource[];
  locations: ReferenceLocation[];
  index_letters: ReferenceIndexLetter[];
  iuk_colors: IUKColor[];
  amylase_variants: AmylaseVariant[];
  growth_media: GrowthMedium[];
}

export const EditSampleForm: React.FC<EditSampleFormProps> = ({ 
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
  
  // Дополнительные ячейки хранения (локальное состояние)
  const [multiCells, setMultiCells] = useState<AssignedCell[]>([]);
  
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
        iuk_color_id: undefined,
        amylase_variant_id: undefined,
        growth_media_ids: [],
        characteristics: {}
    });
  
  // Состояние для двухэтапного выбора хранения
  const [selectedBoxId, setSelectedBoxId] = useState<string | undefined>(undefined);
  
  // Фотографии
  const [newPhotos, setNewPhotos] = useState<File[]>([]);

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
        
        setReferenceData({
          sources: referenceData.sources || [],
          locations: referenceData.locations || [],
          index_letters: referenceData.index_letters || [],
          iuk_colors: referenceData.iuk_colors || [],
          amylase_variants: referenceData.amylase_variants || [],
          growth_media: referenceData.growth_media || [],
        });

        // Преобразуем характеристики в объект для формы (поддерживаем оба формата)
        const characteristicsObj: SampleCharacteristicsUpdate = {};
        if (sampleData.characteristics) {
          if (Array.isArray(sampleData.characteristics)) {
            // Старый формат: массив SampleCharacteristicValue
            (sampleData.characteristics as SampleCharacteristicValue[]).forEach((charValue) => {
              const characteristic = charValue.characteristic;
              if (characteristic) {
                const value =
                  charValue.boolean_value ??
                  charValue.text_value ??
                  charValue.select_value ??
                  null;
                characteristicsObj[characteristic.name] = {
                  characteristic_id: characteristic.id,
                  characteristic_type: characteristic.characteristic_type,
                  characteristic_name: characteristic.display_name,
                  value,
                };
              }
            });
          } else {
            // Новый формат: объект с именами характеристик как ключи
            Object.entries(sampleData.characteristics as SampleCharacteristicsUpdate).forEach(
              ([charName, charData]) => {
                if (charData) {
                  characteristicsObj[charName] = {
                    characteristic_id: charData.characteristic_id,
                    characteristic_type: charData.characteristic_type,
                    characteristic_name: charData.characteristic_name ?? charName,
                    value: charData.value,
                  };
                }
              },
            );
          }
        }

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
                iuk_color_id: sampleData.iuk_color?.id,
                amylase_variant_id: sampleData.amylase_variant?.id,
                growth_media_ids: (sampleData.growth_media ?? []).map((medium) => medium.id),
                characteristics: characteristicsObj
            });

        // Устанавливаем выбранный бокс для хранения
        const boxId = sampleData.storage?.box_id;
        if (boxId) {
          setSelectedBoxId(boxId.toString());
        }

      } catch (error: unknown) {
        console.error('Ошибка при загрузке данных:', error);
        if (isAxiosError(error)) {
          setError(error.response?.data?.message ?? 'Не удалось загрузить данные');
        } else {
          setError('Не удалось загрузить данные');
        }
      } finally {
        setLoadingData(false);
        setLoadingReferences(false);
      }
    };

    loadData();
  }, [isOpen, sampleId]);

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
      // Обновляем данные образца
      const result = await apiService.updateSample(sampleId, formData);

      // Загружаем новые фотографии, если есть
      if (newPhotos.length > 0) {
        await apiService.uploadSamplePhotos(sampleId, newPhotos);
      }

      onSuccess();
    } catch (error: unknown) {
      console.error('Ошибка при обновлении образца:', error);
      if (isAxiosError(error)) {
        setError(error.response?.data?.message ?? 'Не удалось обновить образец');
      } else {
        setError('Не удалось обновить образец');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = <K extends keyof UpdateSampleData>(
    field: K,
    value: UpdateSampleData[K],
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
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
              Редактировать образец #{currentSample?.id}
              {currentSample?.original_sample_number && ` (${currentSample.original_sample_number})`}
            </h2>
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

            {/* Loading States */}
            {(loadingData || loadingReferences) && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-blue-700 text-sm">
                    {loadingData ? 'Загрузка данных образца...' : 'Загрузка справочных данных...'}
                  </span>
                </div>
              </div>
            )}

            {/* Основная информация */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Штамм */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Штамм <span className="text-red-500">*</span>
                </label>
                <StrainAutocomplete
                  value={formData.strain_id}
                  onChange={(value) => handleFieldChange('strain_id', value)}
                  disabled={loadingData || loadingReferences}
                  required
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
                  disabled={loadingData || loadingReferences}
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
                  currentSourceName={currentSample?.source?.organism_name}
                  disabled={loadingData || loadingReferences}
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
                  disabled={loadingData || loadingReferences}
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
                  disabled={loadingData || loadingReferences}
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
              disabled={loadingData || loadingReferences}
              required
              currentCellData={currentSample?.storage ? {
                id: currentSample.storage.id,
                cell_id: currentSample.storage.cell_id,
                box_id: currentSample.storage.box_id
              } : undefined}
            />

            {/* Дополнительные места хранения (несколько ячеек) */}
            <div className="mt-6">
              <StorageMultiAssign
                disabled={loadingData || loadingReferences}
                currentPrimaryCell={currentSample?.storage ? {
                  id: currentSample.storage.id,
                  cell_id: currentSample.storage.cell_id,
                  box_id: currentSample.storage.box_id,
                } : undefined}
                onChange={setMultiCells}
              />
            </div>

            {/* Цвет ИУК и Вариант амилазы */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Цвет ИУК */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Цвет ИУК
                </label>
                <select
                  value={formData.iuk_color_id || ''}
                  onChange={(e) => handleFieldChange('iuk_color_id', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loadingData || loadingReferences}
                >
                  <option value="">Не выбрано</option>
                  {referenceData?.iuk_colors?.map((color) => (
                    <option key={color.id} value={color.id}>
                      {color.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Вариант амилазы */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Вариант амилазы
                </label>
                <select
                  value={formData.amylase_variant_id || ''}
                  onChange={(e) => handleFieldChange('amylase_variant_id', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loadingData || loadingReferences}
                >
                  <option value="">Не выбрано</option>
                  {referenceData?.amylase_variants?.map((variant) => (
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
              disabled={loadingData || loadingReferences}
            />

            {/* Характеристики образца */}
            <SampleCharacteristics
              data={formData}
              onChange={handleFieldChange}
              disabled={loadingData || loadingReferences}
              sampleId={sampleId}
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
                  disabled={loadingData || loadingReferences}
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
                  disabled={loadingData || loadingReferences}
                />
              </div>
            </div>

            {/* Фотографии */}
            <PhotoUpload
              photos={newPhotos}
              onChange={setNewPhotos}
              disabled={loadingData || loadingReferences}
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
              disabled={loading || loadingData || loadingReferences}
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
      </div>
    </div>
  );
};
