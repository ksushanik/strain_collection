import React, { useState } from 'react';
import { Trash2, Edit, Download, Check, X, Loader2 } from 'lucide-react';
import apiService from '../services/api';
import type { Sample, SampleFilters } from '../types';

interface BulkOperationsPanelProps {
  selectedIds: number[];
  allSamples: Sample[];
  onClearSelection: () => void;
  onRefresh: () => void;
  filters?: SampleFilters;
}

interface BulkUpdateData {
  has_photo?: boolean;
  is_identified?: boolean;
  has_antibiotic_activity?: boolean;
  has_genome?: boolean;
  has_biochemistry?: boolean;
  seq_status?: boolean;
}

const BulkOperationsPanel: React.FC<BulkOperationsPanelProps> = ({
  selectedIds,
  allSamples,
  onClearSelection,
  onRefresh,
  filters
}) => {
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [updateData, setUpdateData] = useState<BulkUpdateData>({});
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleBulkDelete = async () => {
    setLoading(true);
    try {
      const result = await apiService.bulkDeleteSamples(selectedIds);
      alert(`✅ ${result.message}`);
      onClearSelection();
      onRefresh();
    } catch (error: any) {
      console.error('Ошибка массового удаления:', error);
      alert(`❌ Ошибка: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleBulkUpdate = async () => {
    if (Object.keys(updateData).length === 0) {
      alert('Выберите поля для обновления');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.bulkUpdateSamples(selectedIds, updateData);
      alert(`✅ ${result.message}`);
      onClearSelection();
      onRefresh();
      setShowUpdateForm(false);
      setUpdateData({});
    } catch (error: any) {
      console.error('Ошибка массового обновления:', error);
      alert(`❌ Ошибка: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setLoading(true);
    try {
      const blob = await apiService.exportSamples(filters, selectedIds);
      
      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `samples_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      alert(`✅ Экспортировано ${selectedIds.length} образцов`);
    } catch (error: any) {
      console.error('Ошибка экспорта:', error);
      alert(`❌ Ошибка экспорта: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateFieldOptions = [
    { key: 'has_photo', label: 'Есть фото' },
    { key: 'is_identified', label: 'Идентифицирован' },
    { key: 'has_antibiotic_activity', label: 'АБ активность' },
    { key: 'has_genome', label: 'Есть геном' },
    { key: 'has_biochemistry', label: 'Есть биохимия' },
    { key: 'seq_status', label: 'Секвенирован' },
  ];

  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-blue-800 font-medium">
            Выбрано: {selectedIds.length} образцов
          </span>
          
          <div className="flex space-x-2">
            {/* Bulk Delete */}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={loading}
              className="bg-red-600 text-white px-3 py-1 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center space-x-1 text-sm"
            >
              <Trash2 className="w-4 h-4" />
              <span>Удалить</span>
            </button>

            {/* Bulk Update */}
            <button
              onClick={() => setShowUpdateForm(true)}
              disabled={loading}
              className="bg-yellow-600 text-white px-3 py-1 rounded-lg hover:bg-yellow-700 disabled:opacity-50 flex items-center space-x-1 text-sm"
            >
              <Edit className="w-4 h-4" />
              <span>Изменить</span>
            </button>

            {/* Export */}
            <button
              onClick={handleExport}
              disabled={loading}
              className="bg-green-600 text-white px-3 py-1 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-1 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Экспорт</span>
            </button>
          </div>
        </div>

        <button
          onClick={onClearSelection}
          className="text-gray-500 hover:text-gray-700"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Подтверждение удаления
            </h3>
            <p className="text-gray-600 mb-6">
              Вы уверены, что хотите удалить {selectedIds.length} образцов? 
              Это действие нельзя отменить.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="btn-secondary"
                disabled={loading}
              >
                Отмена
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={loading}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Удаление...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Удалить
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Update Form */}
      {showUpdateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Массовое обновление {selectedIds.length} образцов
            </h3>
            
            <div className="space-y-4">
              {updateFieldOptions.map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    {label}
                  </label>
                  <select
                    value={updateData[key as keyof BulkUpdateData] === undefined ? '' : updateData[key as keyof BulkUpdateData]?.toString()}
                    onChange={(e) => setUpdateData(prev => ({
                      ...prev,
                      [key]: e.target.value === '' ? undefined : e.target.value === 'true'
                    }))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="">Не изменять</option>
                    <option value="true">Да</option>
                    <option value="false">Нет</option>
                  </select>
                </div>
              ))}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowUpdateForm(false);
                  setUpdateData({});
                }}
                className="btn-secondary"
                disabled={loading}
              >
                Отмена
              </button>
              <button
                onClick={handleBulkUpdate}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Обновление...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-2" />
                    Обновить
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkOperationsPanel; 