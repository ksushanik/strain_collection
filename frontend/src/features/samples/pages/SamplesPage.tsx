import React, { useState } from 'react';
import { useSamples } from '../hooks/useSamples';
import type { Sample, SampleFilters } from '../types';

const SamplesPage: React.FC = () => {
  console.log('SamplesPage: Component is rendering');
  
  const [filters, setFilters] = useState<SampleFilters>({ // eslint-disable-line @typescript-eslint/no-unused-vars
    search: '',
    page: 1,
    limit: 20
  });

  const { data, loading, error, refetch } = useSamples(filters);

  // Debug logs
  console.log('=== SamplesPage Debug ===');
  console.log('SamplesPage - loading:', loading);
  console.log('SamplesPage - error:', error);
  console.log('SamplesPage - data:', data);
  console.log('SamplesPage - data?.samples length:', data?.samples?.length);
  console.log('SamplesPage - filters:', filters);
  console.log('========================');



  if (loading && !data) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Образцы</h1>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Образцы</h1>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Ошибка загрузки
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={() => refetch()}
                  className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200"
                >
                  Попробовать снова
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Загрузка образцов...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Ошибка загрузки</h2>
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Образцы</h1>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <span>+</span>
            Добавить образец
          </button>
        </div>
      </div>

      {data && data.samples && data.samples.length > 0 ? (
        <div>
          <div className="mb-4 text-sm text-gray-600">
            Показано {data.samples.length} из {data.total} образцов
          </div>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.samples.map((sample: Sample) => (
              <div key={sample.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {sample.strain?.short_code || `Образец #${sample.id}`}
                  </h3>
                  <span className="text-sm text-gray-500">#{sample.id}</span>
                </div>
                
                <div className="space-y-2 text-sm">
                  {sample.strain && (
                    <div>
                      <span className="font-medium text-gray-700">Штамм:</span>
                      <span className="ml-2 text-gray-600">{sample.strain.short_code}</span>
                    </div>
                  )}
                  
                  {sample.storage && (
                    <div>
                      <span className="font-medium text-gray-700">Хранение:</span>
                      <span className="ml-2 text-gray-600">{sample.storage.box_id}-{sample.storage.cell_id}</span>
                    </div>
                  )}
                  
                  {sample.source && (
                    <div>
                      <span className="font-medium text-gray-700">Источник:</span>
                      <span className="ml-2 text-gray-600">{sample.source.organism_name}</span>
                    </div>
                  )}
                  
                  {sample.location && (
                    <div>
                      <span className="font-medium text-gray-700">Локация:</span>
                      <span className="ml-2 text-gray-600">{sample.location.name}</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex gap-2">
                  <button className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                    Подробнее
                  </button>
                  <button className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
                    Редактировать
                  </button>
                </div>
              </div>
            ))}
          </div>

          {data.total > data.samples.length && (
            <div className="mt-8 text-center">
              <button className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Загрузить еще
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg mb-4">Образцы не найдены</div>
          <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Добавить первый образец
          </button>
        </div>
      )}
    </div>
  );
};

export { SamplesPage };
export default SamplesPage;