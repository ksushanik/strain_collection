import { useState, useEffect, useCallback } from 'react';
import { strainsApi } from '../services/strains-api';
import type { Strain, StrainFilters, StrainsListResponse } from '../types';
import type { PaginationInfo } from '../../../shared/types';

export interface UseStrainsResult {
  strains: Strain[];
  loading: boolean;
  error: string | null;
  pagination: PaginationInfo;
  refetch: () => Promise<void>;
  setFilters: (filters: StrainFilters) => void;
  filters: StrainFilters;
}

export const useStrains = (initialFilters: StrainFilters = { page: 1, limit: 50 }): UseStrainsResult => {
  const [strains, setStrains] = useState<Strain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<StrainFilters>(initialFilters);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    total_pages: 1,
    has_next: false,
    has_previous: false,
    total: 0,
    shown: 0,
    limit: 50,
    offset: 0
  });

  const fetchStrains = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response: StrainsListResponse = await strainsApi.getStrains(filters);
      setStrains(response.strains);
      setPagination(response.pagination);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка при загрузке штаммов';
      setError(errorMessage);
      console.error('Error fetching strains:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchStrains();
  }, [fetchStrains]);

  const refetch = useCallback(() => fetchStrains(), [fetchStrains]);

  return {
    strains,
    loading,
    error,
    pagination,
    refetch,
    setFilters,
    filters
  };
};

export interface UseStrainResult {
  strain: Strain | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useStrain = (id: number): UseStrainResult => {
  const [strain, setStrain] = useState<Strain | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStrain = useCallback(async () => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await strainsApi.getStrain(id);
      setStrain(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка при загрузке штамма';
      setError(errorMessage);
      console.error('Error fetching strain:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchStrain();
  }, [fetchStrain]);

  const refetch = useCallback(() => fetchStrain(), [fetchStrain]);

  return {
    strain,
    loading,
    error,
    refetch
  };
};