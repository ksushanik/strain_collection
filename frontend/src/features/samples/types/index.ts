import type { BaseFilters, PaginationInfo } from '../../../shared/types';
import type { Sample } from '../../../types';

// Реэкспорт типа Sample для использования в других модулях
export type { Sample };

export interface SampleFilters extends BaseFilters {
  strain_id?: number;
  box_id?: string;
  cell_id?: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  strain_code?: string;
}

export interface SamplesListResponse {
  samples: Sample[];
  pagination: PaginationInfo;
  search_query: string;
  filters_applied: {
    search: boolean;
    strain_id: boolean;
    has_photo: boolean;
    is_identified: boolean;
    has_antibiotic_activity: boolean;
    has_genome: boolean;
    has_biochemistry: boolean;
    seq_status: boolean;
    box_id: boolean;
    source_id: boolean;
    location_id: boolean;
    date_range: boolean;
    mobilizes_phosphates: boolean;
    stains_medium: boolean;
    produces_siderophores: boolean;
    iuk_color_id: boolean;
    amylase_variant_id: boolean;
    growth_medium_id: boolean;
    advanced_filters: any[];
    total_filters: number;
  };
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