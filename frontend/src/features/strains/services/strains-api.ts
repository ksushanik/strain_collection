import { BaseApiClient } from '../../../shared/services/base-api';
import type { 
  Strain, 
  StrainFilters, 
  StrainsListResponse, 
  CreateStrainData, 
  UpdateStrainData 
} from '../types';
import type { ValidationResponse } from '../../../shared/types';

export class StrainsApiClient extends BaseApiClient {
  private readonly endpoint = '/strains';

  async getStrains(filters?: StrainFilters): Promise<StrainsListResponse> {
    const defaultFilters = { page: 1, page_size: 20 };
    const finalFilters = { ...defaultFilters, ...filters };
    const queryParams = this.buildQueryParams(finalFilters);
    const url = `${this.endpoint}/?${queryParams}`;
    return this.get<StrainsListResponse>(url);
  }

  async getStrain(id: number): Promise<Strain> {
    return this.get<Strain>(`${this.endpoint}/${id}/`);
  }

  async createStrain(data: CreateStrainData): Promise<Strain> {
    return this.post<Strain>(`${this.endpoint}/`, data);
  }

  async updateStrain(id: number, data: UpdateStrainData): Promise<Strain> {
    return this.patch<Strain>(`${this.endpoint}/${id}/`, data);
  }

  // Полное обновление штамма
  async replaceStrain(id: number, data: CreateStrainData): Promise<Strain> {
    return this.put<Strain>(`${this.endpoint}/${id}/`, data);
  }

  async deleteStrain(id: number): Promise<void> {
    return this.delete<void>(`${this.endpoint}/${id}/`);
  }

  async validateStrain(data: CreateStrainData | UpdateStrainData): Promise<ValidationResponse> {
    return this.post<ValidationResponse>(`${this.endpoint}/validate/`, data);
  }

  // Массовое удаление штаммов
  async bulkDelete(ids: number[]): Promise<{ deleted_count: number }> {
    return this.post<{ deleted_count: number }>(`${this.endpoint}/bulk-delete/`, { ids });
  }

  // Поиск штаммов для автокомплита
  async searchStrains(query: string, limit: number = 10): Promise<Strain[]> {
    const queryParams = this.buildQueryParams({ search: query, limit });
    return this.get<Strain[]>(`${this.endpoint}/search/?${queryParams}`);
  }

  // Получение статистики по штаммам
  async getStrainsStats(): Promise<{
    total: number;
    by_species: Record<string, number>;
    by_source: Record<string, number>;
    recent_additions: number;
  }> {
    return this.get(`${this.endpoint}/stats/`);
  }

  async exportStrains(filters?: StrainFilters): Promise<Blob> {
    const queryParams = filters ? this.buildQueryParams(filters) : '';
    const url = queryParams ? `${this.endpoint}/export/?${queryParams}` : `${this.endpoint}/export/`;
    
    return this.get<Blob>(url, {
      responseType: 'blob',
    });
  }
}

// Экспортируем экземпляр для использования
export const strainsApi = new StrainsApiClient();