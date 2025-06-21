import React, { useState, useEffect } from 'react';
import { Trash2, Edit, Download, Check, X, Loader2, Eye, FileText, FileSpreadsheet } from 'lucide-react';
import apiService from '../services/api';
import type { Sample, SampleFilters, Strain } from '../types';

interface BulkOperationsPanelProps {
  selectedIds: number[];
  allSamples: Sample[];
  onClearSelection: () => void;
  onRefresh: () => void;
  filters?: SampleFilters;
  entityType?: 'samples' | 'strains'; // Новое: поддержка штаммов
  allStrains?: Strain[]; // Новое: для штаммов
  totalCount?: number; // Общее количество отфильтрованных записей
}

interface BulkUpdateData {
  // Boolean поля для образцов
  has_photo?: boolean;
  is_identified?: boolean;
  has_antibiotic_activity?: boolean;
  has_genome?: boolean;
  has_biochemistry?: boolean;
  seq_status?: boolean;
  
  // Поля для образцов - связанные объекты
  strain_id?: number;
  index_letter_id?: number;
  source_id?: number;
  location_id?: number;
  comment_id?: number;
  appendix_note_id?: number;
  original_sample_number?: string;

  // Поля для штаммов
  short_code?: string;
  identifier?: string;
  rrna_taxonomy?: string;
  name_alt?: string;
  rcam_collection_id?: string;
}

interface ExportConfig {
  format: 'csv' | 'xlsx' | 'json';
  fields: string[];
  includeRelated: boolean;
  customFilename?: string;
}

interface PreviewChange {
  id: number;
  currentValues: Record<string, any>;
  newValues: Record<string, any>;
  changes: Record<string, { from: any; to: any }>;
}

const BulkOperationsPanel: React.FC<BulkOperationsPanelProps> = ({
  selectedIds,
  allSamples,
  onClearSelection,
  onRefresh,
  filters,
  entityType = 'samples',
  allStrains = [],
  totalCount
}) => {
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [showExportConfig, setShowExportConfig] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [updateData, setUpdateData] = useState<BulkUpdateData>({});
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'csv',
    fields: [],
    includeRelated: true
  });
  const [previewChanges, setPreviewChanges] = useState<PreviewChange[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [referenceData, setReferenceData] = useState<any>(null);
  const [exportAll, setExportAll] = useState<boolean>(false);

  // Загружаем справочные данные
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const data = await apiService.getReferenceData();
        setReferenceData(data);
      } catch (error) {
        console.error('Ошибка загрузки справочных данных:', error);
      }
    };
    loadReferenceData();
  }, []);

  // Расширенные поля для обновления
  const getSampleUpdateFields = () => [
    // Boolean поля для образцов
    { key: 'has_photo', label: 'Есть фото', type: 'boolean' },
    { key: 'is_identified', label: 'Идентифицирован', type: 'boolean' },
    { key: 'has_antibiotic_activity', label: 'АБ активность', type: 'boolean' },
    { key: 'has_genome', label: 'Есть геном', type: 'boolean' },
    { key: 'has_biochemistry', label: 'Есть биохимия', type: 'boolean' },
    { key: 'seq_status', label: 'Секвенирован', type: 'boolean' },
    
    // Связанные объекты для образцов
    { key: 'strain_id', label: 'Штамм', type: 'select', options: 'strains' },
    { key: 'index_letter_id', label: 'Индексная буква', type: 'select', options: 'index_letters' },
    { key: 'source_id', label: 'Источник', type: 'select', options: 'sources' },
    { key: 'location_id', label: 'Локация', type: 'select', options: 'locations' },
    { key: 'comment_id', label: 'Комментарий', type: 'select', options: 'comments' },
    { key: 'appendix_note_id', label: 'Примечание', type: 'select', options: 'appendix_notes' },
    
    // Текстовые поля для образцов
    { key: 'original_sample_number', label: 'Номер образца', type: 'text' },
  ];

  const getStrainUpdateFields = () => [
    // Текстовые поля для штаммов
    { key: 'short_code', label: 'Короткий код', type: 'text' },
    { key: 'identifier', label: 'Идентификатор', type: 'text' },
    { key: 'rrna_taxonomy', label: 'rRNA таксономия', type: 'text' },
    { key: 'name_alt', label: 'Альтернативное название', type: 'text' },
    { key: 'rcam_collection_id', label: 'RCAM ID', type: 'text' },
  ];

  const updateFieldOptions = entityType === 'samples' ? getSampleUpdateFields() : getStrainUpdateFields();

  // Доступные поля для экспорта
  const getSampleExportFields = () => [
    { key: 'id', label: 'ID' },
    { key: 'strain_short_code', label: 'Код штамма' },
    { key: 'strain_identifier', label: 'Идентификатор штамма' },
    { key: 'original_sample_number', label: 'Номер образца' },
    { key: 'has_photo', label: 'Есть фото' },
    { key: 'is_identified', label: 'Идентифицирован' },
    { key: 'has_antibiotic_activity', label: 'АБ активность' },
    { key: 'has_genome', label: 'Есть геном' },
    { key: 'has_biochemistry', label: 'Есть биохимия' },
    { key: 'seq_status', label: 'Секвенирован' },
    { key: 'source_organism', label: 'Организм источника' },
    { key: 'source_type', label: 'Тип источника' },
    { key: 'location_name', label: 'Локация' },
    { key: 'storage_cell', label: 'Ячейка хранения' },
    { key: 'created_at', label: 'Дата создания' },
    { key: 'updated_at', label: 'Дата обновления' },
  ];

  const getStrainExportFields = () => [
    { key: 'id', label: 'ID' },
    { key: 'short_code', label: 'Короткий код' },
    { key: 'identifier', label: 'Идентификатор' },
    { key: 'rrna_taxonomy', label: 'rRNA таксономия' },
    { key: 'name_alt', label: 'Альтернативное название' },
    { key: 'rcam_collection_id', label: 'RCAM ID' },
    { key: 'created_at', label: 'Дата создания' },
    { key: 'updated_at', label: 'Дата обновления' },
  ];

  const exportFieldOptions = entityType === 'samples' ? getSampleExportFields() : getStrainExportFields();

  // Генерация предварительного просмотра изменений
  const generatePreview = () => {
    const changes: PreviewChange[] = [];
    
    selectedIds.forEach(id => {
      const entity = entityType === 'samples' 
        ? allSamples.find(s => s.id === id)
        : allStrains.find(s => s.id === id);
      
      if (!entity) return;

      const currentValues: Record<string, any> = {};
      const newValues: Record<string, any> = {};
      const entityChanges: Record<string, { from: any; to: any }> = {};

      Object.entries(updateData).forEach(([field, value]) => {
        if (value !== undefined) {
          const currentValue = (entity as any)[field];
          if (currentValue !== value) {
            currentValues[field] = currentValue;
            newValues[field] = value;
            entityChanges[field] = { from: currentValue, to: value };
          }
        }
      });

      if (Object.keys(entityChanges).length > 0) {
        changes.push({
          id,
          currentValues,
          newValues,
          changes: entityChanges
        });
      }
    });

    setPreviewChanges(changes);
    setShowPreview(true);
  };

  // Применение изменений после предварительного просмотра
  const applyChanges = async () => {
    if (Object.keys(updateData).length === 0) {
      alert('Выберите поля для обновления');
      return;
    }

    setLoading(true);
    try {
      const result = entityType === 'samples'
        ? await apiService.bulkUpdateSamples(selectedIds, updateData)
        : await apiService.bulkUpdateStrains(selectedIds, updateData as Partial<Strain>);
      
      alert(`✅ ${result.message}`);
      onClearSelection();
      onRefresh();
      setShowUpdateForm(false);
      setShowPreview(false);
      setUpdateData({});
    } catch (error: any) {
      console.error('Ошибка массового обновления:', error);
      alert(`❌ Ошибка: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    setLoading(true);
    try {
      const result = entityType === 'samples'
        ? await apiService.bulkDeleteSamples(selectedIds)
        : await apiService.bulkDeleteStrains(selectedIds);
      
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

  const handleExport = async () => {
    setLoading(true);
    try {
      let blob: Blob;
      
      const idsParam = exportAll ? undefined : selectedIds;
      if (entityType === 'strains') {
        blob = await apiService.exportStrains(filters, idsParam, exportConfig);
      } else {
        blob = await apiService.exportSamples(filters, idsParam, exportConfig);
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const filename = exportConfig.customFilename || 
        `${entityType}_export_${new Date().toISOString().split('T')[0]}.${exportConfig.format}`;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      alert('✅ Экспорт успешно выполнен');
      setShowExportConfig(false);
    } catch (error: any) {
      console.error('Ошибка экспорта:', error);
      alert(`❌ Ошибка экспорта: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderUpdateField = (field: any) => {
    const { key, label, type, options } = field;
    
    if (type === 'boolean') {
      return (
        <div key={key} className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">{label}</label>
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
      );
    }
    
    if (type === 'text') {
      return (
        <div key={key} className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          <input
            type="text"
            value={updateData[key as keyof BulkUpdateData] as string || ''}
            onChange={(e) => setUpdateData(prev => ({
              ...prev,
              [key]: e.target.value || undefined
            }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm w-32"
            placeholder="Новое значение"
          />
        </div>
      );
    }
    
    if (type === 'select' && referenceData && options) {
      const optionsList = referenceData[options] || [];
      return (
        <div key={key} className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          <select
            value={updateData[key as keyof BulkUpdateData] as number || ''}
            onChange={(e) => setUpdateData(prev => ({
              ...prev,
              [key]: e.target.value ? parseInt(e.target.value) : undefined
            }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Не изменять</option>
            {optionsList.map((option: any) => (
              <option key={option.id} value={option.id}>
                {option.name || option.short_code || option.identifier || option.letter || option.text}
              </option>
            ))}
          </select>
        </div>
      );
    }
    
    return null;
  };

  if (selectedIds.length === 0) {
    return null;
  }

  const entityLabel = entityType === 'samples' ? 'образцов' : 'штаммов';

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-blue-800 font-medium">
            Выбрано: {selectedIds.length} {entityLabel}
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
              onClick={() => setShowExportConfig(true)}
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
              Вы уверены, что хотите удалить {selectedIds.length} {entityLabel}? 
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

      {/* Enhanced Update Form */}
      {showUpdateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Массовое обновление {selectedIds.length} {entityLabel}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {updateFieldOptions.map(renderUpdateField)}
            </div>

            <div className="flex justify-between items-center">
              <button
                onClick={generatePreview}
                disabled={loading || Object.keys(updateData).length === 0}
                className="bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200 disabled:opacity-50 flex items-center"
              >
                <Eye className="w-4 h-4 mr-2" />
                Предварительный просмотр
              </button>
              
              <div className="flex space-x-3">
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
                  onClick={applyChanges}
                  disabled={loading || Object.keys(updateData).length === 0}
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
                      Применить изменения
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Changes Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Предварительный просмотр изменений
            </h3>
            
            {previewChanges.length === 0 ? (
              <p className="text-gray-600 mb-6">Нет изменений для применения</p>
            ) : (
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-4">
                  Будет изменено {previewChanges.length} записей из {selectedIds.length} выбранных
                </p>
                
                <div className="max-h-64 overflow-y-auto border rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Поле</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Было</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Станет</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {previewChanges.map(change => (
                        Object.entries(change.changes).map(([field, { from, to }]) => (
                          <tr key={`${change.id}-${field}`}>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{change.id}</td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{field}</td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">{String(from)}</td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-green-600">{String(to)}</td>
                          </tr>
                        ))
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowPreview(false)}
                className="btn-secondary"
              >
                Назад к редактированию
              </button>
              {previewChanges.length > 0 && (
                <button
                  onClick={applyChanges}
                  disabled={loading}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Применение...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Применить изменения
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Export Configuration Modal */}
      {showExportConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Настройка экспорта
            </h3>
            
            <div className="space-y-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Формат файла</label>
                <div className="flex space-x-4">
                  {[
                    { value: 'csv', label: 'CSV', icon: FileText },
                    { value: 'xlsx', label: 'Excel', icon: FileSpreadsheet },
                    { value: 'json', label: 'JSON', icon: FileText }
                  ].map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      onClick={() => setExportConfig(prev => ({ ...prev, format: value as any }))}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg border ${
                        exportConfig.format === value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Field Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Поля для экспорта</label>
                <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-lg p-3">
                  {exportFieldOptions.map(({ key, label }) => (
                    <label key={key} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={exportConfig.fields.includes(key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setExportConfig(prev => ({
                              ...prev,
                              fields: [...prev.fields, key]
                            }));
                          } else {
                            setExportConfig(prev => ({
                              ...prev,
                              fields: prev.fields.filter(f => f !== key)
                            }));
                          }
                        }}
                        className="rounded"
                      />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
                <div className="mt-2 flex space-x-2">
                  <button
                    onClick={() => setExportConfig(prev => ({
                      ...prev,
                      fields: exportFieldOptions.map(f => f.key)
                    }))}
                    className="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Выбрать все
                  </button>
                  <button
                    onClick={() => setExportConfig(prev => ({ ...prev, fields: [] }))}
                    className="text-xs text-gray-600 hover:text-gray-800"
                  >
                    Очистить
                  </button>
                </div>
              </div>

              {/* Export All Option */}
              <div>
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={exportAll}
                    onChange={(e) => setExportAll(e.target.checked)}
                    className="rounded"
                  />
                  <span>
                    Экспортировать {totalCount ? `все ${totalCount}` : 'все'} записи (игнорировать выбор)
                  </span>
                </label>
              </div>

              {/* Additional Options */}
              <div>
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={exportConfig.includeRelated}
                    onChange={(e) => setExportConfig(prev => ({
                      ...prev,
                      includeRelated: e.target.checked
                    }))}
                    className="rounded"
                  />
                  <span>Включить связанные данные</span>
                </label>
              </div>

              {/* Custom Filename */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Имя файла (опционально)</label>
                <input
                  type="text"
                  value={exportConfig.customFilename || ''}
                  onChange={(e) => setExportConfig(prev => ({
                    ...prev,
                    customFilename: e.target.value
                  }))}
                  placeholder={`${entityType}_export_${new Date().toISOString().split('T')[0]}.${exportConfig.format}`}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowExportConfig(false)}
                className="btn-secondary"
                disabled={loading}
              >
                Отмена
              </button>
              <button
                onClick={handleExport}
                disabled={loading || exportConfig.fields.length === 0}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Экспорт...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Экспортировать
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