import type { BaseFilters, PaginationInfo } from '../../../shared/types';

export interface Strain {
  id: number;
  short_code: string;
  identifier: string;
  rrna_taxonomy?: string;
  name_alt?: string;
  rcam_collection_id?: string;
  created_at?: string;
  updated_at?: string;
  index_letter_id?: number;
  location_id?: number;
  source_id?: number;
  comment_id?: number;
  appendix_note_id?: number;
  
  // Связанные данные
  index_letter?: {
    id: number;
    letter_value: string;
  };
  location?: {
    id: number;
    name: string;
  };
  source?: {
    id: number;
    organism_name: string;
    source_type: string;
    category: string;
  };
  comment?: {
    id: number;
    text: string;
  };
  appendix_note?: {
    id: number;
    text: string;
  };
}

export interface StrainFilters extends BaseFilters {
  index_letter_id?: number;
  location_id?: number;
  source_id?: number;
  comment_id?: number;
  appendix_note_id?: number;
  rrna_taxonomy?: string;
  name_alt?: string;
  rcam_collection_id?: string;
}

export interface StrainsListResponse {
  results: Strain[];
  pagination: PaginationInfo;
}

export interface CreateStrainData {
  short_code: string;
  identifier: string;
  rrna_taxonomy?: string;
  name_alt?: string;
  rcam_collection_id?: string;
  index_letter_id?: number;
  location_id?: number;
  source_id?: number;
  comment_id?: number;
  appendix_note_id?: number;
}

export interface UpdateStrainData extends Partial<CreateStrainData> {
  id: number;
}