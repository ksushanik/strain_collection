import React from 'react';
import { Loader2, AlertCircle, Wifi, WifiOff } from 'lucide-react';

interface LoadingStateProps {
  loading?: boolean;
  error?: string | null;
  retry?: () => void;
  children?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'inline' | 'overlay' | 'page';
  loadingText?: string;
  emptyText?: string;
  isEmpty?: boolean;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  loading = false,
  error = null,
  retry,
  children,
  size = 'md',
  variant = 'inline',
  loadingText = 'Загрузка...',
  emptyText = 'Нет данных',
  isEmpty = false
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const containerClasses = {
    inline: 'flex items-center justify-center p-4',
    overlay: 'absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10',
    page: 'min-h-screen flex items-center justify-center'
  };

  // Определяем, является ли ошибка сетевой
  const isNetworkError = error && (
    error.toLowerCase().includes('network') ||
    error.toLowerCase().includes('fetch') ||
    error.toLowerCase().includes('connection') ||
    error.toLowerCase().includes('timeout')
  );

  if (loading) {
    return (
      <div className={containerClasses[variant]}>
        <div className="text-center">
          <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-600 mx-auto mb-2`} />
          <p className="text-gray-600 text-sm">{loadingText}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={containerClasses[variant]}>
        <div className="text-center max-w-md">
          <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
            {isNetworkError ? (
              <WifiOff className="w-6 h-6 text-red-600" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600" />
            )}
          </div>
          
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {isNetworkError ? 'Проблемы с подключением' : 'Произошла ошибка'}
          </h3>
          
          <p className="text-gray-600 text-sm mb-4">
            {isNetworkError 
              ? 'Проверьте подключение к интернету и попробуйте снова'
              : error
            }
          </p>

          {retry && (
            <button
              onClick={retry}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {isNetworkError ? (
                <Wifi className="w-4 h-4 mr-2" />
              ) : (
                <Loader2 className="w-4 h-4 mr-2" />
              )}
              Попробовать снова
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={containerClasses[variant]}>
        <div className="text-center">
          <div className="w-12 h-12 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <AlertCircle className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 text-sm">{emptyText}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};