import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Beaker } from 'lucide-react';
import apiService from '../../../../services/api';
import type { 
  Sample,
  UpdateSampleData, 
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
    mobilizes_phosphates: false,
    stains_medium: false,
    produces_siderophores: false,
    iuk_color_id: undefined,
    amylase_variant_id: undefined,
    growth_medium_ids: [],
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
        });

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
          has_photo: sampleData.has_photo || false,
          is_identified: sampleData.is_identified || false,
          has_antibiotic_activity: sampleData.has_antibiotic_activity || false,
          has_genome: sampleData.has_genome || false,
          has_biochemistry: sampleData.has_biochemistry || false,
          seq_status: sampleData.seq_status || false,
          mobilizes_phosphates: sampleData.mobilizes_phosphates || false,
          stains_medium: sampleData.stains_medium || false,
          produces_siderophores: sampleData.produces_siderophores || false,
          iuk_color_id: sampleData.iuk_color?.id,
          amylase_variant_id: sampleData.amylase_variant?.id,
          growth_medium_ids: sampleData.growth_media?.map((m: any) => m.id) || [],
        });

        // Устанавливаем выбранный бокс для хранения
        if (sampleData.storage?.box_id) {
          setSelectedBoxId(sampleData.storage.box_id.toString());
        }

      } catch (error: any) {
        console.error('Ошибка при загрузке данных:', error);
        setError(error.response?.data?.message || 'Не удалось загрузить данные');
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
      await apiService.updateSample(sampleId, formData);

      // Загружаем новые фотографии, если есть
      if (newPhotos.length > 0) {
        await apiService.uploadSamplePhotos(sampleId, newPhotos);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Ошибка при обновлении образца:', error);
      setError(error.response?.data?.message || 'Не удалось обновить образец');
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
              Редактировать образец {currentSample?.original_sample_number}
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
            />

            {/* Характеристики образца */}
            <SampleCharacteristics
              data={{
                has_photo: formData.has_photo ?? false,
                is_identified: formData.is_identified ?? false,
                has_antibiotic_activity: formData.has_antibiotic_activity ?? false,
                has_genome: formData.has_genome ?? false,
                has_biochemistry: formData.has_biochemistry ?? false,
                seq_status: formData.seq_status ?? false,
                mobilizes_phosphates: formData.mobilizes_phosphates ?? false,
                stains_medium: formData.stains_medium ?? false,
                produces_siderophores: formData.produces_siderophores ?? false,
                iuk_color_id: formData.iuk_color_id,
                amylase_variant_id: formData.amylase_variant_id,
                growth_medium_ids: formData.growth_medium_ids ?? [],
              }}
              onChange={handleFieldChange}
              disabled={loadingData || loadingReferences}
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