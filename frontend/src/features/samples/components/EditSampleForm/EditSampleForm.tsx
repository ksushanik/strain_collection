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
import { useToast } from '../../../../shared/notifications';
import { Select, Input, Textarea } from '../../../../shared/components';

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
  const [fieldErrors, setFieldErrors] = useState<{ strain_id?: string; storage_id?: string }>({});
  
  // Справочные данные
  const [referenceData, setReferenceData] = useState<EditSampleReferenceData | null>(null);
  const [currentSample, setCurrentSample] = useState<Sample | null>(null);
  
  // Дополнительные ячейки хранения (локальное состояние)
  const [multiCells, setMultiCells] = useState<AssignedCell[]>([]);
  // Статистика массового размещения дополнительных ячеек
  const [bulkStats, setBulkStats] = useState<{ total: number; successful: number; failed: number } | null>(null);
  // Детали ошибок массового размещения
  const [bulkErrors, setBulkErrors] = useState<string[]>([]);
  const { success: notifySuccess, warning: notifyWarning, error: notifyError } = useToast();
  
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

    setFieldErrors({});
    
    if (!formData.strain_id) {
      setFieldErrors(prev => ({ ...prev, strain_id: 'Требуется выбрать штамм' }));
      setError('Выберите штамм');
      return;
    }

    if (!formData.storage_id) {
      setFieldErrors(prev => ({ ...prev, storage_id: 'Требуется выбрать место хранения' }));
      setError('Выберите место хранения');
      return;
    }

    setLoading(true);
    setError(null);
    setBulkStats(null);
    setBulkErrors([]);
    
    try {
      // Обновляем данные образца
      await apiService.updateSample(sampleId, formData);

      // Загружаем новые фотографии, если есть
      if (newPhotos.length > 0) {
        await apiService.uploadSamplePhotos(sampleId, newPhotos);
      }

      // Сохраняем дополнительные ячейки (мульти-ячейки), если выбраны
      if (multiCells.length > 0) {
        const groups: Record<string, { cell_id: string; sample_id: number }[]> = {};
        for (const c of multiCells) {
          const list = groups[c.box_id] || [];
          list.push({ cell_id: c.cell_id, sample_id: sampleId });
          groups[c.box_id] = list;
        }

        const results = await Promise.all(
          Object.entries(groups).map(async ([boxId, assignments]) => {
            try {
              return await apiService.bulkAssignCells(boxId, assignments);
            } catch (err: unknown) {
              const msg = isAxiosError(err)
                ? (err.response?.data?.error || 'Ошибка запроса к серверу')
                : 'Неизвестная ошибка запроса';
              return {
                message: 'Ошибка массового размещения',
                statistics: {
                  total_requested: assignments.length,
                  successful: 0,
                  failed: assignments.length,
                },
                successful_assignments: [],
                errors: [msg],
              };
            }
          })
        );

        const aggregatedErrors = results.flatMap((r) => r.errors || []);
        const totals = results.reduce(
          (acc, r) => {
            const s = r.statistics || { total_requested: 0, successful: 0, failed: 0 };
            return {
              total: acc.total + (s.total_requested || 0),
              successful: acc.successful + (s.successful || 0),
              failed: acc.failed + (s.failed || 0),
            };
          },
          { total: 0, successful: 0, failed: 0 }
        );
        setBulkStats(totals);
        setBulkErrors(aggregatedErrors);

        if (aggregatedErrors.length > 0) {
          setError(`Часть дополнительных ячеек не сохранена: ${aggregatedErrors.join('; ')}`);
          notifyWarning(`Частичный успех: успешно ${totals.successful}/${totals.total}, ошибок ${totals.failed}.`, { title: 'Частичное сохранение' });
        } else {
          notifySuccess(`Сохранено: ${totals.successful}/${totals.total} доп. ячеек`, { title: 'Сохранено' });
          onSuccess();
        }
      }

      // Успешное сохранение основной формы без дополнительных ячеек
      if (multiCells.length === 0) {
        notifySuccess('Образец обновлен', { title: 'Успех' });
        onSuccess();
      }
    } catch (error: unknown) {
      console.error('Ошибка при обновлении образца:', error);
      if (isAxiosError(error)) {
        const msg = error.response?.data?.message ?? 'Не удалось обновить образец';
        setError(msg);
        notifyError(msg, { title: 'Ошибка обновления' });
      } else {
        setError('Не удалось обновить образец');
        notifyError('Не удалось обновить образец', { title: 'Ошибка обновления' });
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

            {/* Bulk stats info */}
            {bulkStats && (
              <div className={`rounded-lg p-4 border ${bulkStats.failed > 0 ? 'bg-yellow-50 border-yellow-200 text-yellow-800' : 'bg-green-50 border-green-200 text-green-800'}`}>
                <p className="text-sm">
                  Дополнительные ячейки: запросов {bulkStats.total}, успешно {bulkStats.successful}, ошибок {bulkStats.failed}.
                </p>
                {bulkStats.failed > 0 && bulkErrors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium">Детали ошибок:</p>
                    <ul className="mt-1 list-disc list-inside text-sm">
                      {bulkErrors.slice(0, 5).map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                    {bulkErrors.length > 5 && (
                      <p className="text-xs text-gray-600 mt-1">Показано 5 из {bulkErrors.length} ошибок.</p>
                    )}
                  </div>
                )}
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
                {fieldErrors.strain_id && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.strain_id}</p>
                )}
              </div>

              {/* Номер образца */}
              <div className="space-y-2">
                <Input
                  label="Номер образца"
                  type="text"
                  value={formData.original_sample_number || ''}
                  onChange={(e) => handleFieldChange('original_sample_number', e.target.value)}
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
                <Select
                  value={formData.location_id ?? ''}
                  onChange={(val) => handleFieldChange('location_id', val === '' ? undefined : Number(val))}
                  options={(referenceData?.locations || []).map((location) => ({ value: location.id, label: location.name }))}
                  placeholder="Выберите локацию"
                  disabled={loadingData || loadingReferences}
                />
              </div>

              {/* Индексная буква */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Индексная буква
                </label>
                <Select
                  value={formData.index_letter_id ?? ''}
                  onChange={(val) => handleFieldChange('index_letter_id', val === '' ? undefined : Number(val))}
                  options={(referenceData?.index_letters || []).map((letter) => ({ value: letter.id, label: letter.letter_value }))}
                  placeholder="Выберите букву"
                  disabled={loadingData || loadingReferences}
                />
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
            {fieldErrors.storage_id && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.storage_id}</p>
            )}

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
                <Select
                  value={formData.iuk_color_id ?? ''}
                  onChange={(val) => handleFieldChange('iuk_color_id', val === '' ? undefined : Number(val))}
                  options={(referenceData?.iuk_colors || []).map((color) => ({ value: color.id, label: color.name }))}
                  placeholder="Не выбрано"
                  disabled={loadingData || loadingReferences}
                />
              </div>

              {/* Вариант амилазы */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Вариант амилазы
                </label>
                <Select
                  value={formData.amylase_variant_id ?? ''}
                  onChange={(val) => handleFieldChange('amylase_variant_id', val === '' ? undefined : Number(val))}
                  options={(referenceData?.amylase_variants || []).map((variant) => ({ value: variant.id, label: variant.name }))}
                  placeholder="Не выбрано"
                  disabled={loadingData || loadingReferences}
                />
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
                <Textarea
                  label="Комментарий"
                  value={formData.comment || ''}
                  onChange={(e) => handleFieldChange('comment', e.target.value)}
                  rows={4}
                  placeholder="Введите комментарий"
                  disabled={loadingData || loadingReferences}
                />
              </div>

              {/* Примечание */}
              <div className="space-y-2">
                <Textarea
                  label="Примечание"
                  value={formData.appendix_note || ''}
                  onChange={(e) => handleFieldChange('appendix_note', e.target.value)}
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
