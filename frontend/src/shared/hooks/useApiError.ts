import { useCallback } from 'react';
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
  getErrorMessage: (error: ApiErrorType) => string;
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
  }, [notifyError, notifyWarning]);

  // Получение человекочитаемого сообщения об ошибке
  const getErrorMessage = useCallback((error: ApiErrorType): string => {
    if (isValidationError(error)) {
      if (error.non_field_errors && error.non_field_errors.length > 0) {
        return error.non_field_errors[0];
      }
      if (error.field_errors) {
        const firstFieldError = Object.values(error.field_errors)[0];
        if (firstFieldError && firstFieldError.length > 0) {
          return firstFieldError[0];
        }
      }
      return error.message || 'Ошибка валидации данных';
    }

    if (isNetworkError(error)) {
      return 'Проблемы с подключением к серверу. Проверьте интернет-соединение.';
    }

    if (isServerError(error)) {
      return 'Внутренняя ошибка сервера. Попробуйте позже.';
    }

    if (isClientError(error)) {
      if (error.status === 401) {
        return 'Необходима авторизация';
      }
      if (error.status === 403) {
        return 'Недостаточно прав доступа';
      }
      if (error.status === 404) {
        return 'Запрашиваемый ресурс не найден';
      }
      // Специальная обработка конфликтов размещения хранилища
      if (error.status === 409) {
        const details = error.details || {};
        const errorCode = (details['error_code'] as string | undefined) || (error.code as string | undefined);
        const baseMessage = (details['message'] as string | undefined) || error.message || 'Конфликт назначения ячейки';

        const codeHints: Record<string, string> = {
          CELL_OCCUPIED_LEGACY: 'Ячейка уже занята (legacy). Очистите ячейку в хранилище.',
          CELL_OCCUPIED_ALLOCATION: 'Ячейка занята через мульти-ячейку. Снимите размещение через Allocate.',
          LEGACY_ASSIGN_BLOCKED: 'У образца уже есть размещения. Используйте мульти-ячейки (Allocate).',
          SAMPLE_ALREADY_PLACED: 'Образец уже размещён в другой ячейке. Очистите текущую ячейку.',
          ASSIGN_CONFLICT: 'Обнаружен конфликт назначения. Сверьте текущие размещения образца и ячейки.'
        };

        const hint = errorCode ? codeHints[errorCode] : undefined;
        const recommendedMethod = details['recommended_method'] as string | undefined;
        const recommendedEndpoint = details['recommended_endpoint'] as string | undefined;
        const recommendedPayload = details['recommended_payload'] as unknown | undefined;

        const parts: string[] = [baseMessage];
        if (hint) parts.push(hint);
        if (recommendedMethod && recommendedEndpoint) {
          parts.push(`Решение: ${recommendedMethod} ${recommendedEndpoint}`);
        }
        if (recommendedPayload) {
          try {
            parts.push(`Payload: ${JSON.stringify(recommendedPayload)}`);
          } catch {}
        }
        return parts.join(' — ');
      }
      return error.message || 'Ошибка запроса';
    }

    // Fallback for any other error types
    return (error as any).message || 'Произошла неизвестная ошибка';
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