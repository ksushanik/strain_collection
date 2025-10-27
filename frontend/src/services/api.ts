import axios from 'axios';
import type { 
  StatsResponse,
  StrainFilters,
  Strain,
  StrainsListResponse,
  SampleFilters,
  Sample,
  SamplesListResponse,
  CreateSampleData,
  UpdateSampleData,
  StorageListResponse,
  CreateBoxData,
  UpdateBoxData,
  DeleteBoxResponse,
  BoxDetailResponse,
  BoxDetailsResponse,
  StorageSummaryResponse,
  StorageBoxSummary,
  SampleCharacteristic,
  SampleAllocationsResponse,
  StorageBox,
  AnalyticsResponse,
  GrowthMedium,
  UploadSamplePhotosResponse,
  ReferenceData,
  CellAssignment,
  AssignCellResponse,
  BulkAssignResponse,
  ClearCellResponse
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

const buildQueryParams = (params: Record<string, unknown>): string => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((entry) => {
        if (entry !== undefined && entry !== null) {
          query.append(key, String(entry));
        }
      });
      return;
    }
    query.append(key, String(value));
  });
  return query.toString();
};

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

  async getAnalytics(): Promise<AnalyticsResponse> {
    const response = await api.get('/analytics/');
    return response.data;
  },
  async getReferenceData(): Promise<ReferenceData> {
    const response = await api.get('/reference-data/');
    return response.data;
  },

  async getSourceTypes(): Promise<{ source_types: { value: string; label: string }[] }> {
    const response = await api.get('/reference-data/source-types/');
    return response.data;
  },

  async getOrganismNames(): Promise<{ organism_names: { value: string; label: string }[] }> {
    const response = await api.get('/reference-data/organism-names/');
    return response.data;
  },

  async getStrains(filters?: StrainFilters): Promise<StrainsListResponse> {
    const query = filters ? buildQueryParams(filters as Record<string, unknown>) : '';
    const url = query ? '/strains/?' + query : '/strains/';
    const response = await api.get(url);
    return response.data;
  },

  async getStrain(strainId: number): Promise<Strain> {
    const response = await api.get('/strains/' + String(strainId) + '/');
    return response.data;
  },

  async createStrain(data: Partial<Strain>): Promise<Strain> {
    const response = await api.post('/strains/create/', data);
    return response.data;
  },

  async updateStrain(strainId: number, data: Partial<Strain>): Promise<Strain> {
    const response = await api.put('/strains/' + String(strainId) + '/update/', data);
    return response.data;
  },

  async deleteStrain(strainId: number): Promise<{ message: string }> {
    const response = await api.delete('/strains/' + String(strainId) + '/delete/');
    return response.data;
  },

  async getSamples(filters?: SampleFilters): Promise<SamplesListResponse> {
    const query = filters ? buildQueryParams(filters as Record<string, unknown>) : '';
    const url = query ? '/samples/?' + query : '/samples/';
    const response = await api.get(url);
    return response.data;
  },

  async getSample(sampleId: number): Promise<Sample> {
    const response = await api.get('/samples/' + String(sampleId) + '/');
    return response.data;
  },

  async createSample(data: CreateSampleData): Promise<Sample> {
    const response = await api.post('/samples/create/', data);
    return response.data;
  },

  async updateSample(sampleId: number, data: UpdateSampleData): Promise<Sample> {
    const response = await api.put('/samples/' + String(sampleId) + '/update/', data);
    return response.data;
  },

  async deleteSample(sampleId: number): Promise<{ message: string }> {
    const response = await api.delete('/samples/' + String(sampleId) + '/delete/');
    return response.data;
  },

  async bulkDeleteSamples(sampleIds: number[]): Promise<{ message: string; deleted_count: number; deleted_samples: Array<{ id: number }> ; batch_id: string }> {
    const response = await api.post('/samples/bulk-delete/', { sample_ids: sampleIds });
    return response.data;
  },

  async bulkUpdateSamples(sampleIds: number[], updateData: Record<string, unknown>): Promise<{ message: string; updated_count: number; updated_fields: string[]; batch_id: string }> {
    const response = await api.post('/samples/bulk-update/', {
      sample_ids: sampleIds,
      update_data: updateData,
    });
    return response.data;
  },

  async getSamplesByStrain(strainId: number, limit: number = 100): Promise<SamplesListResponse> {
    const query = buildQueryParams({ strain_id: strainId, limit });
    const response = await api.get('/samples/?' + query);
    return response.data;
  },

  async getSampleAllocations(sampleId: number): Promise<SampleAllocationsResponse> {
    const response = await api.get('/storage/samples/' + String(sampleId) + '/allocations/');
    return response.data;
  },

  // Работа с боксами
  async createBox(data: CreateBoxData): Promise<{ message: string; box: StorageBox }> {
    const response = await api.post('/storage/boxes/create/', data);
    return response.data;
  },

  async updateBox(boxId: string, data: UpdateBoxData): Promise<{ message: string; box: StorageBox }> {
    const response = await api.put(`/storage/boxes/${boxId}/update/`, data);
    return response.data;
  },

  async getBoxDetails(boxId: string): Promise<BoxDetailsResponse> {
    const response = await api.get(`/storage/boxes/${boxId}/`);
    return response.data as BoxDetailsResponse;
  },

  async deleteBox(boxId: string, force: boolean = false): Promise<DeleteBoxResponse> {
    const suffix = force ? '?force=true' : '';
    const response = await api.delete(`/storage/boxes/${boxId}/delete/${suffix}`);
    return response.data as DeleteBoxResponse;
  },

  async getBoxCells(boxId: string, search?: string): Promise<{ box_id: string; cells: { id: number; cell_id: string; display_name?: string }[] }> {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await api.get(`/storage/boxes/${boxId}/cells/${params}`);
    return response.data;
  },

  async exportSamples(filters?: SampleFilters, sampleIds?: number[], exportConfig?: { format?: 'csv' | 'xlsx' | 'json'; fields?: string[]; includeRelated?: boolean }): Promise<Blob> {
    const requestData: Record<string, string | number | boolean> = {};

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

  async bulkDeleteStrains(strainIds: number[], forceDelete: boolean = false): Promise<{ message: string; deleted_count: number; deleted_strains: { id: number; short_code: string; identifier: string }[] }> {
    const response = await api.post('/strains/bulk-delete/', { 
      strain_ids: strainIds, 
      force_delete: forceDelete 
    });
    return response.data;
  },

  async bulkUpdateStrains(strainIds: number[], updateData: Record<string, unknown>): Promise<{ message: string; updated_count: number; updated_fields: string[]; updated_data: Record<string, unknown>; batch_id: string }> {
    const response = await api.post('/strains/bulk-update/', {
      strain_ids: strainIds,
      update_data: updateData,
    });
    return response.data;
  },

  async exportStrains(filters?: StrainFilters, strainIds?: number[], exportConfig?: { format?: 'csv' | 'xlsx' | 'json'; fields?: string[]; includeRelated?: boolean }): Promise<Blob> {
    const requestData: Record<string, string | number | boolean> = {};
    
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

    const [boxesResponse, overviewResponse] = await Promise.all([
      api.get(boxesUrl),
      api.get('/storage/'),
    ]);

    type BoxMeta = Pick<StorageBox, 'box_id' | 'rows' | 'cols' | 'description'>;
    const metaMap: Map<string, BoxMeta> = new Map(
      ((boxesResponse.data.results ?? boxesResponse.data.boxes ?? []) as BoxMeta[]).map(
        (box) => [box.box_id, box],
      ),
    );

    type OverviewBox = {
      box_id: string;
      rows?: number | null;
      cols?: number | null;
      description?: string | null;
      total?: number | null;
      total_cells?: number | null;
      occupied?: number | null;
      occupied_cells?: number | null;
      free_cells?: number | null;
    };

    const overviewBoxes: OverviewBox[] = (overviewResponse.data?.boxes ?? []) as OverviewBox[];

    const coalesceNumber = (...values: Array<number | null | undefined>): number | undefined => {
      for (const value of values) {
        if (typeof value === 'number' && !Number.isNaN(value)) {
          return value;
        }
      }
      return undefined;
    };

    const filtered = overviewBoxes.filter((box) => {
      if (!search) return true;
      const term = search.toLowerCase();
      const matchesId = box.box_id.toLowerCase().includes(term);
      const meta = metaMap.get(box.box_id);
      const description = meta?.description ?? box.description ?? '';
      return matchesId || description.toLowerCase().includes(term);
    });

    const limited = limit ? filtered.slice(0, limit) : filtered;

    const boxes: StorageBoxSummary[] = limited.map((item) => {
      const meta = metaMap.get(item.box_id);
      const rows = coalesceNumber(meta?.rows ?? undefined, item.rows ?? undefined);
      const cols = coalesceNumber(meta?.cols ?? undefined, item.cols ?? undefined);
      const geometryTotal =
        rows !== undefined && cols !== undefined ? rows * cols : undefined;

      const totalCells =
        geometryTotal ??
        coalesceNumber(item.total_cells, item.total) ??
        0;

      const directFree = coalesceNumber(item.free_cells);
      let occupiedCells = coalesceNumber(item.occupied_cells, item.occupied);

      if (occupiedCells === undefined && directFree !== undefined) {
        occupiedCells = Math.max(totalCells - directFree, 0);
      }

      if (occupiedCells === undefined) {
        occupiedCells = 0;
      }

      const freeCells =
        directFree !== undefined ? directFree : Math.max(totalCells - occupiedCells, 0);

      return {
        box_id: item.box_id,
        rows: rows ?? undefined,
        cols: cols ?? undefined,
        description: meta?.description ?? item.description ?? undefined,
        total_cells: totalCells,
        occupied_cells: occupiedCells,
        free_cells: freeCells,
      };
    });

    return { boxes };
  },

  async getBoxes(): Promise<StorageListResponse> {
    // Получаем метаданные боксов и обзор хранилища
    const [boxesResponse, overviewResponse] = await Promise.all([
      api.get('/storage/boxes/'),
      api.get('/storage/'),
    ]);

    type BoxMeta = Pick<StorageBox, 'box_id' | 'rows' | 'cols' | 'description'>;
    const metaMap: Map<string, BoxMeta> = new Map(
      ((boxesResponse.data.results ?? boxesResponse.data.boxes ?? []) as BoxMeta[]).map(
        (box) => [box.box_id, box],
      ),
    );

    type OverviewBox = {
      box_id: string;
      rows?: number | null;
      cols?: number | null;
      description?: string | null;
      total?: number | null;
      total_cells?: number | null;
      occupied?: number | null;
      occupied_cells?: number | null;
      free_cells?: number | null;
    };

    const overviewBoxes: OverviewBox[] = (overviewResponse.data?.boxes ?? []) as OverviewBox[];

    const coalesceNumber = (...values: Array<number | null | undefined>): number | undefined => {
      for (const value of values) {
        if (typeof value === 'number' && !Number.isNaN(value)) {
          return value;
        }
      }
      return undefined;
    };

    const boxes: StorageBox[] = overviewBoxes.map((item) => {
      const meta = metaMap.get(item.box_id);
      const rows = coalesceNumber(meta?.rows ?? undefined, item.rows ?? undefined) ?? 0;
      const cols = coalesceNumber(meta?.cols ?? undefined, item.cols ?? undefined) ?? 0;
      const geometryTotal = rows * cols;

      const totalCells =
        coalesceNumber(item.total_cells, item.total, geometryTotal) ?? geometryTotal;

      const directFree = coalesceNumber(item.free_cells);
      let occupiedCells = coalesceNumber(item.occupied_cells, item.occupied);
      if (occupiedCells === undefined && directFree !== undefined) {
        occupiedCells = Math.max(totalCells - directFree, 0);
      }
      if (occupiedCells === undefined) {
        occupiedCells = 0;
      }
      const freeCells = directFree !== undefined ? directFree : Math.max(totalCells - occupiedCells, 0);

      return {
        box_id: item.box_id,
        rows,
        cols,
        description: meta?.description ?? item.description ?? undefined,
        occupied: occupiedCells,
        total: totalCells,
        total_cells: totalCells,
        free_cells: freeCells,
      } as StorageBox;
    });

    const total_boxes = boxes.length;
    const total_cells = boxes.reduce((sum, b) => sum + (b.total_cells ?? 0), 0);
    const occupied_cells = boxes.reduce((sum, b) => sum + (b.occupied ?? 0), 0);

    return {
      boxes,
      total_boxes,
      total_cells,
      occupied_cells,
    };
  },

  async getBoxDetail(boxId: string): Promise<BoxDetailResponse> {
    const response = await api.get(`/storage/boxes/${boxId}/detail/`);
    return response.data as BoxDetailResponse;
  },

  async getFreeCells(boxId: string): Promise<{ cells: { id: number; cell_id: string; display_name?: string }[] }> {
    // Используем существующий эндпоинт для получения всех ячеек в боксе
    const response = await api.get(`/storage/boxes/${boxId}/cells/`);
    return response.data;
  },

  async assignCell(sampleId: number, boxId: string, cellId: string): Promise<AssignCellResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/${cellId}/assign/`, {
      sample_id: sampleId,
    });
    return response.data as AssignCellResponse;
  },

  async bulkAssignCells(boxId: string, assignments: CellAssignment[]): Promise<BulkAssignResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/bulk-assign/`, {
      assignments,
    });
    return response.data as BulkAssignResponse;
  },
  async clearCell(boxId: string, cellId: string): Promise<ClearCellResponse> {
    const response = await api.delete('/storage/boxes/' + boxId + '/cells/' + cellId + '/clear/');
    return response.data;
  },

  async bulkAllocateCells(boxId: string, assignments: CellAssignment[]): Promise<BulkAssignResponse> {
    const response = await api.post('/storage/boxes/' + boxId + '/cells/bulk-allocate/', { assignments });
    return response.data;
  },


  // ------------------  Фотографии образцов  ------------------ //

  async uploadSamplePhotos(sampleId: number, files: File[]): Promise<UploadSamplePhotosResponse> {
    const formData = new FormData();
    files.forEach(f => formData.append('photos', f));
    const response = await api.post(`/samples/${sampleId}/photos/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as UploadSamplePhotosResponse;
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

  async getGrowthMedia(): Promise<GrowthMedium[]> {
    const response = await api.get('/reference-data/growth-media/');
    return response.data;
  },

  async createGrowthMedium(data: { name: string; description?: string }): Promise<GrowthMedium> {
    const response = await api.post('/reference-data/growth-media/', data);
    return response.data;
  },

  async updateGrowthMedium(id: number, data: { name: string; description?: string }): Promise<GrowthMedium> {
    const response = await api.put(`/reference-data/growth-media/${id}/`, data);
    return response.data;
  },

  async deleteGrowthMedium(id: number): Promise<{ message: string }> {
    const response = await api.delete(`/reference-data/growth-media/${id}/`);
    return response.data;
  },
  async createSource(data: { name: string }): Promise<{ id: number; name: string }> {
    const response = await api.post('/reference-data/sources/', data);
    return response.data;
  },

  async createLocation(data: { name: string }): Promise<{ id: number; name: string }> {
    const response = await api.post('/reference-data/locations/', data);
    return response.data;
  },

  async createIndexLetter(data: { letter_value: string }): Promise<{ id: number; letter_value: string }> {
    const response = await api.post('/reference-data/index-letters/', data);
    return response.data;
  },

};

export default apiService;
