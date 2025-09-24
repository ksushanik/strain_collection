// Типы для обработки API ошибок

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, any>;
}

export interface ValidationError extends ApiError {
  field_errors?: Record<string, string[]>;
  non_field_errors?: string[];
}

export interface NetworkError extends ApiError {
  isNetworkError: true;
  originalError?: Error;
}

export interface ServerError extends ApiError {
  isServerError: true;
  status: number;
}

export interface ClientError extends ApiError {
  isClientError: true;
  status: number;
}

export type ApiErrorType = ValidationError | NetworkError | ServerError | ClientError;

// Утилитарные функции для проверки типов ошибок
export const isValidationError = (error: ApiErrorType): error is ValidationError => {
  return 'field_errors' in error || 'non_field_errors' in error;
};

export const isNetworkError = (error: ApiErrorType): error is NetworkError => {
  return 'isNetworkError' in error && error.isNetworkError === true;
};

export const isServerError = (error: ApiErrorType): error is ServerError => {
  return 'isServerError' in error && error.isServerError === true;
};

export const isClientError = (error: ApiErrorType): error is ClientError => {
  return 'isClientError' in error && error.isClientError === true;
};