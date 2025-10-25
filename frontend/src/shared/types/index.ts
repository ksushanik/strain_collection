// Общие типы для всего приложения

export interface PaginationInfo {
  page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
  total: number;
  shown: number;
  limit: number;
  offset: number;
}

export interface BaseFilters {
  page?: number;
  limit?: number;
  search?: string;
}

export interface ApiResponse<T> {
  data: T;
  pagination?: PaginationInfo;
  message?: string;
}

export interface ValidationResponse {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface StatsResponse {
  total_strains: number;
  total_samples: number;
  total_storage_cells: number;
  occupied_cells: number;
  free_cells: number;
  recent_additions: {
    strains: number;
    samples: number;
  };
}

// Справочные данные
export interface IndexLetter {
  id: number;
  letter_value: string;
}

export interface Location {
  id: number;
  name: string;
}

export interface Source {
  id: number;
  name: string;
  organism_name?: string;
  source_type?: string;
  category?: string;
}

export interface Comment {
  id: number;
  text: string;
}

export interface AppendixNote {
  id: number;
  text: string;
}

export interface ReferenceData {
  index_letters: IndexLetter[];
  locations: Location[];
  sources: Source[];
  comments: Comment[];
  appendix_notes: AppendixNote[];
}

// Фильтры для расширенного поиска
export interface FilterGroup {
  id: string;
  field: string;
  operator: string;
  value: string;
  logic?: 'AND' | 'OR';
}

export interface AdvancedFilters {
  groups: FilterGroup[];
}

// Экспорт типов ошибок API
export * from './api-errors';
