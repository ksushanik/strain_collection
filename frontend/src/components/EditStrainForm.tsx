import React, { useState, useEffect } from 'react';
import { Edit, Save, X } from 'lucide-react';
import apiService from '../services/api';
import type { Strain } from '../types';

interface EditStrainFormProps {
  strainId: number;
  onSuccess?: (strain: Strain) => void;
  onCancel?: () => void;
}

interface StrainFormData {
  short_code: string;
  identifier: string;
  rrna_taxonomy: string;
  name_alt: string;
  rcam_collection_id: string;
}

const EditStrainForm: React.FC<EditStrainFormProps> = ({ strainId, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState<StrainFormData>({
    short_code: '',
    identifier: '',
    rrna_taxonomy: '',
    name_alt: '',
    rcam_collection_id: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [message, setMessage] = useState<string>('');

  // Загрузка данных штамма для редактирования
  useEffect(() => {
    const loadStrainData = async () => {
      try {
        setIsLoadingData(true);
        const strain = await apiService.getStrain(strainId);
        
        setFormData({
          short_code: strain.short_code || '',
          identifier: strain.identifier || '',
          rrna_taxonomy: strain.rrna_taxonomy || '',
          name_alt: strain.name_alt || '',
          rcam_collection_id: strain.rcam_collection_id || ''
        });
      } catch (error) {
        setMessage('Ошибка загрузки данных штамма');
        console.error('Error loading strain data:', error);
      } finally {
        setIsLoadingData(false);
      }
    };

    loadStrainData();
  }, [strainId]);

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
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});
    setMessage('');

    try {
      // Подготовка данных - убираем пустые поля
      const dataToSend = Object.fromEntries(
        Object.entries(formData).filter(([_, value]) => value.trim() !== '')
      );

      const response = await fetch(`http://localhost:8000/api/strains/${strainId}/update/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend)
      });

      const result = await response.json();

      if (response.ok) {
        setMessage('Штамм успешно обновлен!');
        
        if (onSuccess) {
          onSuccess(result);
        }
      } else {
        if (result.details) {
          // Ошибки валидации Pydantic
          const validationErrors: Record<string, string[]> = {};
          result.details.forEach((error: any) => {
            const field = error.loc[0];
            if (!validationErrors[field]) {
              validationErrors[field] = [];
            }
            validationErrors[field].push(error.msg);
          });
          setErrors(validationErrors);
        } else if (result.error) {
          setMessage(result.error);
        }
      }
    } catch (error) {
      setMessage('Ошибка соединения с сервером');
      console.error('Error updating strain:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoadingData) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Загрузка данных штамма...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <Edit className="mr-2" />
          Редактировать штамм
        </h2>
        {onCancel && (
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        )}
      </div>

      {message && (
        <div className={`p-4 rounded-md mb-4 ${
          message.includes('успешно') 
            ? 'bg-green-50 text-green-800 border border-green-200' 
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Короткий код штамма */}
          <div>
            <label htmlFor="short_code" className="block text-sm font-medium text-gray-700 mb-1">
              Короткий код штамма *
            </label>
            <input
              type="text"
              id="short_code"
              name="short_code"
              value={formData.short_code}
              onChange={handleInputChange}
              required
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.short_code ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Например: LB001"
            />
            {errors.short_code && (
              <p className="text-red-500 text-sm mt-1">{errors.short_code.join(', ')}</p>
            )}
          </div>

          {/* ID коллекции RCAM */}
          <div>
            <label htmlFor="rcam_collection_id" className="block text-sm font-medium text-gray-700 mb-1">
              ID коллекции RCAM
            </label>
            <input
              type="text"
              id="rcam_collection_id"
              name="rcam_collection_id"
              value={formData.rcam_collection_id}
              onChange={handleInputChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.rcam_collection_id ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Например: RCAM-001"
            />
            {errors.rcam_collection_id && (
              <p className="text-red-500 text-sm mt-1">{errors.rcam_collection_id.join(', ')}</p>
            )}
          </div>
        </div>

        {/* Идентификатор штамма */}
        <div>
          <label htmlFor="identifier" className="block text-sm font-medium text-gray-700 mb-1">
            Идентификатор штамма *
          </label>
          <input
            type="text"
            id="identifier"
            name="identifier"
            value={formData.identifier}
            onChange={handleInputChange}
            required
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.identifier ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Например: Lysobacter antibioticus LB001"
          />
          {errors.identifier && (
            <p className="text-red-500 text-sm mt-1">{errors.identifier.join(', ')}</p>
          )}
        </div>

        {/* rRNA таксономия */}
        <div>
          <label htmlFor="rrna_taxonomy" className="block text-sm font-medium text-gray-700 mb-1">
            rRNA таксономия
          </label>
          <textarea
            id="rrna_taxonomy"
            name="rrna_taxonomy"
            value={formData.rrna_taxonomy}
            onChange={handleInputChange}
            rows={3}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.rrna_taxonomy ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Таксономическая классификация на основе rRNA"
          />
          {errors.rrna_taxonomy && (
            <p className="text-red-500 text-sm mt-1">{errors.rrna_taxonomy.join(', ')}</p>
          )}
        </div>

        {/* Альтернативное название */}
        <div>
          <label htmlFor="name_alt" className="block text-sm font-medium text-gray-700 mb-1">
            Альтернативное название
          </label>
          <input
            type="text"
            id="name_alt"
            name="name_alt"
            value={formData.name_alt}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.name_alt ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Альтернативное или синонимичное название"
          />
          {errors.name_alt && (
            <p className="text-red-500 text-sm mt-1">{errors.name_alt.join(', ')}</p>
          )}
        </div>

        {/* Кнопки управления */}
        <div className="flex justify-end space-x-4 pt-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Отмена
            </button>
          )}
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Save className="mr-2" size={16} />
            {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditStrainForm; 