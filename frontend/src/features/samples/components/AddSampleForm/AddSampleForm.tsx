import React, { useState, useEffect } from 'react';
import { X, Plus, Loader2, Beaker } from 'lucide-react';
import apiService from '../../../../services/api';
import type { 
  CreateSampleData, 
  ReferenceSource,
  ReferenceLocation,
  ReferenceIndexLetter
} from '../../../../types';
import {
  StrainAutocomplete,
  SourceAutocomplete,
  StorageAutocomplete,
  SampleCharacteristics,
  PhotoUpload
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
    is_identified: false,
    has_antibiotic_activity: false,
    has_genome: false,
    has_biochemistry: false,
    seq_status: false,
    mobilizes_phosphates: false,
    stains_medium: false,
    produces_siderophores: false,
    has_photo: false,
    iuk_color_id: undefined,
    amylase_variant_id: undefined,
    growth_medium_ids: [],
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
    } catch (error: any) {
      console.error('Ошибка при создании образца:', error);
      setError(error.response?.data?.message || 'Не удалось создать образец');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof CreateSampleData, value: any) => {
    console.log('📝 AddSampleForm: handleFieldChange called with:', { field, value });
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
                  <span className="text-blue-700 text-sm">Загрузка справочных данных...</span>
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
                  disabled={loadingReferences}
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

            {/* Характеристики образца */}
            <SampleCharacteristics
              data={{
                is_identified: formData.is_identified,
                has_antibiotic_activity: formData.has_antibiotic_activity,
                has_genome: formData.has_genome,
                has_biochemistry: formData.has_biochemistry,
                seq_status: formData.seq_status,
                mobilizes_phosphates: formData.mobilizes_phosphates,
                stains_medium: formData.stains_medium,
                produces_siderophores: formData.produces_siderophores,
                iuk_color_id: formData.iuk_color_id,
                amylase_variant_id: formData.amylase_variant_id,
                growth_medium_ids: formData.growth_medium_ids ?? [],
              }}
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
  );
};