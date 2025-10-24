import React, { useState } from 'react';
import { X, Plus, Loader2, Dna } from 'lucide-react';
import apiService from '../../../../services/api';
import type { Strain } from '../../../../types';
import type { AxiosError } from 'axios';

interface CreateStrainFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (strain: Strain) => void;
}

export const CreateStrainForm: React.FC<CreateStrainFormProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    short_code: '',
    identifier: '',
    rrna_taxonomy: '',
    name_alt: '',
    rcam_collection_id: ''
  });

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
    setError(null);

    try {
      const strainData = {
        short_code: formData.short_code.trim(),
        identifier: formData.identifier.trim(),
        rrna_taxonomy: formData.rrna_taxonomy.trim() || undefined,
        name_alt: formData.name_alt.trim() || undefined,
        rcam_collection_id: formData.rcam_collection_id.trim() || undefined
      };

      const newStrain = await apiService.createStrain(strainData);
      onSuccess(newStrain);
    } catch (error: unknown) {
      console.error('Ошибка при создании штамма:', error);
      const axErr = error as AxiosError<{ error?: string; message?: string }>;
      const serverMessage = axErr?.response?.data?.error ?? axErr?.response?.data?.message;
      const fallback = error instanceof Error ? error.message : 'Не удалось создать штамм';
      setError(serverMessage || fallback);
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <Dna className="w-4 h-4 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Создать новый штамм</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="p-6 space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* Основная информация */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Короткий код */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Короткий код <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.short_code}
                  onChange={(e) => handleFieldChange('short_code', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Например: ABC123"
                  disabled={loading}
                  required
                />
              </div>

              {/* Идентификатор */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Идентификатор <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.identifier}
                  onChange={(e) => handleFieldChange('identifier', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Название штамма"
                  disabled={loading}
                  required
                />
              </div>

              {/* rRNA таксономия */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  rRNA таксономия
                </label>
                <input
                  type="text"
                  value={formData.rrna_taxonomy}
                  onChange={(e) => handleFieldChange('rrna_taxonomy', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Таксономическая классификация"
                  disabled={loading}
                />
              </div>

              {/* Альтернативное название */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Альтернативное название
                </label>
                <input
                  type="text"
                  value={formData.name_alt}
                  onChange={(e) => handleFieldChange('name_alt', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Дополнительное название"
                  disabled={loading}
                />
              </div>

              {/* ID коллекции RCAM */}
              <div className="space-y-2 md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  ID коллекции RCAM
                </label>
                <input
                  type="text"
                  value={formData.rcam_collection_id}
                  onChange={(e) => handleFieldChange('rcam_collection_id', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Идентификатор в коллекции RCAM"
                  disabled={loading}
                />
              </div>
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
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Создание...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Создать штамм</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};