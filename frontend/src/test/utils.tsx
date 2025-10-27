/* eslint-disable react-refresh/only-export-components */
import React, { type ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';

// Провайдер для тестов с роутингом
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

// Кастомная функция рендера с провайдерами
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Мок для API клиентов
export const createMockApiClient = () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  buildQueryParams: vi.fn(),
  uploadFile: vi.fn(),
});

// Мок данных для штаммов
export const mockStrain = {
  id: 1,
  short_code: 'TEST-001',
  identifier: 'Test Identifier',
  rrna_taxonomy: 'Test Taxonomy',
  name_alt: 'Test Alternative Name',
  rcam_collection_id: 'RCAM-001',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  index_letter_id: 1,
  location_id: 1,
  source_id: 1,
  comment_id: 1,
  appendix_note_id: 1,
};

// Мок данных для образцов
export const mockSample = {
  id: 1,
  sample_number: 'SAMPLE-001',
  strain: mockStrain,
  iuk_color: 'blue',
  amylase_variant: 'positive',
  collection_date: '2024-01-01',
  notes: 'Test sample notes',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Мок ответа списка штаммов
export const mockStrainsResponse = {
  strains: [mockStrain],
  pagination: {
    page: 1,
    limit: 20,
    total_pages: 1,
    total: 1,
    shown: 1,
    has_next: false,
    has_previous: false,
    offset: 0,
  },
  search_query: '',
  filters_applied: {
    search: false,
    advanced_filters: [],
    total_filters: 0,
  },
};

// Мок ответа списка образцов
export const mockSamplesResponse = {
  results: [mockSample],
  count: 1,
  next: null,
  previous: null,
  pagination: {
    page: 1,
    page_size: 20,
    total_pages: 1,
    total_count: 1,
  },
};

// Мок ошибок API
export const mockApiError = {
  message: 'Test error',
  status: 400,
  isClientError: true,
  details: {},
};

export const mockValidationError = {
  message: 'Validation error',
  status: 400,
  field_errors: {
    strain_number: ['This field is required'],
  },
  non_field_errors: [],
};

// Экспортируем все из testing-library
export * from '@testing-library/react';
export { customRender as render };
