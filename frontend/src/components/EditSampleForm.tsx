import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, Search, Beaker } from 'lucide-react';
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
    appendix_note_id: undefined,
    comment_id: undefined,
    has_photo: false,
    is_identified: false,
    has_antibiotic_activity: false,
    has_genome: false,
    has_biochemistry: false,
    seq_status: false,
  });

  // Поиск в выпадающих списках
  const [searchTerms, setSearchTerms] = useState({
    strain: '',
    source: '',
    location: '',
    storage: ''
  });

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
          appendix_note_id: sampleData.appendix_note?.id,
          comment_id: sampleData.comment?.id,
          has_photo: sampleData.has_photo,
          is_identified: sampleData.is_identified,
          has_antibiotic_activity: sampleData.has_antibiotic_activity,
          has_genome: sampleData.has_genome,
          has_biochemistry: sampleData.has_biochemistry,
          seq_status: sampleData.seq_status,
        });

      } catch (err: unknown) {
        const error = err as { response?: { data?: { error?: string } }; message?: string };
        console.error('Ошибка загрузки данных:', err);
        setError(error.response?.data?.error || error.message || 'Ошибка загрузки данных');
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
    if (!searchTerms.strain) return referenceData.strains.slice(0, 50);
    
    return referenceData.strains.filter(strain =>
      strain.display_name.toLowerCase().includes(searchTerms.strain.toLowerCase()) ||
      strain.short_code.toLowerCase().includes(searchTerms.strain.toLowerCase())
    ).slice(0, 50);
  };

  const getFilteredSources = (): ReferenceSource[] => {
    if (!referenceData) return [];
    if (!searchTerms.source) return referenceData.sources.slice(0, 50);
    
    return referenceData.sources.filter(source =>
      source.display_name.toLowerCase().includes(searchTerms.source.toLowerCase()) ||
      source.organism_name.toLowerCase().includes(searchTerms.source.toLowerCase())
    ).slice(0, 50);
  };

  const getFilteredLocations = (): ReferenceLocation[] => {
    if (!referenceData) return [];
    if (!searchTerms.location) return referenceData.locations.slice(0, 50);
    
    return referenceData.locations.filter(location =>
      location.name.toLowerCase().includes(searchTerms.location.toLowerCase())
    ).slice(0, 50);
  };

  const getFilteredStorage = (): ReferenceStorage[] => {
    if (!referenceData) return [];
    
    // Добавляем текущее место хранения в список доступных, если оно есть
    const availableStorage = [...referenceData.free_storage];
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
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
      setError(error.response?.data?.error || error.message || 'Ошибка при обновлении образца');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: keyof UpdateSampleData, value: unknown) => {
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
                  <div className="relative">
                    <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск штамма..."
                      value={searchTerms.strain}
                      onChange={(e) => setSearchTerms(prev => ({ ...prev, strain: e.target.value }))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={loadingReferences}
                    />
                  </div>
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
                  <div className="relative">
                    <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск ячейки..."
                      value={searchTerms.storage}
                      onChange={(e) => setSearchTerms(prev => ({ ...prev, storage: e.target.value }))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={loadingReferences}
                    />
                  </div>
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
                  <div className="relative">
                    <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск источника..."
                      value={searchTerms.source}
                      onChange={(e) => setSearchTerms(prev => ({ ...prev, source: e.target.value }))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={loadingReferences}
                    />
                  </div>
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
                  <div className="relative">
                    <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск местоположения..."
                      value={searchTerms.location}
                      onChange={(e) => setSearchTerms(prev => ({ ...prev, location: e.target.value }))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={loadingReferences}
                    />
                  </div>
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
                    {referenceData?.comments.map(comment => (
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
                    {referenceData?.appendix_notes.map(note => (
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