import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { SampleFiltersComponent } from './SampleFilters';
import type { SampleFilters } from '../types';

describe('SampleFiltersComponent', () => {
  const mockFilters: SampleFilters = {
    search: '',
    strain_id: undefined,
    storage_id: undefined,
    page: 1,
    limit: 10
  };

  const mockOnFiltersChange = vi.fn();
  const mockOnClearFilters = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    global.fetch = vi.fn((input: RequestInfo) => {
      if (typeof input === 'string' && input.includes('/api/strains/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            strains: [
              { id: 1, short_code: 'ST001', identifier: 'Strain 1' },
              { id: 2, short_code: 'ST002', identifier: 'Strain 2' }
            ]
          })
        } as unknown as Response);
      }

      if (typeof input === 'string' && input.includes('/api/storage/storages/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            results: [
              { id: 10, box_id: 'B1', cell_id: 'A1' },
              { id: 11, box_id: 'B2', cell_id: 'B2' }
            ]
          })
        } as unknown as Response);
      }

      return Promise.resolve({ ok: false, json: async () => ({}) } as unknown as Response);
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders search input', () => {
    render(
      <SampleFiltersComponent
        filters={mockFilters}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    expect(
      screen.getByPlaceholderText('Поиск по номеру образца, штамму, комментарию...')
    ).toBeInTheDocument();
  });

  it('calls onFiltersChange when search input changes', async () => {
    render(
      <SampleFiltersComponent
        filters={mockFilters}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    const searchInput = screen.getByPlaceholderText(
      'Поиск по номеру образца, штамму, комментарию...'
    );
    fireEvent.change(searchInput, { target: { value: 'test search' } });

    await waitFor(() => {
      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        ...mockFilters,
        search: 'test search',
        page: 1
      });
    });
  });

  it('shows filter button', () => {
    render(
      <SampleFiltersComponent
        filters={mockFilters}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    expect(screen.getByText('Фильтры')).toBeInTheDocument();
  });

  it('calls onClearFilters when clear button is clicked', () => {
    const filtersWithData = {
      ...mockFilters,
      search: 'test',
      strain_id: 1
    };

    render(
      <SampleFiltersComponent
        filters={filtersWithData}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    const clearButton = screen.getByText('Очистить');
    fireEvent.click(clearButton);

    expect(mockOnClearFilters).toHaveBeenCalled();
  });
});
