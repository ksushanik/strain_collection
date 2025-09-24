import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
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
  strain_number: 'TEST-001',
  species: 'Test Species',
  source: 'Test Source',
  isolation_date: '2024-01-01',
  notes: 'Test notes',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
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
  results: [mockStrain],
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