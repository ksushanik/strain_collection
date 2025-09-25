import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { SampleFiltersComponent } from './SampleFilters';
import type { SampleFilters } from '../types';

// Mock API calls
vi.mock('../../../shared/services/base-api', () => ({
  BaseApiClient: vi.fn().mockImplementation(() => ({
    get: vi.fn().mockResolvedValue({
      data: {
        results: [
          { id: 1, short_code: 'ST001', identifier: 'Strain 1' },
          { id: 2, short_code: 'ST002', identifier: 'Strain 2' }
        ]
      }
    })
  }))
}));

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
  });

  it('renders search input', () => {
    render(
      <SampleFiltersComponent
        filters={mockFilters}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    expect(screen.getByPlaceholderText('Поиск по образцам, штаммам...')).toBeInTheDocument();
  });

  it('calls onFiltersChange when search input changes', async () => {
    render(
      <SampleFiltersComponent
        filters={mockFilters}
        onFiltersChange={mockOnFiltersChange}
        onClearFilters={mockOnClearFilters}
      />
    );

    const searchInput = screen.getByPlaceholderText('Поиск по образцам, штаммам...');
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