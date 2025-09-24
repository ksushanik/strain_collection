import React, { useState, useEffect } from 'react';
import { Save, X, Loader2, Dna } from 'lucide-react';
import apiService from '../../../../services/api';
import type { Strain } from '../../../../types';

interface StrainFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (strain: Strain) => void;
  strainId?: number;
}

interface StrainFormData {
  short_code: string;
  identifier: string;
  rrna_taxonomy: string;
  name_alt: string;
  rcam_collection_id: string;
}

export const StrainForm: React.FC<StrainFormProps> = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  strainId 
}) => {
  const isEditMode = Boolean(strainId);
  
  const [formData, setFormData] = useState<StrainFormData>({
    short_code: '',
    identifier: '',
    rrna_taxonomy: '',
    name_alt: '',
    rcam_collection_id: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Загрузка данных штамма для редактирования
  useEffect(() => {
    const loadStrainData = async () => {
      if (!isEditMode || !strainId || !isOpen) return;
      
      setLoadingData(true);
      setError(null);

      try {
        const strain = await apiService.getStrain(strainId);
        
        setFormData({
          short_code: strain.short_code || '',
          identifier: strain.identifier || '',
          rrna_taxonomy: strain.rrna_taxonomy || '',
          name_alt: strain.name_alt || '',
          rcam_collection_id: strain.rcam_collection_id || ''
        });
      } catch (error: any) {
        console.error('Ошибка при загрузке данных штамма:', error);
        setError(error.response?.data?.message || 'Не удалось загрузить данные штамма');
      } finally {
        setLoadingData(false);
      }
    };

    loadStrainData();
  }, [isEditMode, strainId, isOpen]);

  // Сброс формы при закрытии
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        short_code: '',
        identifier: '',
        rrna_taxonomy: '',
        name_alt: '',
        rcam_collection_id: ''
      });
      setErrors({});
      setError(null);
      setSuccessMessage(null);
    }
  }, [isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Очищаем ошибки для этого поля
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: []
      }));
    }
    
    // Очищаем общую ошибку
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.short_code.trim()) {
      setError('Короткий код штамма обязателен');
      return;
    }

    if (!formData.identifier.trim()) {
      setError('Идентификатор штамма обязателен');
      return;
    }

    setLoading(true);
    setErrors({});
    setError(null);
    setSuccessMessage(null);

    try {
      // Подготовка данных - убираем пустые поля
      const dataToSend = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value.trim() !== '')
      );

      let response;
      if (isEditMode && strainId) {
        // Редактирование существующего штамма
        response = await apiService.updateStrain(strainId, dataToSend);
      } else {
        // Создание нового штамма
        response = await apiService.createStrain(dataToSend);
      }

      const strain = response;
      setSuccessMessage(isEditMode ? 'Штамм успешно обновлен!' : 'Штамм успешно создан!');
      
      // Задержка для показа сообщения об успехе
      setTimeout(() => {
        onSuccess(strain);
      }, 1000);

    } catch (error: any) {
      console.error('Ошибка при сохранении штамма:', error);
      
      if (error.response?.data?.details) {
        // Ошибки валидации
        const validationErrors: Record<string, string[]> = {};
        error.response.data.details.forEach((err: any) => {
          const field = err.loc[0];
          if (!validationErrors[field]) {
            validationErrors[field] = [];
          }
          validationErrors[field].push(err.msg);
        });
        setErrors(validationErrors);
      } else {
        setError(error.response?.data?.message || 'Не удалось сохранить штамм');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[95vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <Dna className="w-4 h-4 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">
              {isEditMode ? 'Редактировать штамм' : 'Добавить новый штамм'}
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
            {/* Success Message */}
            {successMessage && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-600 text-sm">{successMessage}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* Loading State */}
            {loadingData && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-blue-700 text-sm">Загрузка данных штамма...</span>
                </div>
              </div>
            )}

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Короткий код штамма */}
              <div className="space-y-2">
                <label htmlFor="short_code" className="block text-sm font-medium text-gray-700">
                  Короткий код штамма <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="short_code"
                  name="short_code"
                  value={formData.short_code}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                    errors.short_code ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Например: LB001"
                  disabled={loadingData}
                  required
                />
                {errors.short_code && (
                  <p className="text-red-500 text-sm">{errors.short_code.join(', ')}</p>
                )}
              </div>

              {/* ID коллекции RCAM */}
              <div className="space-y-2">
                <label htmlFor="rcam_collection_id" className="block text-sm font-medium text-gray-700">
                  ID коллекции RCAM
                </label>
                <input
                  type="text"
                  id="rcam_collection_id"
                  name="rcam_collection_id"
                  value={formData.rcam_collection_id}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                    errors.rcam_collection_id ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Например: RCAM-001"
                  disabled={loadingData}
                />
                {errors.rcam_collection_id && (
                  <p className="text-red-500 text-sm">{errors.rcam_collection_id.join(', ')}</p>
                )}
              </div>
            </div>

            {/* Идентификатор штамма */}
            <div className="space-y-2">
              <label htmlFor="identifier" className="block text-sm font-medium text-gray-700">
                Идентификатор штамма <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="identifier"
                name="identifier"
                value={formData.identifier}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                  errors.identifier ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Например: Lysobacter antibioticus LB001"
                disabled={loadingData}
                required
              />
              {errors.identifier && (
                <p className="text-red-500 text-sm">{errors.identifier.join(', ')}</p>
              )}
            </div>

            {/* rRNA таксономия */}
            <div className="space-y-2">
              <label htmlFor="rrna_taxonomy" className="block text-sm font-medium text-gray-700">
                rRNA таксономия
              </label>
              <textarea
                id="rrna_taxonomy"
                name="rrna_taxonomy"
                value={formData.rrna_taxonomy}
                onChange={handleInputChange}
                rows={3}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                  errors.rrna_taxonomy ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Таксономическая классификация на основе rRNA"
                disabled={loadingData}
              />
              {errors.rrna_taxonomy && (
                <p className="text-red-500 text-sm">{errors.rrna_taxonomy.join(', ')}</p>
              )}
            </div>

            {/* Альтернативное название */}
            <div className="space-y-2">
              <label htmlFor="name_alt" className="block text-sm font-medium text-gray-700">
                Альтернативное название
              </label>
              <input
                type="text"
                id="name_alt"
                name="name_alt"
                value={formData.name_alt}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                  errors.name_alt ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Альтернативное или синонимичное название"
                disabled={loadingData}
              />
              {errors.name_alt && (
                <p className="text-red-500 text-sm">{errors.name_alt.join(', ')}</p>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || loadingData}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Сохранение...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>{isEditMode ? 'Обновить штамм' : 'Сохранить штамм'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};