import { useState, useEffect, useCallback } from 'react';
import { samplesApi } from '../services/samples-api';
import type { Sample, SampleFilters, SamplesListResponse } from '../types';

export interface UseSamplesReturn {
  data: SamplesListResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useSamples = (filters: SampleFilters): UseSamplesReturn => {
  const [data, setData] = useState<SamplesListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSamples = useCallback(async () => {
    console.log('useSamples: fetchSamples called with filters:', filters);
    try {
      setLoading(true);
      setError(null);
      
      console.log('useSamples: calling samplesApi.getSamples...');
      const response = await samplesApi.getSamples(filters);
      console.log('useSamples: API response:', response);
      
      setData(response);
      console.log('useSamples: data set successfully');
    } catch (err) {
      console.error('useSamples: Ошибка при загрузке образцов:', err);
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
      console.log('useSamples: loading set to false');
    }
  }, [filters]);

  useEffect(() => {
    fetchSamples();
  }, [fetchSamples]);

  return {
    data,
    loading,
    error,
    refetch: fetchSamples,
  };
};

interface UseSampleOptions {
  id: number;
  autoFetch?: boolean;
}

interface UseSampleReturn {
  data: Sample | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useSample = ({
  id,
  autoFetch = true
}: UseSampleOptions): UseSampleReturn => {
  const [data, setData] = useState<Sample | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSample = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await samplesApi.getSample(id);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при загрузке образца');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (autoFetch && id) {
      fetchSample();
    }
  }, [fetchSample, autoFetch, id]);

  return {
    data,
    loading,
    error,
    refetch: fetchSample
  };
};