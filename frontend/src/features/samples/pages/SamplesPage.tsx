import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSamples } from '../hooks/useSamples';
import { Pagination } from '../../../shared/components';
import { SortableTableHeader } from '../../../shared/components/SortableTableHeader';
import type { Sample, SampleFilters } from '../types';

const SamplesPage: React.FC = () => {
  const [filters, setFilters] = useState<SampleFilters>({
    search: '',
    page: 1,
    limit: 10,
  });

  const navigate = useNavigate();
  const { data, loading, error, refetch } = useSamples(filters);

  const samples: Sample[] = data?.samples ?? [];
  const total = data?.total ?? samples.length;
  const currentPage = data?.page ?? 1;
  const currentLimit = data?.limit ?? filters.limit ?? 25;
  
  // Создаем объект pagination для компонента Pagination
  const pagination = data ? {
    page: currentPage,
    total_pages: Math.ceil(total / currentLimit),
    has_next: data.has_next,
    has_previous: data.has_prev,
    total: total,
    shown: samples.length,
    limit: currentLimit,
    offset: (currentPage - 1) * currentLimit
  } : null;

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleLimitChange = (limit: number) => {
    setFilters(prev => ({ ...prev, limit, page: 1 }));
  };

  const handleSort = (sortKey: string, direction: 'asc' | 'desc') => {
    setFilters(prev => ({ 
      ...prev, 
      sort_by: sortKey, 
      sort_direction: direction, 
      page: 1 
    }));
  };

  const handleRowNavigate = (id: number) => {
    navigate(`/samples/${id}`);
  };

  const handleRowKeyDown = (
    event: React.KeyboardEvent<HTMLTableRowElement>,
    id: number
  ) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleRowNavigate(id);
    }
  };

  const renderDate = (value?: string) =>
    value ? new Date(value).toLocaleDateString('ru-RU') : '--';

  if (loading && !data) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900">Образцы</h1>
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-4 text-gray-600">
            <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600" />
            <span>Загрузка образцов...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900">Образцы</h1>
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="text-sm font-medium">Не удалось загрузить образцы.</p>
          <p className="mt-2 text-sm">{error}</p>
          <button
            type="button"
            onClick={refetch}
            className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Образцы</h1>
          <p className="mt-1 text-sm text-gray-600">
            Показаны {samples.length} из {total} образцов.
          </p>
        </div>
        <Link
          to="/samples/add"
          className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + Добавить образец
        </Link>
      </div>

      {loading && (
        <div className="mt-4 text-sm text-gray-500">Обновляем список...</div>
      )}

      {samples.length > 0 ? (
        <div className="mt-6 overflow-hidden rounded-lg border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <SortableTableHeader
                    label="Образец"
                    sortKey="original_sample_number"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                  <SortableTableHeader
                    label="Штамм"
                    sortKey="strain__short_code"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                  <th className="px-4 py-3 text-left font-medium uppercase tracking-wider text-gray-500">Место хранения</th>
                  <SortableTableHeader
                    label="Источник"
                    sortKey="source__organism_name"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                  <SortableTableHeader
                    label="Локация"
                    sortKey="location__name"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                  <SortableTableHeader
                    label="Создан"
                    sortKey="created_at"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                  <SortableTableHeader
                    label="Обновлен"
                    sortKey="updated_at"
                    currentSortBy={filters.sort_by}
                    currentSortDirection={filters.sort_direction}
                    onSort={handleSort}
                  />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {samples.map((sample) => (
                  <tr
                    key={sample.id}
                    tabIndex={0}
                    role="button"
                    aria-label={`Открыть образец ${sample.id}`}
                    onClick={() => handleRowNavigate(sample.id)}
                    onKeyDown={(event) => handleRowKeyDown(event, sample.id)}
                    className="cursor-pointer hover:bg-gray-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-600"
                  >
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                      {sample.original_sample_number || sample.strain?.short_code || `Образец #${sample.id}`}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {sample.strain?.short_code ?? '--'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {sample.storage ? `${sample.storage.box_id}-${sample.storage.cell_id}` : '--'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {sample.source?.organism_name ?? '--'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {sample.location?.name ?? '--'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {renderDate(sample.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {renderDate(sample.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {pagination && (
            <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
              <Pagination 
                pagination={pagination}
                onPageChange={handlePageChange}
                onLimitChange={handleLimitChange}
                limitOptions={[10, 25, 50]}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="mt-12 rounded-lg border border-dashed border-gray-300 px-6 py-12 text-center text-gray-500">
          <p className="text-base font-medium">Образцы отсутствуют.</p>
          <p className="mt-2 text-sm">Добавьте образец, чтобы увидеть его в списке.</p>
        </div>
      )}
    </div>
  );
};

export { SamplesPage };
export default SamplesPage;