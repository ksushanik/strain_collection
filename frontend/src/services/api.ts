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
  StorageListResponse,
  CreateBoxData,
  UpdateBoxData,
  BoxDetailsResponse,
  BoxDetailResponse,
  DeleteBoxResponse,
  CellAssignment,
  AssignCellResponse,
  ClearCellResponse,
  BulkAssignResponse,
  StorageSummaryResponse,
  StorageBoxSummary,
  SampleCharacteristic,
  StorageBox
} from '../types';
import { API_BASE_URL } from '../config/api';

const apiBaseUrl = `${API_BASE_URL}/api`;

// Функция для получения CSRF токена из cookies
const getCSRFToken = (): string | undefined => {
  const name = 'csrftoken=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return undefined;
};

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Включаем отправку credentials (cookies)
});

// Добавляем request interceptor для CSRF токена
api.interceptors.request.use(
  (config) => {
    // Для unsafe методов добавляем CSRF токен
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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

  async getAnalytics(): Promise<any> {
    const response = await api.get('/analytics/');
    return response.data;
  },

  // Справочные данные
  async getReferenceData(): Promise<ReferenceData> {
    const response = await api.get('/reference-data/');
    return response.data;
  },

  // Получение типов источников
  async getSourceTypes(): Promise<{ source_types: { value: string; label: string }[] }> {
    const response = await api.get('/reference-data/source-types/');
    return response.data;
  },

  // Получение названий организмов
  async getOrganismNames(): Promise<{ organism_names: { value: string; label: string }[] }> {
    const response = await api.get('/reference-data/organism-names/');
    return response.data;
  },

  // Работа с боксами
  async createBox(data: CreateBoxData): Promise<{ message: string; box: any }> {
    const response = await api.post('/storage/boxes/create/', data);
    return response.data;
  },

  async getBoxes(search?: string): Promise<StorageListResponse> {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await api.get(`/storage/${query}`);
    return response.data;
  },

  async getBox(boxId: string): Promise<BoxDetailsResponse> {
    const response = await api.get(`/storage/boxes/${boxId}/`);
    return response.data;
  },

  async updateBox(boxId: string, data: UpdateBoxData): Promise<{ message: string; box: any }> {
    const response = await api.put(`/storage/boxes/${boxId}/update/`, data);
    return response.data;
  },

  async deleteBox(boxId: string, force: boolean = false): Promise<DeleteBoxResponse> {
    const url = force
      ? `/storage/boxes/${boxId}/delete/?force=true`
      : `/storage/boxes/${boxId}/delete/`;
    const response = await api.delete(url);
    return response.data;
  },

  async getBoxDetails(boxId: string): Promise<BoxDetailsResponse> {
    const response = await api.get(`/storage/boxes/${boxId}/`);
    return response.data;
  },

  async getBoxDetail(boxId: string): Promise<BoxDetailResponse> {
    const response = await api.get(`/storage/boxes/${boxId}/detail/`);
    return response.data;
  },

  // Операции с ячейками
  async assignCell(sampleId: number, boxId: string, cellId: string): Promise<AssignCellResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/${cellId}/assign/`, {
      sample_id: sampleId,
    });
    return response.data;
  },

  async clearCell(boxId: string, cellId: string): Promise<ClearCellResponse> {
    const response = await api.delete(`/storage/boxes/${boxId}/cells/${cellId}/clear/`);
    return response.data;
  },

  async bulkAssignCells(boxId: string, assignments: CellAssignment[]): Promise<BulkAssignResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/bulk-assign/`, {
      assignments
    });
    return response.data;
  },

  async bulkAllocateCells(boxId: string, assignments: CellAssignment[]): Promise<BulkAssignResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/bulk-allocate/`, {
      assignments
    });
    return response.data;
  },

  async getBoxCells(boxId: string, search?: string): Promise<{ box_id: string; cells: any[] }> {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await api.get(`/storage/boxes/${boxId}/cells/${params}`);
    return response.data;
  },


  // Штаммы
  async getStrains(filters?: StrainFilters): Promise<StrainsListResponse> {
    const params = new URLSearchParams();
    
    // Добавляем все параметры из filters (включая расширенные операторы)
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (typeof value === 'boolean') {
            params.append(key, value.toString());
          } else if (typeof value === 'number') {
            params.append(key, value.toString());
          } else if (typeof value === 'string') {
            params.append(key, value);
          }
        }
      });
    }
    
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

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (typeof value === 'boolean') {
            params.append(key, value.toString());
          } else if (typeof value === 'number') {
            params.append(key, value.toString());
          } else if (typeof value === 'string') {
            params.append(key, value);
          }
        }
      });
    }

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

  async bulkUpdateSamples(sampleIds: number[], updateData: Record<string, unknown>): Promise<{ message: string; updated_count: number; updated_fields: string[] }> {
    const response = await api.post('/samples/bulk-update/', { 
      sample_ids: sampleIds, 
      update_data: updateData 
    });
    return response.data;
  },

  async exportSamples(filters?: SampleFilters, sampleIds?: number[], exportConfig?: any): Promise<Blob> {
    const requestData: any = {};

    if (sampleIds?.length) {
      requestData.sample_ids = sampleIds.join(',');
    } else if (filters) {
      if (filters.search) requestData.search = filters.search;
      if (filters.strain_id) requestData.strain_id = filters.strain_id;
      if (filters.source_type) requestData.source_type = filters.source_type;
      if (filters.has_photo !== undefined) requestData.has_photo = filters.has_photo;
    }

    if (exportConfig) {
      if (exportConfig.format) requestData.format = exportConfig.format;
      if (exportConfig.fields?.length) requestData.fields = exportConfig.fields.join(',');
      if (exportConfig.includeRelated !== undefined) requestData.include_related = exportConfig.includeRelated.toString();
    }

    const response = await api.post('/samples/export/', requestData, { responseType: 'blob' });
    return response.data;
  },

  // Массовые операции со штаммами
  async bulkDeleteStrains(strainIds: number[], forceDelete: boolean = false): Promise<{ message: string; deleted_count: number; deleted_strains: any[] }> {
    const response = await api.post('/strains/bulk-delete/', { 
      strain_ids: strainIds, 
      force_delete: forceDelete 
    });
    return response.data;
  },

  async bulkUpdateStrains(strainIds: number[], updateData: Record<string, unknown>): Promise<{ message: string; updated_count: number; updated_fields: string[] }> {
    const response = await api.post('/strains/bulk-update/', { 
      strain_ids: strainIds, 
      update_data: updateData 
    });
    return response.data;
  },

  async exportStrains(filters?: StrainFilters, strainIds?: number[], exportConfig?: any): Promise<Blob> {
    const requestData: any = {};
    
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
      if (exportConfig.fields?.length) requestData.fields = exportConfig.fields.join(',');
      if (exportConfig.includeRelated !== undefined) requestData.include_related = exportConfig.includeRelated.toString();
    }
    
    // Используем POST вместо GET для избежания проблем с URL параметрами
    const response = await api.post('/strains/export/', requestData, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Хранилища
  getStorage: async (): Promise<StorageListResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/storage/`);
    if (!response.ok) {
      throw new Error('Failed to fetch storage data');
    }
    return response.json();
  },

  // Новые функции для оптимизированной загрузки
  getStorageSummary: async (): Promise<StorageSummaryResponse> => {
    const response = await api.get('/storage/summary/');
    return response.data;
  },

  // Методы для работы с боксами и ячейками
  async getFreeBoxes(
    search?: string,
    limit?: number,
  ): Promise<{ boxes: StorageBoxSummary[] }> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (limit) params.append('limit', limit.toString());

    const queryString = params.toString();
    const boxesUrl = queryString ? `/storage/boxes/?${queryString}` : '/storage/boxes/';

    const [boxesResponse, summaryResponse] = await Promise.all([
      api.get(boxesUrl),
      api.get('/storage/summary/'),
    ]);

    // Карта метаданных боксов (rows, cols, description) из /storage/boxes/
    type BoxMeta = Pick<StorageBox, 'box_id' | 'rows' | 'cols' | 'description'>;
    const metaMap: Map<string, BoxMeta> = new Map(
      ((boxesResponse.data.results ?? boxesResponse.data.boxes ?? []) as BoxMeta[]).map(
        (box) => [box.box_id, box],
      ),
    );

    // Берем список боксов из summary как источник истины, чтобы не терять боксы
    // без записей в StorageBox, но имеющие ячейки в Storage
    let summaryBoxes: Array<{ box_id: string; occupied: number; total: number; free_cells: number }> =
      summaryResponse.data.boxes ?? [];

    // Локальная фильтрация по поиску (endpoint summary не поддерживает search)
    if (search) {
      const s = search.toLowerCase();
      summaryBoxes = summaryBoxes.filter((b) => b.box_id.toLowerCase().includes(s));
    }

    // Локальное ограничение количества
    if (limit) {
      summaryBoxes = summaryBoxes.slice(0, limit);
    }

    const boxes: StorageBoxSummary[] = summaryBoxes.map((item) => {
      const meta = metaMap.get(item.box_id);
      const rows = meta?.rows ?? null;
      const cols = meta?.cols ?? null;
      const totalFromSummary = item.total;
      const totalFromSize = rows !== null && cols !== null ? rows * cols : undefined;
      const totalCells = totalFromSummary ?? totalFromSize ?? 0;
      const occupiedCells = item.occupied ?? 0;
      const freeCells = item.free_cells ?? Math.max(totalCells - occupiedCells, 0);

      return {
        box_id: item.box_id,
        rows: meta?.rows,
        cols: meta?.cols,
        description: meta?.description,
        total_cells: totalCells,
        occupied_cells: occupiedCells,
        free_cells: freeCells,
      };
    });

    return { boxes };
  },

  async getFreeCells(boxId: string): Promise<{ cells: { id: number; cell_id: string; display_name?: string }[] }> {
    // Используем существующий эндпоинт для получения всех ячеек в боксе
    const response = await api.get(`/storage/boxes/${boxId}/cells/`);
    return response.data;
  },

  // ------------------  Фотографии образцов  ------------------ //

  async uploadSamplePhotos(sampleId: number, files: File[]): Promise<{ created: any[]; errors: string[] }> {
    const formData = new FormData();
    files.forEach(f => formData.append('photos', f));
    const response = await api.post(`/samples/${sampleId}/photos/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async deleteSamplePhoto(sampleId: number, photoId: number): Promise<{ message: string }> {
    const response = await api.delete(`/samples/${sampleId}/photos/${photoId}/delete/`);
    return response.data;
  },

  // ------------------  Характеристики образцов  ------------------ //

  async getCharacteristics(): Promise<SampleCharacteristic[]> {
    const response = await api.get('/samples/characteristics/');
    return response.data;
  },

  async createCharacteristic(data: Partial<SampleCharacteristic>): Promise<SampleCharacteristic> {
    const response = await api.post('/samples/characteristics/create/', data);
    return response.data;
  },

  async updateCharacteristic(id: number, data: Partial<SampleCharacteristic>): Promise<SampleCharacteristic> {
    const response = await api.put(`/samples/characteristics/${id}/update/`, data);
    return response.data;
  },

  async deleteCharacteristic(id: number): Promise<{ message: string }> {
    const response = await api.delete(`/samples/characteristics/${id}/delete/`);
    return response.data;
  },

  // ------------------  Среды роста  ------------------ //

  async getGrowthMedia(): Promise<any[]> {
    const response = await api.get('/reference-data/growth-media/');
    return response.data;
  },

  async createGrowthMedium(data: { name: string; description?: string }): Promise<any> {
    const response = await api.post('/reference-data/growth-media/', data);
    return response.data;
  },

  async updateGrowthMedium(id: number, data: { name: string; description?: string }): Promise<any> {
    const response = await api.put(`/reference-data/growth-media/${id}/`, data);
    return response.data;
  },

  async deleteGrowthMedium(id: number): Promise<{ message: string }> {
    const response = await api.delete(`/reference-data/growth-media/${id}/`);
    return response.data;
  },

};

export default apiService;
