import React from 'react';

interface SortableTableHeaderProps {
  label: string;
  sortKey: string;
  currentSortBy?: string;
  currentSortDirection?: 'asc' | 'desc';
  onSort: (sortKey: string, direction: 'asc' | 'desc') => void;
  className?: string;
}

export const SortableTableHeader: React.FC<SortableTableHeaderProps> = ({
  label,
  sortKey,
  currentSortBy,
  currentSortDirection,
  onSort,
  className = ''
}) => {
  const isActive = currentSortBy === sortKey;
  const nextDirection = isActive && currentSortDirection === 'asc' ? 'desc' : 'asc';

  const handleClick = () => {
    onSort(sortKey, nextDirection);
  };

  const getSortIcon = () => {
    if (!isActive) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }

    if (currentSortDirection === 'asc') {
      return (
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      );
    }

    return (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  return (
    <th 
      className={`px-4 py-3 text-left font-medium uppercase tracking-wider text-gray-500 cursor-pointer hover:bg-gray-100 select-none ${className}`}
      onClick={handleClick}
    >
      <div className="flex items-center space-x-1">
        <span>{label}</span>
        {getSortIcon()}
      </div>
    </th>
  );
};

export default SortableTableHeader;