import React, { useState, useEffect } from 'react';
import { Trash2, Edit, Download, Check, X, Loader2, Eye, FileText, FileSpreadsheet } from 'lucide-react';
import apiService from '../services/api';
import type { 
  Sample, 
  SampleFilters, 
  Strain,
  StrainFilters,
  ReferenceData,
  ReferenceStrain,
  ReferenceSource,
  ReferenceLocation,
  ReferenceIndexLetter,
  ReferenceComment,
  ReferenceAppendixNote
} from '../types';
import type { AxiosError } from 'axios';

interface BulkOperationsPanelProps {
  selectedIds: number[];
  allSamples: Sample[];
  onClearSelection: () => void;
  onRefresh: () => void;
  filters?: SampleFilters | StrainFilters;
  entityType?: 'samples' | 'strains';
  allStrains?: Strain[];
  totalCount?: number;
}

interface BulkUpdateData {
  // Boolean fields for samples
  has_photo?: boolean;
  
  // Fields for samples - related objects
  strain_id?: number;
  index_letter_id?: number;
  source_id?: number;
  location_id?: number;
  comment_id?: number;
  appendix_note_id?: number;
  original_sample_number?: string;

  // Fields for strains
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

type PreviewValue = string | number | boolean | null | undefined;
type BulkUpdateFieldKey = keyof BulkUpdateData;

interface PreviewChange {
  id: number;
  currentValues: Partial<Record<BulkUpdateFieldKey, PreviewValue>>;
  newValues: Partial<Record<BulkUpdateFieldKey, PreviewValue>>;
  changes: Partial<Record<BulkUpdateFieldKey, { from: PreviewValue; to: PreviewValue }>>;
}

type FieldOptionsKey = 'strains' | 'index_letters' | 'sources' | 'locations' | 'comments' | 'appendix_notes';
type UpdateFieldType = 'boolean' | 'select' | 'text';
interface UpdateField { 
  key: BulkUpdateFieldKey; 
  label: string; 
  type: UpdateFieldType; 
  options?: FieldOptionsKey; 
}

type ReferenceDictionary = {
  strains: ReferenceStrain[];
  index_letters: ReferenceIndexLetter[];
  sources: ReferenceSource[];
  locations: ReferenceLocation[];
  comments: ReferenceComment[];
  appendix_notes: ReferenceAppendixNote[];
};

type ReferenceOption = ReferenceDictionary[FieldOptionsKey][number];

type ExtendedReferenceData = ReferenceData & {
  comments?: ReferenceComment[];
  appendix_notes?: ReferenceAppendixNote[];
};

const normalizeReferenceData = (data: ExtendedReferenceData): ReferenceDictionary => ({
  strains: data.strains ?? [],
  index_letters: data.index_letters ?? [],
  sources: data.sources ?? [],
  locations: data.locations ?? [],
  comments: data.comments ?? [],
  appendix_notes: data.appendix_notes ?? [],
});

const getOptionLabel = (option: ReferenceOption): string => {
  if ('display_name' in option && option.display_name) return option.display_name;
  if ('short_code' in option && option.short_code) return option.short_code;
  if ('identifier' in option && option.identifier) return option.identifier;
  if ('name' in option && option.name) return option.name;
  if ('letter_value' in option && option.letter_value) return option.letter_value;
  if ('text' in option && option.text) return option.text;
  if ('organism_name' in option && option.organism_name) return option.organism_name;
  return `ID ${option.id}`;
};

type ApiErrorResponse = { error?: string; message?: string; detail?: string };

const getErrorMessage = (error: unknown): string => {
  const axiosError = error as AxiosError<ApiErrorResponse>;
  const data = axiosError.response?.data;
  if (data) {
    return data.error ?? data.message ?? data.detail ?? axiosError.message ?? 'Unknown error';
  }
  if (axiosError.message) {
    return axiosError.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unknown error';
};

const sampleUpdateFields: UpdateField[] = [
  { key: 'has_photo', label: 'Has Photo', type: 'boolean' },
  { key: 'strain_id', label: 'Strain', type: 'select', options: 'strains' },
  { key: 'index_letter_id', label: 'Index Letter', type: 'select', options: 'index_letters' },
  { key: 'source_id', label: 'Source', type: 'select', options: 'sources' },
  { key: 'location_id', label: 'Location', type: 'select', options: 'locations' },
  { key: 'comment_id', label: 'Comment', type: 'select', options: 'comments' },
  { key: 'appendix_note_id', label: 'Appendix Note', type: 'select', options: 'appendix_notes' },
  { key: 'original_sample_number', label: 'Original Sample Number', type: 'text' },
];

const strainUpdateFields: UpdateField[] = [
  { key: 'short_code', label: 'Short Code', type: 'text' },
  { key: 'identifier', label: 'Identifier', type: 'text' },
  { key: 'rrna_taxonomy', label: 'rRNA Taxonomy', type: 'text' },
  { key: 'name_alt', label: 'Alternative Name', type: 'text' },
  { key: 'rcam_collection_id', label: 'RCAM ID', type: 'text' },
];

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
  const [showBulkUpdate, setShowBulkUpdate] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [updateData, setUpdateData] = useState<BulkUpdateData>({});
  const [referenceData, setReferenceData] = useState<ReferenceDictionary>({
    strains: [],
    index_letters: [],
    sources: [],
    locations: [],
    comments: [],
    appendix_notes: [],
  });
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'csv',
    fields: [],
    includeRelated: true,
  });
  const [previewChanges, setPreviewChanges] = useState<PreviewChange[]>([]);

  const currentUpdateFields = entityType === 'strains' ? strainUpdateFields : sampleUpdateFields;
  const selectedEntities = entityType === 'strains' ? allStrains.filter(s => selectedIds.includes(s.id)) : allSamples.filter(s => selectedIds.includes(s.id));

  useEffect(() => {
    if (showBulkUpdate || showExport) {
      loadReferenceData();
    }
  }, [showBulkUpdate, showExport]);

  const loadReferenceData = async () => {
    try {
      const data = await apiService.getReferenceData();
      setReferenceData(normalizeReferenceData(data));
    } catch (error) {
      console.error('Error loading reference data:', error);
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedIds.length} ${entityType}?`)) {
      return;
    }

    setLoading(true);
    try {
      const endpoint = entityType === 'strains' ? 'bulkDeleteStrains' : 'bulkDeleteSamples';
      await apiService[endpoint](selectedIds);
      onRefresh();
      onClearSelection();
      alert(`Successfully deleted ${selectedIds.length} ${entityType}`);
    } catch (error) {
      alert(`Error during bulk delete: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const generatePreview = async () => {
    const changes: PreviewChange[] = selectedEntities.map(entity => {
      const currentValues: Partial<Record<BulkUpdateFieldKey, PreviewValue>> = {};
      const newValues: Partial<Record<BulkUpdateFieldKey, PreviewValue>> = {};
      const entityChanges: Partial<Record<BulkUpdateFieldKey, { from: PreviewValue; to: PreviewValue }>> = {};

      Object.entries(updateData).forEach(([key, value]) => {
        if (value !== undefined) {
          const fieldKey = key as BulkUpdateFieldKey;
          const entityPreview = entity as unknown as Partial<Record<BulkUpdateFieldKey, PreviewValue>>;
          const currentValue = entityPreview[fieldKey];
          currentValues[fieldKey] = currentValue;
          newValues[fieldKey] = value;
          
          if (currentValue !== value) {
            entityChanges[fieldKey] = { from: currentValue, to: value };
          }
        }
      });

      return {
        id: entity.id,
        currentValues,
        newValues,
        changes: entityChanges,
      };
    });

    setPreviewChanges(changes);
    setShowPreview(true);
  };

  const handleBulkUpdate = async () => {
    if (Object.keys(updateData).length === 0) {
      alert('Please select at least one field to update');
      return;
    }

    setLoading(true);
    try {
      const endpoint = entityType === 'strains' ? 'bulkUpdateStrains' : 'bulkUpdateSamples';
      await apiService[endpoint](selectedIds, updateData as Record<string, unknown>);
      onRefresh();
      onClearSelection();
      setShowBulkUpdate(false);
      setUpdateData({});
      alert(`Successfully updated ${selectedIds.length} ${entityType}`);
    } catch (error) {
      alert(`Error during bulk update: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const renderUpdateField = (field: UpdateField) => {
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
            <option value="">Don't change</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
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
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            placeholder="Enter new value"
          />
        </div>
      );
    }
    
    if (type === 'select' && options) {
      const optionsList = referenceData[options] || [];
      return (
        <div key={key} className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">{label}</label>
          <select
            value={updateData[key as keyof BulkUpdateData] as number || ''}
            onChange={(e) => setUpdateData(prev => ({
              ...prev,
              [key]: e.target.value ? Number(e.target.value) : undefined
            }))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="">Don't change</option>
            {optionsList.map(option => (
              <option key={option.id} value={option.id}>
                {getOptionLabel(option)}
              </option>
            ))}
          </select>
        </div>
      );
    }
    
    return null;
  };

  const handleExport = async () => {
    if (exportConfig.fields.length === 0) {
      alert('Please select at least one field to export');
      return;
    }

    setLoading(true);
    try {
      const endpoint = entityType === 'strains' ? 'exportStrains' : 'exportSamples';
      const blob = await apiService[endpoint](
        filters,
        selectedIds,
        {
          format: exportConfig.format,
          fields: exportConfig.fields,
          includeRelated: exportConfig.includeRelated
        }
      );

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = exportConfig.customFilename || `${entityType}_export.${exportConfig.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setShowExport(false);
      alert(`Successfully exported ${selectedIds.length} ${entityType}`);
    } catch (error) {
      alert(`Error during export: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  if (selectedIds.length === 0) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-blue-800">
            {selectedIds.length} {entityType} selected
            {totalCount && ` (of ${totalCount} total)`}
          </span>
          <button
            onClick={onClearSelection}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Clear selection
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBulkUpdate(true)}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            disabled={loading}
          >
            <Edit size={14} />
            <span>Bulk Update</span>
          </button>
          
          <button
            onClick={() => setShowExport(true)}
            className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            disabled={loading}
          >
            <Download size={14} />
            <span>Export</span>
          </button>
          
          <button
            onClick={handleBulkDelete}
            className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            disabled={loading}
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Bulk Update Modal */}
      {showBulkUpdate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Bulk Update {entityType}</h3>
              <button
                onClick={() => setShowBulkUpdate(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4 mb-6">
              {currentUpdateFields.map(renderUpdateField)}
            </div>
            
            <div className="flex items-center justify-between">
              <button
                onClick={generatePreview}
                className="flex items-center space-x-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                disabled={loading || Object.keys(updateData).length === 0}
              >
                <Eye size={16} />
                <span>Preview Changes</span>
              </button>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowBulkUpdate(false)}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkUpdate}
                  className="flex items-center space-x-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  disabled={loading || Object.keys(updateData).length === 0}
                >
                  {loading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Updating...</span>
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      <span>Update {selectedIds.length} {entityType}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Export {entityType}</h3>
              <button
                onClick={() => setShowExport(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                <div className="flex space-x-4">
                  {(['csv', 'xlsx', 'json'] as const).map(format => (
                    <label key={format} className="flex items-center">
                      <input
                        type="radio"
                        name="format"
                        value={format}
                        checked={exportConfig.format === format}
                        onChange={(e) => setExportConfig(prev => ({ ...prev, format: e.target.value as ExportConfig['format'] }))}
                        className="mr-2"
                      />
                      <span className="flex items-center space-x-1">
                        {format === 'csv' && <FileText size={16} />}
                        {format === 'xlsx' && <FileSpreadsheet size={16} />}
                        {format === 'json' && <FileText size={16} />}
                        <span>{format.toUpperCase()}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Fields to Export</label>
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto border border-gray-200 rounded p-2">
                  {currentUpdateFields.map(field => (
                    <label key={field.key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportConfig.fields.includes(field.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setExportConfig(prev => ({ ...prev, fields: [...prev.fields, field.key] }));
                          } else {
                            setExportConfig(prev => ({ ...prev, fields: prev.fields.filter(f => f !== field.key) }));
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm">{field.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportConfig.includeRelated}
                    onChange={(e) => setExportConfig(prev => ({ ...prev, includeRelated: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm">Include related data</span>
                </label>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Custom Filename (optional)</label>
                <input
                  type="text"
                  value={exportConfig.customFilename || ''}
                  onChange={(e) => setExportConfig(prev => ({ ...prev, customFilename: e.target.value }))}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                  placeholder={`${entityType}_export.${exportConfig.format}`}
                />
              </div>
            </div>
            
            <div className="flex items-center justify-end space-x-2">
              <button
                onClick={() => setShowExport(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleExport}
                className="flex items-center space-x-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                disabled={loading || exportConfig.fields.length === 0}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Exporting...</span>
                  </>
                ) : (
                  <>
                    <Download size={16} />
                    <span>Export {selectedIds.length} {entityType}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Preview Changes</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4 mb-6">
              {previewChanges.map(change => (
                <div key={change.id} className="border border-gray-200 rounded p-4">
                  <h4 className="font-medium mb-2">{entityType.slice(0, -1)} ID: {change.id}</h4>
                  {Object.keys(change.changes).length > 0 ? (
                    <div className="space-y-2">
                      {Object.entries(change.changes).map(([field, { from, to }]) => (
                        <div key={field} className="flex items-center justify-between text-sm">
                          <span className="font-medium">{currentUpdateFields.find(f => f.key === field)?.label}:</span>
                          <span>
                            <span className="text-red-600">{String(from)}</span>
                            <span className="mx-2">→</span>
                            <span className="text-green-600">{String(to)}</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No changes</p>
                  )}
                </div>
              ))}
            </div>
            
            <div className="flex items-center justify-end space-x-2">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowPreview(false);
                  handleBulkUpdate();
                }}
                className="flex items-center space-x-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <>
                    <Check size={16} />
                    <span>Confirm Update</span>
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





