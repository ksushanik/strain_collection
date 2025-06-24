import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import type { PaginationInfo } from '../types';

interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  showInfo?: boolean;
}

const Pagination: React.FC<PaginationProps> = ({ 
  pagination, 
  onPageChange, 
  showInfo = true 
}) => {
  const { page, total_pages, has_next, has_previous, total, shown, limit } = pagination;

  console.log('📄 Pagination component props:', { pagination, currentPage: page });

  // Генерируем массив номеров страниц для отображения
  const getPageNumbers = () => {
    const delta = 2; // Количество страниц слева и справа от текущей
    const range = [];
    const rangeWithDots = [];

    // Всегда показываем первую страницу
    range.push(1);

    // Добавляем страницы вокруг текущей
    for (let i = Math.max(2, page - delta); i <= Math.min(total_pages - 1, page + delta); i++) {
      range.push(i);
    }

    // Всегда показываем последнюю страницу (если она не первая)
    if (total_pages > 1) {
      range.push(total_pages);
    }

    // Удаляем дубликаты и сортируем
    const uniqueRange = [...new Set(range)].sort((a, b) => a - b);

    // Добавляем точки между несвязанными страницами
    let prev = 0;
    for (const current of uniqueRange) {
      if (current - prev > 1) {
        rangeWithDots.push('...');
      }
      rangeWithDots.push(current);
      prev = current;
    }

    return rangeWithDots;
  };

  const pageNumbers = getPageNumbers();

  return (
    <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
      {/* Информация о показанных записях */}
      {showInfo && (
        <div className="text-sm text-gray-600">
          Показано <span className="font-medium">{shown}</span> из{' '}
          <span className="font-medium">{total.toLocaleString()}</span> записей
          {limit && (
            <span className="text-gray-400 ml-2">
              (по {limit} на странице)
            </span>
          )}
        </div>
      )}

      {/* Навигация по страницам */}
      <div className="flex items-center space-x-1">
        {/* Переход к первой странице */}
        <button
          onClick={() => onPageChange(1)}
          disabled={!has_previous}
          className={`p-2 rounded-md ${
            has_previous
              ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              : 'text-gray-300 cursor-not-allowed'
          }`}
          title="Первая страница"
        >
          <ChevronsLeft className="w-4 h-4" />
        </button>

        {/* Предыдущая страница */}
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={!has_previous}
          className={`p-2 rounded-md ${
            has_previous
              ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              : 'text-gray-300 cursor-not-allowed'
          }`}
          title="Предыдущая страница"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Номера страниц */}
        <div className="flex items-center space-x-1">
          {pageNumbers.map((pageNum, index) => {
            if (pageNum === '...') {
              return (
                <span
                  key={`dots-${index}`}
                  className="px-3 py-2 text-gray-400"
                >
                  ...
                </span>
              );
            }

            const pageNumber = pageNum as number;
            const isCurrentPage = pageNumber === page;

            return (
              <button
                key={pageNumber}
                onClick={() => {
                  console.log('🖱️ Page button clicked:', pageNumber);
                  onPageChange(pageNumber);
                }}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isCurrentPage
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {pageNumber}
              </button>
            );
          })}
        </div>

        {/* Следующая страница */}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={!has_next}
          className={`p-2 rounded-md ${
            has_next
              ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              : 'text-gray-300 cursor-not-allowed'
          }`}
          title="Следующая страница"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Переход к последней странице */}
        <button
          onClick={() => onPageChange(total_pages)}
          disabled={!has_next}
          className={`p-2 rounded-md ${
            has_next
              ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              : 'text-gray-300 cursor-not-allowed'
          }`}
          title="Последняя страница"
        >
          <ChevronsRight className="w-4 h-4" />
        </button>
      </div>

      {/* Быстрый переход к странице */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">Перейти к:</span>
        <input
          type="number"
          min={1}
          max={total_pages}
          value={page}
          onChange={(e) => {
            const newPage = parseInt(e.target.value);
            if (newPage >= 1 && newPage <= total_pages) {
              onPageChange(newPage);
            }
          }}
          className="w-16 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <span className="text-sm text-gray-600">из {total_pages}</span>
      </div>
    </div>
  );
};

export default Pagination; 