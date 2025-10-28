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

export interface StorageCell {
  id: number;
  box_id: string;
  cell_id: string;
  occupied: boolean;
  sample_id?: number;
  strain_code?: string;
  is_free_cell?: boolean;
}

// Для обратной совместимости
export type Storage = StorageCell;

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

export interface IUKColor {
  id: number;
  name: string;
  hex_code?: string;
}

export interface AmylaseVariant {
  id: number;
  name: string;
  description?: string;
}

export interface GrowthMedium {
  id: number;
  name: string;
  description?: string;
}

// Динамические характеристики образцов
export interface SampleCharacteristic {
  id: number;
  name: string;
  display_name: string;
  characteristic_type: 'boolean' | 'select' | 'text';
  description?: string;
  is_required: boolean;
  color: string;
  order: number;
  options?: SampleCharacteristicOption[];
}

export interface SampleCharacteristicOption {
  id: number;
  value: string;
  display_value: string;
  order: number;
}

export interface SampleCharacteristicValue {
  id: number;
  characteristic: SampleCharacteristic;
  boolean_value?: boolean;
  text_value?: string;
  select_value?: string;
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
  source?: Source | null;
  location?: {
    id: number;
    name: string;
  };
  index_letter?: {
    id: number;
    letter_value: string;
  };
  appendix_note?: string;
  comment?: string;
  original_sample_number?: string;
  has_photo: boolean;
  // Новые характеристики
  mobilizes_phosphates: boolean;
  stains_medium: boolean;
  produces_siderophores: boolean;
  iuk_color?: IUKColor;
  amylase_variant?: AmylaseVariant;
  growth_media: GrowthMedium[];
  // Динамические характеристики - поддерживаем оба формата
  characteristics?: SampleCharacteristicValue[] | { [key: string]: {
    characteristic_id: number;
    characteristic_name: string;
    characteristic_type: 'boolean' | 'select' | 'text';
    value: boolean | string | null;
  } };
  created_at?: string;
  updated_at?: string;
  photos?: SamplePhoto[];
}

// Фотографии образцов
export interface SamplePhoto {
  id: number;
  image: string;
  uploaded_at: string;
}

export interface SampleStorageAllocation {
  storage_id: number;
  box_id: string;
  cell_id: string;
  is_primary: boolean;
  allocated_at: string | null;
}

export interface SampleAllocationsResponse {
  sample_id: number;
  current_primary_storage_id: number | null;
  allocations: SampleStorageAllocation[];
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
    characteristics: { [key: string]: number };
    total_characteristics: number;
    unique_characteristics: number;
  };
  validation: {
    engine: string;
    schemas_available: string[];
  };
  // Storage information from unified endpoint
  storage: {
    boxes: Array<{
      box_id: string;
      occupied: number;
      total: number;
    }>;
    total_boxes: number;
    total_cells: number;
    occupied_cells: number;
    occupancy_percentage: number;
  };
}

export interface ValidationError {
  type: string;
  loc: string[];
  msg: string;
  input: unknown;
  ctx?: Record<string, unknown>;
  url?: string;
}

export interface ValidationResponse {
  valid: boolean;
  data?: unknown;
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
  rows?: number;
  cols?: number;
  description?: string;
  created_at?: string;
  cells?: StorageCell[];
  occupied: number;
  total: number;
  total_cells: number;
  free_cells: number;
  statistics?: {
    total_cells: number;
    occupied_cells: number;
    free_marked_cells: number;
    empty_cells: number;
    occupancy_percentage: number;
  };
}

// Новые типы для операций с боксами
export interface CreateBoxData {
  box_id?: string;
  rows: number;
  cols: number;
  description?: string;
}

export interface UpdateBoxData {
  description?: string;
}

export interface BoxDetailsResponse {
  box_id: string;
  rows: number;
  cols: number;
  description?: string;
  created_at?: string;
  cells: StorageCell[];
  statistics: {
    total_cells: number;
    occupied_cells: number;
    free_marked_cells: number;
    empty_cells: number;
    occupancy_percentage: number;
  };
}

export interface BoxDetailCell {
  row: number;
  col: number;
  cell_id: string;
  storage_id: number | null;
  is_occupied: boolean;
  sample_info?: {
    sample_id: number;
    strain_id: number;
    strain_number: string | null;
    comment: string | null;
    total_samples: number;
  } | null;
}

export interface BoxDetailResponse {
  box_id: string;
  rows: number;
  cols: number;
  description?: string;
  total_cells: number;
  occupied_cells: number;
  free_cells: number;
  occupancy_percentage: number;
  cells_grid: BoxDetailCell[][];
}

export interface DeleteBoxResponse {
  message: string;
  statistics: {
    cells_deleted: number;
    samples_freed: number;
    force_delete_used: boolean;
  };
}

// Типы для операций с ячейками
export interface CellAssignment {
  cell_id: string;
  sample_id: number;
}

export interface AllocateCellResponse {
  message: string;
  allocation: {
    sample_id: number;
    box_id: string;
    cell_id: string;
    storage_id: number;
    is_primary: boolean;
    created: boolean;
  };
}

export interface UnallocateCellResponse {
  message: string;
  unallocated: {
    sample_id: number;
    box_id: string;
    cell_id: string;
    was_primary: boolean;
  };
}

export interface BulkAllocateResponse {
  message: string;
  statistics: {
    total_requested: number;
    successful: number;
    failed: number;
  };
  successful_allocations: Array<{
    sample_id: number;
    cell_id: string;
    storage_id: number;
    is_primary: boolean;
  }>;
  errors: string[];
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
  name: string;
  display_name?: string;
  organism_name?: string;
  source_type?: string;
  category?: string;
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
  iuk_colors: IUKColor[];
  amylase_variants: AmylaseVariant[];
  growth_media: GrowthMedium[];
}

// Формы для создания и редактирования
export interface CreateSampleData {
  strain_id?: number;
  index_letter_id?: number;
  storage_id?: number;
  original_sample_number?: string;
  source_id?: number;
  location_id?: number;
  appendix_note?: string;
  comment?: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  growth_media_ids?: number[];
  // Динамические характеристики
  characteristics?: SampleCharacteristicsUpdate;
}

export interface UpdateSampleData {
  strain_id?: number;
  index_letter_id?: number;
  storage_id?: number;
  original_sample_number?: string;
  source_id?: number;
  location_id?: number;
  appendix_note?: string;
  comment?: string;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  growth_media_ids?: number[];
  // Динамические характеристики
  characteristics?: SampleCharacteristicsUpdate;
}

export interface SampleCharacteristicsUpdate {
  [key: string]: {
    characteristic_id: number;
    characteristic_name: string;
    characteristic_type: 'boolean' | 'select' | 'text';
    value: boolean | string | null;
  };
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
  filters_applied?: Record<string, unknown>;
}

export interface StrainsListResponse {
  strains: Strain[];
  pagination: PaginationInfo;
  search_query?: string;
  filters_applied?: Record<string, unknown>;
}

export interface StorageListResponse {
  boxes: StorageBox[];
  total_boxes: number;
  total_cells: number;
  occupied_cells: number;
  free_cells: number;
}

// Сводная статистика хранилища
export interface StorageSummaryResponse {
  boxes: Array<{
    box_id: string;
    occupied: number;
    total: number;
    free_cells: number;
  }>;
  total_boxes: number;
  total_cells: number;
  occupied_cells: number;
  free_cells: number;
}

export interface StorageBoxSummary {
  box_id: string;
  rows?: number;
  cols?: number;
  description?: string;
  total_cells: number;
  occupied_cells: number;
  free_cells: number;
}

export interface AnalyticsMonthlyTrend {
  month: string;
  count: number;
}

export interface StorageUtilization {
  occupied: number;
  free: number;
  total: number;
}

export interface AnalyticsResponse {
  totalSamples: number;
  totalStrains: number;
  totalStorage: number;
  sourceTypeDistribution: Record<string, number>;
  strainDistribution: Record<string, number>;
  monthlyTrends: AnalyticsMonthlyTrend[];
  characteristicsStats: Record<string, number>;
  storageUtilization: StorageUtilization;
}

export interface ExportConfig {
  format?: 'csv' | 'xlsx' | 'json';
  fields?: string[];
  includeRelated?: boolean;
  delimiter?: string;
  dateRange?: {
    from?: string;
    to?: string;
  };
}

export interface UploadSamplePhotosResponse {
  created: SamplePhoto[];
  errors: string[];
}
