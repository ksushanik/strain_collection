import React, { useState, useEffect, useMemo } from 'react';
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
  SampleCharacteristics,
  PhotoUpload,
  GrowthMediaSelector
} from '../index';
import { StorageManager, type StorageCell } from '../StorageManager';
import { useToast } from '../../../../shared/notifications';
import { Select, Input, Textarea, Autocomplete } from '../../../../shared/components';

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
  
  // Ячейки хранения (объединенное состояние)
  const [storageCells, setStorageCells] = useState<StorageCell[]>([]);
  const [initialStorageCells, setInitialStorageCells] = useState<StorageCell[]>([]);
  // Статистика массового размещения дополнительных ячеек
  const [bulkStats, setBulkStats] = useState<{ total: number; successful: number; failed: number } | null>(null);
  // Детали ошибок массового размещения
  const [bulkErrors, setBulkErrors] = useState<string[]>([]);
  const [removalStats, setRemovalStats] = useState<{ total: number; successful: number; failed: number } | null>(null);
  const [removalErrors, setRemovalErrors] = useState<string[]>([]);
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
  
  // Фотографии
  const [newPhotos, setNewPhotos] = useState<File[]>([]);

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

        // Выбранный бокс для хранения будет установлен через StorageManager

        // Загружаем существующие аллокации образца (включая доп. ячейки)
        try {
          const allocResp = await apiService.getSampleAllocations(sampleId);
          const allAllocations = allocResp.allocations || [];

          // Преобразуем все аллокации в StorageCell формат
          let cells: StorageCell[] = allAllocations.map((allocation) => ({
            id: allocation.storage_id,
            cell_id: allocation.cell_id,
            box_id: allocation.box_id,
            display_name: allocation.cell_id,
            is_primary: allocation.is_primary,
            is_new: false, // Все существующие аллокации помечаем как не новые
            allocated_at: allocation.allocated_at
          }));

          cells.sort((a, b) => (b.is_primary ? 1 : 0) - (a.is_primary ? 1 : 0));

          // Если основной ячейки нет в списке (например, API не вернул ее), добавляем из данных образца
          const hasPrimaryCell = cells.some((cell) => cell.is_primary);
          if (!hasPrimaryCell && sampleData.storage) {
            const primaryAlreadyAdded = cells.some(
              (cell) =>
                cell.box_id === sampleData.storage?.box_id &&
                cell.cell_id === sampleData.storage?.cell_id,
            );

            if (!primaryAlreadyAdded) {
            cells = [
              {
                id: sampleData.storage.id,
                cell_id: sampleData.storage.cell_id,
                box_id: sampleData.storage.box_id,
                display_name: sampleData.storage.cell_id,
                is_primary: true,
                is_new: false,
              },
              ...cells,
            ];
            }
          }

          // Если нет аллокаций, но есть основное место хранения, показываем его
          if (cells.length === 0 && sampleData.storage) {
            cells = [
              {
                id: sampleData.storage.id,
                cell_id: sampleData.storage.cell_id,
                box_id: sampleData.storage.box_id,
                display_name: sampleData.storage.cell_id,
                is_primary: true,
                is_new: false,
              },
            ];
          }

          const normalizedInitial = cells.map((cell, index) => ({
            ...cell,
            is_primary: index === 0,
          }));

          setStorageCells(normalizedInitial);
          setInitialStorageCells(normalizedInitial);
        } catch (e) {
          console.warn('Не удалось загрузить аллокации образца:', e);
          // Если не удалось загрузить аллокации, создаем основную ячейку из данных образца
          if (sampleData.storage) {
            const fallbackCells = [{
              id: sampleData.storage.id,
              cell_id: sampleData.storage.cell_id,
              box_id: sampleData.storage.box_id,
              is_primary: true,
              is_new: false
            }];
            setStorageCells(fallbackCells);
            setInitialStorageCells(fallbackCells);
          } else {
            setStorageCells([]);
            setInitialStorageCells([]);
          }
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
    setBulkStats(null);
    setBulkErrors([]);
    setRemovalStats(null);
    setRemovalErrors([]);
    
    try {
      const buildKey = (cell: StorageCell) => `${cell.box_id}__${cell.cell_id}`;
      const initialKeys = new Set(initialStorageCells.map((cell) => buildKey(cell)));
      const currentKeys = new Set(storageCells.map((cell) => buildKey(cell)));

      const currentPrimary = storageCells[0] ?? null;
      const initialPrimary = initialStorageCells[0] ?? null;
      const initialPrimaryKey = initialPrimary ? buildKey(initialPrimary) : null;
      const currentPrimaryKey = currentPrimary ? buildKey(currentPrimary) : null;

      const cellsToRemove = initialStorageCells.filter((cell) => !currentKeys.has(buildKey(cell)));

      // Удаляем ячейки, которые были удалены в форме
      const removalTotals = { total: 0, successful: 0, failed: 0 };
      const removalErrorsList: string[] = [];
      if (cellsToRemove.length > 0) {
        for (const cell of cellsToRemove) {
          removalTotals.total += 1;
          try {
            await apiService.unallocateCell(cell.box_id, cell.cell_id, sampleId);
            removalTotals.successful += 1;
          } catch (err: unknown) {
            if (isAxiosError(err)) {
              const statusCode = err.response?.status;
              const errorMessage = err.response?.data?.error || err.message;
              const errorCode = err.response?.data?.code;
              if (
                statusCode === 404 ||
                statusCode === 409 ||
                errorCode === 'ALLOCATION_NOT_FOUND' ||
                /уже свободна/i.test(errorMessage)
              ) {
                // Ячейка уже свободна — считаем как успешное удаление
                removalTotals.successful += 1;
                continue;
              }
            }
            removalTotals.failed += 1;
            const message = isAxiosError(err)
              ? err.response?.data?.error || err.message
              : (err instanceof Error ? err.message : 'Неизвестная ошибка при удалении ячейки');
            removalErrorsList.push(`Бокс ${cell.box_id}, ячейка ${cell.cell_id}: ${message}`);
          }
        }
        setRemovalStats(removalTotals);
        setRemovalErrors(removalErrorsList);
      } else {
        setRemovalStats(null);
        setRemovalErrors([]);
      }

      let allocationTotals = { total: 0, successful: 0, failed: 0 };
      let allocationErrors: string[] = [];

      if (currentPrimary && currentPrimaryKey !== initialPrimaryKey) {
        allocationTotals.total += 1;
        try {
          await apiService.allocateCell(currentPrimary.box_id, currentPrimary.cell_id, {
            sampleId,
            isPrimary: true,
          });
          allocationTotals.successful += 1;
        } catch (err: unknown) {
          allocationTotals.failed += 1;
          const message = isAxiosError(err)
            ? err.response?.data?.error || err.message
            : err instanceof Error
              ? err.message
              : 'Не удалось обновить основную ячейку';
          allocationErrors.push(`Основная ячейка ${currentPrimary.box_id}, ${currentPrimary.cell_id}: ${message}`);
        }
      }

      const cellsToAdd = storageCells.filter((cell, index) => {
        if (index === 0) {
          return false;
        }
        const key = buildKey(cell);
        if (initialKeys.has(key)) {
          return false;
        }
        return true;
      });

      if (cellsToAdd.length > 0) {
        const groups: Record<string, { cell_id: string; sample_id: number }[]> = {};
        for (const cell of cellsToAdd) {
          const list = groups[cell.box_id] || [];
          list.push({ cell_id: cell.cell_id, sample_id: sampleId });
          groups[cell.box_id] = list;
        }

        const results = await Promise.all(
          Object.entries(groups).map(async ([boxId, assignments]) => {
            try {
              return await apiService.bulkAllocateCells(boxId, assignments);
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
                successful_allocations: [],
                errors: [msg],
              };
            }
          })
        );

        allocationErrors = results.flatMap((r) => r.errors || []);
        const groupedTotals = results.reduce(
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
        allocationTotals = {
          total: allocationTotals.total + groupedTotals.total,
          successful: allocationTotals.successful + groupedTotals.successful,
          failed: allocationTotals.failed + groupedTotals.failed,
        };
      }

      if (allocationTotals.total > 0) {
        setBulkStats(allocationTotals);
        setBulkErrors(allocationErrors);
      } else {
        setBulkStats(null);
        setBulkErrors([]);
      }

      const hasAllocationErrors = allocationErrors.length > 0;
      const hasRemovalErrors = removalErrorsList.length > 0;

      const finalStorageId = currentPrimary?.id ?? updatedFormData.storage_id;

      await apiService.updateSample(sampleId, {
        ...formData,
        storage_id: finalStorageId,
      });

      // Загружаем новые фотографии, если есть
      if (newPhotos.length > 0) {
        await apiService.uploadSamplePhotos(sampleId, newPhotos);
      }

      if (hasAllocationErrors || hasRemovalErrors) {
        const messages: string[] = [];
        if (hasAllocationErrors) {
          messages.push(`Часть новых ячеек не сохранена: ${allocationErrors.join('; ')}`);
        }
        if (hasRemovalErrors) {
          messages.push(`Часть ячеек не удалось удалить: ${removalErrorsList.join('; ')}`);
        }
        setError(messages.join(' '));
        notifyWarning('Изменения частично сохранены, проверьте детали.', { title: 'Частичное сохранение' });
        const revertedCells = initialStorageCells.map((cell, index) => ({
          ...cell,
          is_new: false,
          is_primary: index === 0,
        }));
        setStorageCells(revertedCells);
      } else {
        const normalizedCells = storageCells.map((cell, index) => ({
          ...cell,
          is_new: false,
          is_primary: index === 0,
        }));
        setStorageCells(normalizedCells);
        setInitialStorageCells(normalizedCells);
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
      throw new Error('Source name cannot be empty');
    }

    try {
      const created = await apiService.createSource({ name: trimmed });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.sources.some(source => source.id === created.id);
        if (exists) {
          return prev;
        }
        const newSource: ReferenceSource = {
          id: created.id,
          name: created.name,
          display_name: created.name,
        };
        return { ...prev, sources: [...prev.sources, newSource] };
      });

      return created;
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Failed to create source'));
    }
  };

  const handleCreateLocationInline = async (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) {
      throw new Error('Location name cannot be empty');
    }

    try {
      const created = await apiService.createLocation({ name: trimmed });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.locations.some(location => location.id === created.id);
        if (exists) {
          return prev;
        }
        return { ...prev, locations: [...prev.locations, created] };
      });

      return {
        id: created.id,
        display_name: created.name,
      };
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Failed to create location'));
    }
  };

  const handleCreateIndexLetterInline = async (letter: string) => {
    const trimmed = letter.trim();
    if (!trimmed) {
      throw new Error('Index letter cannot be empty');
    }

    const normalized = trimmed.toUpperCase();

    try {
      const created = await apiService.createIndexLetter({ letter_value: normalized });
      setReferenceData(prev => {
        if (!prev) {
          return prev;
        }
        const exists = prev.index_letters.some(item => item.id === created.id);
        if (exists) {
          return prev;
        }
        return { ...prev, index_letters: [...prev.index_letters, created] };
      });

      return {
        id: created.id,
        display_name: created.letter_value,
      };
    } catch (error) {
      throw new Error(resolveApiErrorMessage(error, 'Failed to create index letter'));
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

            {removalStats && (
              <div className={`rounded-lg p-4 border ${removalStats.failed > 0 ? 'bg-yellow-50 border-yellow-200 text-yellow-800' : 'bg-green-50 border-green-200 text-green-800'}`}>
                <p className="text-sm">
                  Удаление ячеек: запросов {removalStats.total}, успешно {removalStats.successful}, ошибок {removalStats.failed}.
                </p>
                {removalStats.failed > 0 && removalErrors.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium">Детали ошибок удаления:</p>
                    <ul className="mt-1 list-disc list-inside text-sm">
                      {removalErrors.slice(0, 5).map((err, idx) => (
                        <li key={idx}>{err}</li>
                      ))}
                    </ul>
                    {removalErrors.length > 5 && (
                      <p className="text-xs text-gray-600 mt-1">Показано 5 из {removalErrors.length} ошибок.</p>
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
                  sources={(referenceData?.sources || []).map((source) => ({
                    id: source.id,
                    display_name: source.name,
                    secondary_text: source.display_name ?? source.organism_name ?? source.name,
                  }))}
                  currentSourceName={currentSample?.source?.name ?? currentSample?.source?.organism_name}
                  onCreate={handleCreateSourceInline}
                  disabled={loadingData || loadingReferences}
                />
              </div>

              {/* Локация */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Локация
                </label>
                <Autocomplete
                  value={formData.location_id}
                  onChange={(val) => handleFieldChange('location_id', typeof val === 'number' ? val : undefined)}
                  options={locationOptions}
                  placeholder="Select location"
                  disabled={loadingData || loadingReferences}
                  allowCreate
                  onCreateOption={handleCreateLocationInline}
                  createOptionLabel={(term) => `Add location "${term}"`}
                />
              </div>

              {/* Индексная буква */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Индексная буква
                </label>
                <Autocomplete
                  value={formData.index_letter_id}
                  onChange={(val) => handleFieldChange('index_letter_id', typeof val === 'number' ? val : undefined)}
                  options={indexLetterOptions}
                  placeholder="Select index letter"
                  disabled={loadingData || loadingReferences}
                  allowCreate
                  onCreateOption={handleCreateIndexLetterInline}
                  createOptionLabel={(term) => `Add index letter "${term.toUpperCase()}"`}
                />
              </div>
            </div>

            {/* Хранение */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Место хранения <span className="text-red-500">*</span>
              </label>
              <StorageManager
                value={storageCells}
                onChange={setStorageCells}
                disabled={loadingData || loadingReferences}
                required
              />
              {fieldErrors.storage_id && (
                <p className="mt-1 text-sm text-red-600">{fieldErrors.storage_id}</p>
              )}
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
