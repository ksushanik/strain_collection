import { useState, useEffect, useCallback } from 'react';
import { samplesApi } from '../services/samples-api';
import type { SampleFilters, SamplesListResponse, Sample } from '../types';

interface UseSamplesOptions {
  filters?: SampleFilters;
  page?: number;
  limit?: number;
  autoFetch?: boolean;
}

interface UseSamplesReturn {
  data: SamplesListResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useSamples = ({
  filters = {},
  page = 1,
  limit = 20,
  autoFetch = true
}: UseSamplesOptions = {}): UseSamplesReturn => {
  const [data, setData] = useState<SamplesListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSamples = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await samplesApi.getSamples({
        ...filters,
        page,
        limit
      });
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при загрузке образцов');
    } finally {
      setLoading(false);
    }
  }, [filters, page, limit]);

  useEffect(() => {
    if (autoFetch) {
      fetchSamples();
    }
  }, [fetchSamples, autoFetch]);

  return {
    data,
    loading,
    error,
    refetch: fetchSamples
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