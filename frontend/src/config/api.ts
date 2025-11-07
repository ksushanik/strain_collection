// API Configuration
// По умолчанию используем относительные пути (через nginx в Docker).
// Для локального dev/preview без прокси можно задать VITE_API_URL в .env

export const API_BASE_URL = (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_URL) ?? '';

export const API_ENDPOINTS = {
  // Reference data
  referenceData: `${API_BASE_URL}/api/reference-data/`,
  boxes: `${API_BASE_URL}/api/storage/boxes/`,
  boxCells: (boxId: number) => `${API_BASE_URL}/api/storage/boxes/${boxId}/cells/`,
  
  // Strains
  strains: `${API_BASE_URL}/api/strains/`,
  strainCreate: `${API_BASE_URL}/api/strains/create/`,
  strainUpdate: (strainId: number) => `${API_BASE_URL}/api/strains/${strainId}/update/`,
  
  // Samples
  samples: `${API_BASE_URL}/api/samples/`,
  sampleCreate: `${API_BASE_URL}/api/samples/create/`,
  
  // Storage
  storage: `${API_BASE_URL}/api/storage/`,
  storageBoxes: `${API_BASE_URL}/api/storage/boxes/`,
  
  // Stats
  stats: `${API_BASE_URL}/api/stats/`,
};

// Helper function for building search URLs
export const buildSearchUrl = (baseUrl: string, search?: string): string => {
  if (!search) return baseUrl;
  const separator = baseUrl.includes('?') ? '&' : '?';
  return `${baseUrl}${separator}search=${encodeURIComponent(search)}`;
};
