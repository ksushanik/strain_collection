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
  StorageCell,
  AnalyticsResponse,
  GrowthMedium,
  UploadSamplePhotosResponse,
  ReferenceData,
  CellAssignment,
  AllocateCellResponse,
  BulkAllocateResponse,
  UnallocateCellResponse
} from '../types';
import { API_BASE_URL } from '../config/api';
import { notifyEndpointDeprecated } from '../shared/api/deprecationTracker';

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

const extractHeader = (headers: Record<string, unknown> | undefined, name: string): string | undefined => {
  if (!headers) {
    return undefined;
  }

  const lowerName = name.toLowerCase();
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === lowerName);
  if (!entry) {
    return undefined;
  }

  const value = entry[1];
  if (Array.isArray(value)) {
    return value.length > 0 ? String(value[0]) : undefined;
  }

  if (value === undefined || value === null) {
    return undefined;
  }

  return String(value);
};

const handleDeprecatedHeaders = (headers: Record<string, unknown> | undefined): void => {
  const deprecatedFlag = extractHeader(headers, 'x-endpoint-deprecated');
  if (!deprecatedFlag || deprecatedFlag.toLowerCase() !== 'true') {
    return;
  }

  notifyEndpointDeprecated({
    endpoint: extractHeader(headers, 'x-endpoint-name'),
    message: extractHeader(headers, 'x-endpoint-deprecated-message'),
    replacement: extractHeader(headers, 'x-endpoint-replacement'),
  });
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
  (response) => {
    handleDeprecatedHeaders(response.headers as unknown as Record<string, unknown>);
    return response;
  },
  (error) => {
    handleDeprecatedHeaders(error?.response?.headers as Record<string, unknown> | undefined);
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

type RawStorageCell = {
  cell_id?: string | null;
  storage_id?: number | string | null;
  occupied?: boolean | null;
  sample_id?: number | string | null;
  strain_code?: string | null;
  is_free_cell?: boolean | null;
};

type RawStorageBox = {
  box_id?: string | null;
  rows?: number | string | null;
  cols?: number | string | null;
  description?: string | null;
  cells?: RawStorageCell[] | null;
  occupied?: number | string | null;
  occupied_cells?: number | string | null;
  total?: number | string | null;
  total_cells?: number | string | null;
  free_cells?: number | string | null;
};

type RawStorageOverview = {
  boxes?: RawStorageBox[] | null;
  total_boxes?: number | string | null;
  total_cells?: number | string | null;
  occupied_cells?: number | string | null;
  free_cells?: number | string | null;
} | null | undefined;

const toNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed.length > 0) {
      const parsed = Number(trimmed);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }
  return fallback;
};

const normalizeStorageCell = (boxId: string, raw: RawStorageCell | undefined | null): StorageCell => {
  const cell = raw ?? {};
  const cellId = (cell.cell_id ?? '').toString();
  const storageId = toNumber(cell.storage_id, 0);
  const occupied = Boolean(cell.occupied);
  const sampleId = cell.sample_id;
  return {
    id: Number.isFinite(storageId) ? storageId : 0,
    box_id: boxId,
    cell_id: cellId,
    occupied,
    sample_id: typeof sampleId === 'number' ? sampleId : (typeof sampleId === 'string' && sampleId.trim() ? Number(sampleId) : undefined),
    strain_code: cell.strain_code ?? undefined,
    is_free_cell: cell.is_free_cell ?? !occupied,
  };
};

const normalizeStorageBox = (raw: RawStorageBox | undefined | null): StorageBox => {
  const box = raw ?? {};
  const boxId = (box.box_id ?? '').toString().trim();
  const rows = toNumber(box.rows, 0);
  const cols = toNumber(box.cols, 0);
  const geometricalTotal = rows > 0 && cols > 0 ? rows * cols : undefined;
  const totalCells = toNumber(box.total_cells ?? box.total, geometricalTotal ?? 0);
  const occupiedCells = toNumber(box.occupied_cells ?? box.occupied, 0);
  const freeCells = toNumber(box.free_cells, Math.max(totalCells - occupiedCells, 0));
  const cells = Array.isArray(box.cells)
    ? box.cells.map((cell) => normalizeStorageCell(boxId, cell))
    : undefined;

  return {
    box_id: boxId,
    rows,
    cols,
    description: box.description ?? undefined,
    cells,
    occupied: occupiedCells,
    total: totalCells,
    total_cells: totalCells,
    free_cells: freeCells,
  };
};

const normalizeStorageOverview = (payload: RawStorageOverview): StorageListResponse => {
  const rawBoxes = Array.isArray(payload?.boxes) ? payload?.boxes ?? [] : [];
  const boxes = rawBoxes.map((box) => normalizeStorageBox(box));
  const fallbackTotalCells = boxes.reduce((sum, box) => sum + (box.total_cells ?? 0), 0);
  const fallbackOccupiedCells = boxes.reduce((sum, box) => sum + (box.occupied ?? 0), 0);
  const totalBoxes = toNumber(payload?.total_boxes, boxes.length);
  const totalCells = toNumber(payload?.total_cells, fallbackTotalCells);
  const occupiedCells = toNumber(payload?.occupied_cells, fallbackOccupiedCells);
  const freeCells = toNumber(payload?.free_cells, Math.max(totalCells - occupiedCells, 0));

  return {
    boxes,
    total_boxes: totalBoxes,
    total_cells: totalCells,
    occupied_cells: occupiedCells,
    free_cells: freeCells,
  };
};

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
    const response = await api.get('/storage/');
    const snapshot = normalizeStorageOverview(response.data as RawStorageOverview);
    const searchTerm = search?.trim().toLowerCase() ?? '';

    const filtered = snapshot.boxes
      .filter((box) => box.free_cells > 0)
      .filter((box) => {
        if (!searchTerm) {
          return true;
        }
        const haystack = `${box.box_id} ${box.description ?? ''}`.toLowerCase();
        return haystack.includes(searchTerm);
      })
      .sort((a, b) => b.free_cells - a.free_cells || a.box_id.localeCompare(b.box_id));

    const limited = typeof limit === 'number' ? filtered.slice(0, limit) : filtered;

    const boxes: StorageBoxSummary[] = limited.map((box) => ({
      box_id: box.box_id,
      rows: box.rows,
      cols: box.cols,
      description: box.description,
      total_cells: box.total_cells,
      occupied_cells: box.occupied,
      free_cells: box.free_cells,
    }));

    return { boxes };
  },

  async getBoxes(): Promise<StorageListResponse> {
    const response = await api.get('/storage/');
    return normalizeStorageOverview(response.data as RawStorageOverview);
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

  async allocateCell(
    boxId: string,
    cellId: string,
    payload: { sampleId: number; isPrimary?: boolean },
  ): Promise<AllocateCellResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/${cellId}/allocate/`, {
      sample_id: payload.sampleId,
      is_primary: payload.isPrimary ?? false,
    });
    return response.data as AllocateCellResponse;
  },

  async unallocateCell(
    boxId: string,
    cellId: string,
    sampleId: number,
  ): Promise<UnallocateCellResponse> {
    const response = await api.delete(`/storage/boxes/${boxId}/cells/${cellId}/unallocate/`, {
      data: { sample_id: sampleId },
    });
    return response.data as UnallocateCellResponse;
  },

  async bulkAllocateCells(boxId: string, assignments: CellAssignment[]): Promise<BulkAllocateResponse> {
    const response = await api.post(`/storage/boxes/${boxId}/cells/bulk-allocate/`, { assignments });
    return response.data as BulkAllocateResponse;
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
