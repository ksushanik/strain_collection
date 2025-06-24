import axios from 'axios';
import type { 
  Strain, 
  Sample, 
  StatsResponse, 
  ValidationResponse,
  StrainFilters,
  SampleFilters,
  ReferenceData,
  CreateSampleData,
  UpdateSampleData,
  SamplesListResponse,
  StrainsListResponse,
  StorageListResponse
} from '../types';

const API_BASE_URL = '/api';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем интерсептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Общие endpoints
  async getStatus() {
    const response = await api.get('/');
    return response.data;
  },

  async getStats(): Promise<StatsResponse> {
    const response = await api.get('/stats/');
    return response.data;
  },

  async getAnalytics(): Promise<unknown> {
    const response = await api.get('/analytics/');
    return response.data;
  },

  // Справочные данные
  async getReferenceData(): Promise<ReferenceData> {
    const response = await api.get('/reference-data/');
    return response.data;
  },

  // Штаммы
  async getStrains(filters?: StrainFilters): Promise<StrainsListResponse> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.rcam_id) params.append('rcam_id', filters.rcam_id);
    if (filters?.taxonomy) params.append('taxonomy', filters.taxonomy);
    if (filters?.short_code) params.append('short_code', filters.short_code);
    if (filters?.identifier) params.append('identifier', filters.identifier);
    if (filters?.created_after) params.append('created_after', filters.created_after);
    if (filters?.created_before) params.append('created_before', filters.created_before);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    
    const response = await api.get(`/strains/?${params.toString()}`);
    return response.data;
  },

  async getStrain(id: number): Promise<Strain> {
    const response = await api.get(`/strains/${id}/`);
    return response.data;
  },

  async createStrain(data: Partial<Strain>): Promise<Strain> {
    const response = await api.post('/strains/create/', data);
    return response.data;
  },

  async updateStrain(id: number, data: Partial<Strain>): Promise<Strain> {
    const response = await api.put(`/strains/${id}/update/`, data);
    return response.data;
  },

  async deleteStrain(id: number): Promise<{ message: string; deleted_strain: { id: number; short_code: string; identifier: string } }> {
    const response = await api.delete(`/strains/${id}/delete/`);
    return response.data;
  },

  async validateStrain(data: Partial<Strain>): Promise<ValidationResponse> {
    const response = await api.post('/strains/validate/', data);
    return response.data;
  },

  // Образцы - полный CRUD
  async getSamples(filters?: SampleFilters): Promise<SamplesListResponse> {
    const params = new URLSearchParams();
    if (filters?.strain_id) params.append('strain_id', filters.strain_id.toString());
    if (filters?.search) params.append('search', filters.search);
    if (filters?.has_photo !== undefined) params.append('has_photo', filters.has_photo.toString());
    if (filters?.is_identified !== undefined) params.append('is_identified', filters.is_identified.toString());
    if (filters?.has_antibiotic_activity !== undefined) params.append('has_antibiotic_activity', filters.has_antibiotic_activity.toString());
    if (filters?.has_genome !== undefined) params.append('has_genome', filters.has_genome.toString());
    if (filters?.has_biochemistry !== undefined) params.append('has_biochemistry', filters.has_biochemistry.toString());
    if (filters?.seq_status !== undefined) params.append('seq_status', filters.seq_status.toString());
    if (filters?.box_id) params.append('box_id', filters.box_id);
    if (filters?.source_id) params.append('source_id', filters.source_id.toString());
    if (filters?.location_id) params.append('location_id', filters.location_id.toString());
    if (filters?.source_type) params.append('source_type', filters.source_type);
    if (filters?.organism_name) params.append('organism_name', filters.organism_name);
    if (filters?.created_after) params.append('created_after', filters.created_after);
    if (filters?.created_before) params.append('created_before', filters.created_before);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    
    const response = await api.get(`/samples/?${params.toString()}`);
    return response.data;
  },

  async getSample(id: number): Promise<Sample> {
    const response = await api.get(`/samples/${id}/`);
    return response.data;
  },

  async createSample(data: CreateSampleData): Promise<{ id: number; message: string; sample: Partial<Sample> }> {
    const response = await api.post('/samples/create/', data);
    return response.data;
  },

  async updateSample(id: number, data: UpdateSampleData): Promise<{ id: number; message: string; updated_fields: string[] }> {
    const response = await api.put(`/samples/${id}/update/`, data);
    return response.data;
  },

  async deleteSample(id: number): Promise<{ message: string; deleted_sample: string }> {
    const response = await api.delete(`/samples/${id}/delete/`);
    return response.data;
  },

  async getSamplesByStrain(strainId: number): Promise<SamplesListResponse> {
    const response = await api.get(`/samples/?strain_id=${strainId}`);
    return response.data;
  },

  async validateSample(data: Partial<Sample>): Promise<ValidationResponse> {
    const response = await api.post('/samples/validate/', data);
    return response.data;
  },

  // Массовые операции с образцами
  async bulkDeleteSamples(sampleIds: number[]): Promise<{ message: string; deleted_count: number; deleted_samples: string[] }> {
    const response = await api.post('/samples/bulk-delete/', { sample_ids: sampleIds });
    return response.data;
  },

  async bulkUpdateSamples(sampleIds: number[], updateData: Partial<Sample>): Promise<{ message: string; updated_count: number; updated_fields: string[] }> {
    const response = await api.post('/samples/bulk-update/', { 
      sample_ids: sampleIds, 
      update_data: updateData 
    });
    return response.data;
  },

  async exportSamples(filters?: SampleFilters, sampleIds?: number[], exportConfig?: Record<string, unknown>): Promise<Blob> {
    const requestData: Record<string, unknown> = {};

    if (sampleIds?.length) {
      requestData.sample_ids = sampleIds.join(',');
    } else if (filters) {
      if (filters.search) requestData.search = filters.search;
      if (filters.strain_id) requestData.strain_id = filters.strain_id;
      if (filters.source_type) requestData.source_type = filters.source_type;
      if (filters.has_photo !== undefined) requestData.has_photo = filters.has_photo;
      if (filters.is_identified !== undefined) requestData.is_identified = filters.is_identified;
    }

    if (exportConfig) {
      if (exportConfig.format) requestData.format = exportConfig.format;
      if (Array.isArray(exportConfig.fields) && exportConfig.fields.length) {
        requestData.fields = exportConfig.fields.join(',');
      }
      if (exportConfig.includeRelated !== undefined) {
        requestData.include_related = String(exportConfig.includeRelated);
      }
    }

    const response = await api.post('/samples/export/', requestData, { responseType: 'blob' });
    return response.data;
  },

  // Массовые операции со штаммами
  async bulkDeleteStrains(strainIds: number[], forceDelete: boolean = false): Promise<{ message: string; deleted_count: number; deleted_strains: Strain[] }> {
    const response = await api.post('/strains/bulk-delete/', { 
      strain_ids: strainIds, 
      force_delete: forceDelete 
    });
    return response.data;
  },

  async bulkUpdateStrains(strainIds: number[], updateData: Partial<Strain>): Promise<{ message: string; updated_count: number; updated_fields: string[] }> {
    const response = await api.post('/strains/bulk-update/', { 
      strain_ids: strainIds, 
      update_data: updateData 
    });
    return response.data;
  },

  async exportStrains(filters?: StrainFilters, strainIds?: number[], exportConfig?: Record<string, unknown>): Promise<Blob> {
    const requestData: Record<string, unknown> = {};
    
    if (strainIds?.length) {
      requestData.strain_ids = strainIds.join(',');
    } else if (filters) {
      // Добавляем фильтры для экспорта
      if (filters.search) requestData.search = filters.search;
      if (filters.rcam_id) requestData.rcam_id = filters.rcam_id;
      if (filters.taxonomy) requestData.taxonomy = filters.taxonomy;
      if (filters.short_code) requestData.short_code = filters.short_code;
      if (filters.identifier) requestData.identifier = filters.identifier;
    }
    
    // Добавляем параметры экспорта
    if (exportConfig) {
      if (exportConfig.format) requestData.format = exportConfig.format;
      if (Array.isArray(exportConfig.fields) && exportConfig.fields.length) {
        requestData.fields = exportConfig.fields.join(',');
      }
      if (exportConfig.includeRelated !== undefined) {
        requestData.include_related = String(exportConfig.includeRelated);
      }
    }
    
    // Используем POST вместо GET для избежания проблем с URL параметрами
    const response = await api.post('/strains/export/', requestData, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Хранилища
  getStorage: async (): Promise<StorageListResponse> => {
    const response = await fetch(`${API_BASE_URL}/storage/`);
    if (!response.ok) {
      throw new Error('Failed to fetch storage data');
    }
    return response.json();
  },

  // Новые функции для оптимизированной загрузки
  getStorageSummary: async (): Promise<StorageListResponse> => {
    const response = await fetch(`${API_BASE_URL}/storage/summary/`);
    if (!response.ok) {
      throw new Error('Failed to fetch storage summary');
    }
    return response.json();
  },

  getBoxDetails: async (boxId: string): Promise<{
    box_id: string;
    cells: Array<{
      cell_id: string;
      storage_id: number;
      occupied: boolean;
      sample_id?: number;
      strain_code?: string;
      is_free_cell?: boolean;
    }>;
    total: number;
    occupied: number;
  }> => {
    const response = await fetch(`${API_BASE_URL}/storage/box/${boxId}/`);
    if (!response.ok) {
      throw new Error(`Failed to fetch box ${boxId} details`);
    }
    return response.json();
  },
};

export default apiService; 