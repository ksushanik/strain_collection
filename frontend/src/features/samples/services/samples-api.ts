import { BaseApiClient } from '../../../shared/services/base-api';
import type { 
  Sample, 
  SampleFilters, 
  SamplesListResponse, 
  CreateSampleData, 
  UpdateSampleData,
  IUKColor,
  AmylaseVariant
} from '../types';
import type { ValidationResponse } from '../../../shared/types';

export class SamplesApiClient extends BaseApiClient {
  private readonly endpoint = '/samples';

  async getSamples(filters?: SampleFilters): Promise<SamplesListResponse> {
    console.log('samplesApi.getSamples: called with filters:', filters);
    const queryParams = filters ? this.buildQueryParams(filters) : '';
    const url = queryParams ? `${this.endpoint}/?${queryParams}` : `${this.endpoint}/`;
    console.log('samplesApi.getSamples: final URL:', url);
    const result = await this.get<SamplesListResponse>(url);
    console.log('samplesApi.getSamples: API result:', result);
    return result;
  }

  async getSample(id: number): Promise<Sample> {
    return this.get<Sample>(`${this.endpoint}/${id}/`);
  }

  async createSample(data: CreateSampleData): Promise<Sample> {
    return this.post<Sample>(`${this.endpoint}/`, data);
  }

  async updateSample(id: number, data: UpdateSampleData): Promise<Sample> {
    return this.patch<Sample>(`${this.endpoint}/${id}/`, data);
  }

  // Полное обновление образца
  async replaceSample(id: number, data: CreateSampleData): Promise<Sample> {
    return this.put<Sample>(`${this.endpoint}/${id}/`, data);
  }

  async deleteSample(id: number): Promise<void> {
    return this.delete<void>(`${this.endpoint}/${id}/`);
  }

  async validateSample(data: CreateSampleData | UpdateSampleData): Promise<ValidationResponse> {
    return this.post<ValidationResponse>(`${this.endpoint}/validate/`, data);
  }

  // Массовое удаление образцов
  async bulkDelete(ids: number[]): Promise<{ deleted_count: number }> {
    return this.post<{ deleted_count: number }>(`${this.endpoint}/bulk-delete/`, { ids });
  }

  // Поиск образцов для автокомплита
  async searchSamples(query: string, limit: number = 10): Promise<Sample[]> {
    const queryParams = this.buildQueryParams({ search: query, limit });
    return this.get<Sample[]>(`${this.endpoint}/search/?${queryParams}`);
  }

  // Получение статистики по образцам
  async getSamplesStats(): Promise<{
    total: number;
    by_strain: Record<string, number>;
    by_iuk_color: Record<string, number>;
    by_amylase_variant: Record<string, number>;
    recent_additions: number;
  }> {
    return this.get(`${this.endpoint}/stats/`);
  }

  async exportSamples(filters?: SampleFilters): Promise<Blob> {
    const queryParams = filters ? this.buildQueryParams(filters) : '';
    const url = queryParams ? `${this.endpoint}/export/?${queryParams}` : `${this.endpoint}/export/`;
    
    const response = await this.api.get(url, {
      responseType: 'blob',
    });
    
    return response.data;
  }

  // Методы для справочных данных
  async getIUKColors(): Promise<IUKColor[]> {
    return this.get<IUKColor[]>('/reference-data/iuk-colors/');
  }

  async getAmylaseVariants(): Promise<AmylaseVariant[]> {
    return this.get<AmylaseVariant[]>('/reference-data/amylase-variants/');
  }
}

// Экспортируем экземпляр для использования
export const samplesApi = new SamplesApiClient();