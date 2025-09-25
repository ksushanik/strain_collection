import type { BaseFilters } from '../../../shared/types';
import type { Sample } from '../../../types';

// Реэкспорт типа Sample для использования в других модулях
export type { Sample };

export interface SampleFilters extends BaseFilters {
  strain_id?: number;
  storage_id?: number;
  box_id?: string;
  cell_id?: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  strain_code?: string;
  sort_by?: string;
  sort_direction?: 'asc' | 'desc';
}

export interface SamplesListResponse {
  samples: Sample[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  sort_by?: string;
  sort_direction?: 'asc' | 'desc';
}

export interface CreateSampleData {
  strain_id: number;
  box_id: string;
  cell_id: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
}

export interface UpdateSampleData extends Partial<CreateSampleData> {
  id: number;
}

// Дополнительные типы для IUK Color и Amylase Variant
export interface IUKColor {
  id: number;
  name: string;
  description?: string;
}

export interface AmylaseVariant {
  id: number;
  name: string;
  description?: string;
}