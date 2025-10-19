import { useCallback } from 'react';
import axios from 'axios';
import type { AxiosError } from 'axios';
import type { 
  ApiErrorType
} from '../types/api-errors';
import {
  isValidationError,
  isNetworkError,
  isServerError,
  isClientError
} from '../types/api-errors';
import { useToast } from '../notifications';

export interface UseApiErrorReturn {
  handleError: (error: ApiErrorType) => void;
  getErrorMessage: (error: ApiErrorType | unknown) => string;
  getFieldErrors: (error: ApiErrorType) => Record<string, string[]> | null;
  isRetryableError: (error: ApiErrorType) => boolean;
}

export const useApiError = (): UseApiErrorReturn => {
  const { error: notifyError, warning: notifyWarning } = useToast();
  // Обработка ошибки с выводом в консоль и уведомлениями
  const handleError = useCallback((error: ApiErrorType) => {
    console.error('API Error:', error);

    if (isValidationError(error)) {
      console.warn('Validation errors:', error.field_errors);
      notifyWarning(getErrorMessage(error), { title: 'Ошибка валидации' });
    } else if (isNetworkError(error)) {
      console.error('Network error:', error.message);
      notifyError(getErrorMessage(error), { title: 'Сетевая ошибка' });
    } else if (isServerError(error)) {
      console.error('Server error:', error.message);
      notifyError(getErrorMessage(error), { title: 'Ошибка сервера' });
    } else if (isClientError(error)) {
      console.warn('Client error:', error.message);
      notifyError(getErrorMessage(error), { title: 'Ошибка запроса' });
    }
  }, [notifyError, notifyWarning, getErrorMessage]);

  // Получение человекочитаемого сообщения об ошибке
  const getErrorMessage = useCallback((error: ApiErrorType | unknown): string => {
    if (axios.isAxiosError(error)) {
      const axErr = error as AxiosError<{ error?: string; message?: string }>;
      const serverMessage = axErr.response?.data?.error || axErr.response?.data?.message;
      return serverMessage || axErr.message || 'Ошибка запроса';
    }

    const apiError = error as ApiErrorType;

    if (isValidationError(apiError)) {
      if (apiError.non_field_errors && apiError.non_field_errors.length > 0) {
        return apiError.non_field_errors[0];
      }
      if (apiError.field_errors) {
        const firstFieldError = Object.values(apiError.field_errors)[0];
        if (firstFieldError && firstFieldError.length > 0) {
          return firstFieldError[0];
        }
      }
      return apiError.message || 'Ошибка валидации данных';
    }

    if (isNetworkError(apiError)) {
      return 'Проблемы с подключением к серверу. Проверьте интернет-соединение.';
    }

    if (isServerError(apiError)) {
      return 'Внутренняя ошибка сервера. Попробуйте позже.';
    }

    if (isClientError(apiError)) {
      if (apiError.status === 401) {
        return 'Необходима авторизация';
      }
      if (apiError.status === 403) {
        return 'Недостаточно прав доступа';
      }
      if (apiError.status === 404) {
        return 'Запрашиваемый ресурс не найден';
      }
      // Специальная обработка конфликтов размещения хранилища
      if (apiError.status === 409) {
        const details: Record<string, unknown> = (
          'details' in apiError && typeof (apiError as { details?: unknown }).details === 'object'
            ? ((apiError as { details?: Record<string, unknown> }).details ?? {})
            : {}
        );
        const errorCode =
          typeof details['error_code'] === 'string'
            ? (details['error_code'] as string)
            : (
                'code' in apiError && typeof (apiError as { code?: unknown }).code === 'string'
                  ? (apiError as { code?: string }).code
                  : undefined
              );
        const baseMessage =
          typeof details['message'] === 'string'
            ? (details['message'] as string)
            : (apiError.message || 'Конфликт назначения ячейки');

        const codeHints: Record<string, string> = {
          'CELL_OCCUPIED_LEGACY': 'Ячейка уже занята (legacy)',
          'CELL_OCCUPIED': 'Ячейка уже занята',
          'PRIMARY_ALREADY_ASSIGNED': 'Основная ячейка уже назначена',
        };

        const parts: string[] = [baseMessage];
        if (errorCode && codeHints[errorCode]) {
          parts.push(codeHints[errorCode]);
        }
        // Рекомендации, если есть
        const recommendedMethod = details['recommended_method'] as string | undefined;
        const recommendedEndpoint = details['recommended_endpoint'] as string | undefined;
        const recommendedPayload = details['recommended_payload'] as Record<string, unknown> | undefined;
        if (recommendedMethod && recommendedEndpoint) {
          parts.push(`Решение: ${recommendedMethod} ${recommendedEndpoint}`);
          if (recommendedPayload) {
            try {
              parts.push(`Payload: ${JSON.stringify(recommendedPayload)}`);
            } catch {
              parts.push('Payload: [не удалось сериализовать]');
            }
          }
        }
        return parts.join(' — ');
      }
      return apiError.message || 'Ошибка запроса';
    }

    // Fallback for any other error types
    const maybeMessage = (error as { message?: unknown }).message;
    return typeof maybeMessage === 'string' ? maybeMessage : 'Произошла неизвестная ошибка';
  }, []);

  // Получение ошибок полей для форм
  const getFieldErrors = useCallback((error: ApiErrorType): Record<string, string[]> | null => {
    if (isValidationError(error) && error.field_errors) {
      return error.field_errors;
    }
    return null;
  }, []);

  // Проверка, можно ли повторить запрос
  const isRetryableError = useCallback((error: ApiErrorType): boolean => {
    if (isNetworkError(error)) {
      return true; // Сетевые ошибки можно повторить
    }

    if (isServerError(error)) {
      // Серверные ошибки 5xx можно повторить, кроме 501 (Not Implemented)
      return error.status !== 501;
    }

    if (isClientError(error)) {
      // Клиентские ошибки обычно не стоит повторять, кроме 408 (Timeout)
      return error.status === 408;
    }

    return false;
  }, []);

  return {
    handleError,
    getErrorMessage,
    getFieldErrors,
    isRetryableError,
  };
};

// Хук для автоматической обработки ошибок в компонентах
export const useApiErrorHandler = () => {
  const { handleError, getErrorMessage } = useApiError();

  const withErrorHandling = useCallback(
    async <T>(apiCall: () => Promise<T>): Promise<T | null> => {
      try {
        return await apiCall();
      } catch (error) {
        handleError(error as ApiErrorType);
        return null;
      }
    },
    [handleError]
  );

  return {
    withErrorHandling,
    getErrorMessage,
  };
};