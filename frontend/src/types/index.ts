// Основные типы данных для системы учета штаммов микроорганизмов

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
  organism_name: string;
  source_type: string;
  category: string;
}

export interface Comment {
  id: number;
  text: string;
}

export interface AppendixNote {
  id: number;
  text: string;
}

export interface Storage {
  id: number;
  box_id: string;
  cell_id: string;
  occupied: boolean;
  sample_id?: number;
  strain_code?: string;
  is_free_cell?: boolean;
}

export interface Strain {
  id: number;
  short_code: string;
  identifier: string;
  rrna_taxonomy?: string;
  name_alt?: string;
  rcam_collection_id?: string;
  created_at?: string;
  updated_at?: string;
  samples_stats?: {
    total_count: number;
    with_photo_count: number;
    identified_count: number;
    with_genome_count: number;
    with_biochemistry_count: number;
    photo_percentage: number;
    identified_percentage: number;
  };
}

export interface Sample {
  id: number;
  strain?: {
    id: number;
    short_code: string;
    identifier: string;
    rrna_taxonomy?: string;
  };
  storage?: {
    id: number;
    box_id: string;
    cell_id: string;
  };
  source?: {
    id: number;
    organism_name: string;
    source_type: string;
    category: string;
  };
  location?: {
    id: number;
    name: string;
  };
  index_letter?: {
    id: number;
    letter_value: string;
  };
  appendix_note?: {
    id: number;
    text: string;
  };
  comment?: {
    id: number;
    text: string;
  };
  original_sample_number?: string;
  has_photo: boolean;
  is_identified: boolean;
  has_antibiotic_activity: boolean;
  has_genome: boolean;
  has_biochemistry: boolean;
  seq_status: boolean;
  created_at?: string;
  updated_at?: string;
}

// API Response типы
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface StatsResponse {
  counts: {
    strains: number;
    samples: number;
    storage_units: number;
    sources: number;
    locations: number;
    index_letters: number;
    comments: number;
    appendix_notes: number;
  };
  samples_analysis: {
    with_photo: number;
    identified: number;
    with_antibiotic_activity: number;
    with_genome: number;
    with_biochemistry: number;
    sequenced: number;
  };
  validation: {
    engine: string;
    schemas_available: string[];
  };
}

export interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
  input: any;
  ctx?: any;
  url?: string;
}

export interface ValidationResponse {
  valid: boolean;
  data?: any;
  errors?: ValidationError[];
  message: string;
}

// Фильтры для поиска
export interface StrainFilters {
  search?: string;
  rcam_id?: string;
  taxonomy?: string;
  short_code?: string;
  identifier?: string;
  created_after?: string;
  created_before?: string;
  limit?: number;
  page?: number;
}

export interface SampleFilters {
  strain_id?: number;
  search?: string;
  has_photo?: boolean;
  is_identified?: boolean;
  has_antibiotic_activity?: boolean;
  has_genome?: boolean;
  has_biochemistry?: boolean;
  seq_status?: boolean;
  box_id?: string;
  source_id?: number;
  location_id?: number;
  source_type?: string;
  organism_name?: string;
  created_after?: string;
  created_before?: string;
  limit?: number;
  page?: number;
}

// UI типы
export interface TableColumn<T> {
  id: keyof T;
  header: string;
  cell?: (item: T) => React.ReactNode;
  sortable?: boolean;
}

export interface StorageBox {
  box_id: string;
  cells: Storage[];
  occupied: number;
  total: number;
}

// Справочные данные для форм
export interface ReferenceStrain {
  id: number;
  short_code: string;
  identifier: string;
  display_name: string;
}

export interface ReferenceSource {
  id: number;
  organism_name: string;
  source_type: string;
  category: string;
  display_name: string;
}

export interface ReferenceLocation {
  id: number;
  name: string;
}

export interface ReferenceIndexLetter {
  id: number;
  letter_value: string;
}

export interface ReferenceStorage {
  id: number;
  box_id: string;
  cell_id: string;
  display_name: string;
}

export interface ReferenceComment {
  id: number;
  text: string;
}

export interface ReferenceAppendixNote {
  id: number;
  text: string;
}

export interface ReferenceData {
  strains: ReferenceStrain[];
  sources: ReferenceSource[];
  locations: ReferenceLocation[];
  index_letters: ReferenceIndexLetter[];
  free_storage: ReferenceStorage[];
  comments: ReferenceComment[];
  appendix_notes: ReferenceAppendixNote[];
}

// Формы для создания и редактирования
export interface CreateSampleData {
  strain_id?: number;
  index_letter_id?: number;
  storage_id?: number;
  original_sample_number?: string;
  source_id?: number;
  location_id?: number;
  appendix_note_id?: number;
  comment_id?: number;
  has_photo: boolean;
  is_identified: boolean;
  has_antibiotic_activity: boolean;
  has_genome: boolean;
  has_biochemistry: boolean;
  seq_status: boolean;
}

export interface UpdateSampleData {
  strain_id?: number;
  index_letter_id?: number;
  storage_id?: number;
  original_sample_number?: string;
  source_id?: number;
  location_id?: number;
  appendix_note_id?: number;
  comment_id?: number;
  has_photo?: boolean;
  is_identified?: boolean;
  has_antibiotic_activity?: boolean;
  has_genome?: boolean;
  has_biochemistry?: boolean;
  seq_status?: boolean;
}

// Ответы API
export interface PaginationInfo {
  total: number;
  shown: number;
  page: number;
  limit: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
  offset: number;
}

export interface SamplesListResponse {
  samples: Sample[];
  pagination: PaginationInfo;
  search_query?: string;
  filters_applied?: any;
}

export interface StrainsListResponse {
  strains: Strain[];
  pagination: PaginationInfo;
  search_query?: string;
  filters_applied?: any;
}

export interface StorageListResponse {
  boxes: StorageBox[];
  total_boxes: number;
  total_cells: number;
  occupied_cells: number;
} 