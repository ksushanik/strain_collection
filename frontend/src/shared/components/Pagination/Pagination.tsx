import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import type { PaginationInfo } from '../../types';

interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  onLimitChange?: (limit: number) => void;
  showLimitSelector?: boolean;
  limitOptions?: number[];
}

const Pagination: React.FC<PaginationProps> = ({
  pagination,
  onPageChange,
  onLimitChange,
  showLimitSelector = true,
  limitOptions = [10, 25, 50, 100]
}) => {
  const { page, total_pages, has_next, has_previous, total, shown, limit } = pagination;

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= total_pages) {
      onPageChange(newPage);
    }
  };

  const handleLimitChange = (newLimit: number) => {
    if (onLimitChange) {
      onLimitChange(newLimit);
    }
  };

  // Генерируем номера страниц для отображения
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 7;
    
    if (total_pages <= maxVisible) {
      for (let i = 1; i <= total_pages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      
      if (page > 4) {
        pages.push('...');
      }
      
      const start = Math.max(2, page - 2);
      const end = Math.min(total_pages - 1, page + 2);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      if (page < total_pages - 3) {
        pages.push('...');
      }
      
      if (total_pages > 1) {
        pages.push(total_pages);
      }
    }
    
    return pages;
  };

  if (total_pages <= 1) {
    return (
      <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
        <div className="flex items-center text-sm text-gray-700">
          Показано {shown} из {total} записей
        </div>
        {showLimitSelector && onLimitChange && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Показывать по:</span>
            <select
              value={limit}
              onChange={(e) => handleLimitChange(Number(e.target.value))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              {limitOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
      <div className="flex items-center text-sm text-gray-700">
        Показано {shown} из {total} записей
        {showLimitSelector && onLimitChange && (
          <div className="ml-4 flex items-center space-x-2">
            <span>Показывать по:</span>
            <select
              value={limit}
              onChange={(e) => handleLimitChange(Number(e.target.value))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              {limitOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        )}
      </div>
      
      <div className="flex items-center space-x-1">
        {/* Первая страница */}
        <button
          onClick={() => handlePageChange(1)}
          disabled={!has_previous}
          className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Первая страница"
        >
          <ChevronsLeft className="w-4 h-4" />
        </button>
        
        {/* Предыдущая страница */}
        <button
          onClick={() => handlePageChange(page - 1)}
          disabled={!has_previous}
          className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Предыдущая страница"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        
        {/* Номера страниц */}
        <div className="flex items-center space-x-1">
          {getPageNumbers().map((pageNum, index) => (
            <React.Fragment key={index}>
              {pageNum === '...' ? (
                <span className="px-3 py-2 text-gray-500">...</span>
              ) : (
                <button
                  onClick={() => handlePageChange(pageNum as number)}
                  className={`px-3 py-2 text-sm font-medium rounded-md ${
                    pageNum === page
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {pageNum}
                </button>
              )}
            </React.Fragment>
          ))}
        </div>
        
        {/* Следующая страница */}
        <button
          onClick={() => handlePageChange(page + 1)}
          disabled={!has_next}
          className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Следующая страница"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        
        {/* Последняя страница */}
        <button
          onClick={() => handlePageChange(total_pages)}
          disabled={!has_next}
          className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Последняя страница"
        >
          <ChevronsRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default Pagination;