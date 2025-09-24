import type { BaseFilters, PaginationInfo } from '../../../shared/types';

export interface Sample {
  id: number;
  strain_id: number;
  box_id: string;
  cell_id: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  created_at?: string;
  updated_at?: string;
  
  // Связанные данные
  strain?: {
    id: number;
    short_code: string;
    identifier: string;
    rrna_taxonomy?: string;
  };
  iuk_color?: {
    id: number;
    name: string;
    description?: string;
  };
  amylase_variant?: {
    id: number;
    name: string;
    description?: string;
  };
  storage_cell?: {
    id: number;
    box_id: string;
    cell_id: string;
    occupied: boolean;
  };
}

export interface SampleFilters extends BaseFilters {
  strain_id?: number;
  box_id?: string;
  cell_id?: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  strain_code?: string;
}

export interface SamplesListResponse {
  results: Sample[];
  pagination: PaginationInfo;
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