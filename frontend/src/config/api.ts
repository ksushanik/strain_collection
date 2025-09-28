// API Configuration
// Используем относительные пути для всех режимов (nginx проксирует к backend)
// Это работает как в development, так и в production при использовании Docker

export const API_BASE_URL = ''; // Всегда используем относительные пути через nginx прокси

export const API_ENDPOINTS = {
  // Reference data
  referenceData: `${API_BASE_URL}/api/reference-data/`,
  boxes: `${API_BASE_URL}/api/reference-data/boxes/`,
  boxCells: (boxId: number) => `${API_BASE_URL}/api/reference-data/boxes/${boxId}/cells/`,
  
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