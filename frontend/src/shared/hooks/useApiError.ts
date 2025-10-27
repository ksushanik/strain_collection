import { useCallback } from "react";
import axios, { type AxiosError } from "axios";
import type { ApiErrorType } from "../types/api-errors";
import {
  isValidationError,
  isNetworkError,
  isServerError,
  isClientError
} from "../types/api-errors";
import { useToast } from "../notifications";

export interface UseApiErrorReturn {
  handleError: (error: ApiErrorType) => void;
  getErrorMessage: (error: ApiErrorType | unknown) => string;
  getFieldErrors: (error: ApiErrorType) => Record<string, string[]> | null;
  isRetryableError: (error: ApiErrorType) => boolean;
}

export const useApiError = (): UseApiErrorReturn => {
  const { error: notifyError, warning: notifyWarning } = useToast();

  const getErrorMessage = useCallback((error: ApiErrorType | unknown): string => {
    if (axios.isAxiosError(error)) {
      const axErr = error as AxiosError<{ error?: string; message?: string }>;
      const serverMessage = axErr.response?.data?.error || axErr.response?.data?.message;
      return serverMessage || axErr.message || "Произошла ошибка при выполнении запроса";
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
      return apiError.message || "Некорректные данные. Проверьте заполненные поля";
    }

    if (isNetworkError(apiError)) {
      return "Проблемы с подключением к серверу. Проверьте интернет-соединение.";
    }

    if (isServerError(apiError)) {
      return "Внутренняя ошибка сервера. Попробуйте позже.";
    }

    if (isClientError(apiError)) {
      if (apiError.status === 401) {
        return "Необходимо авторизоваться";
      }
      if (apiError.status === 403) {
        return "Недостаточно прав для выполнения действия";
      }
      if (apiError.status === 404) {
        return "Запрашиваемый ресурс не найден";
      }
      if (apiError.status === 409) {
        const details: Record<string, unknown> = (
          "details" in apiError && typeof (apiError as { details?: unknown }).details === "object"
            ? ((apiError as { details?: Record<string, unknown> }).details ?? {})
            : {}
        );
        const errorCode =
          typeof details["error_code"] === "string"
            ? (details["error_code"] as string)
            : (
                "code" in apiError && typeof (apiError as { code?: unknown }).code === "string"
                  ? (apiError as { code?: string }).code
                  : undefined
              );
        const baseMessage =
          typeof details["message"] === "string"
            ? (details["message"] as string)
            : (apiError.message || "Конфликт данных при работе с ячейкой хранения");

        const codeHints: Record<string, string> = {
          CELL_OCCUPIED_LEGACY: "Ячейка уже занята (legacy)",
          CELL_OCCUPIED: "Ячейка уже занята другим образцом",
          PRIMARY_ALREADY_ASSIGNED: "Основная ячейка для образца уже назначена",
        };

        const parts: string[] = [baseMessage];
        if (errorCode && codeHints[errorCode]) {
          parts.push(codeHints[errorCode]);
        }
        const recommendedMethod = details["recommended_method"] as string | undefined;
        const recommendedEndpoint = details["recommended_endpoint"] as string | undefined;
        const recommendedPayload = details["recommended_payload"] as Record<string, unknown> | undefined;
        if (recommendedMethod && recommendedEndpoint) {
          parts.push(`Решение: ${recommendedMethod} ${recommendedEndpoint}`);
          if (recommendedPayload) {
            try {
              parts.push(`Payload: ${JSON.stringify(recommendedPayload)}`);
            } catch {
              parts.push("Payload: [не удалось сериализовать данные]");
            }
          }
        }
        return parts.join(" · ");
      }
      return apiError.message || "Произошла ошибка. Повторите попытку позже";
    }

    const maybeMessage = (error as { message?: unknown }).message;
    return typeof maybeMessage === "string" ? maybeMessage : "Неизвестная ошибка";
  }, []);

  const handleError = useCallback((error: ApiErrorType) => {
    console.error("API Error:", error);

    if (isValidationError(error)) {
      console.warn("Validation errors:", error.field_errors);
      notifyWarning(getErrorMessage(error), { title: "Ошибка валидации" });
      return;
    }

    if (isNetworkError(error)) {
      console.error("Network error:", error.message);
      notifyError(getErrorMessage(error), { title: "Проблема с сетью" });
      return;
    }

    if (isServerError(error)) {
      console.error("Server error:", error.message);
      notifyError(getErrorMessage(error), { title: "Ошибка сервера" });
      return;
    }

    if (isClientError(error)) {
      console.warn("Client error:", error.message);
      notifyError(getErrorMessage(error), { title: "Ошибка при запросе" });
    }
  }, [notifyError, notifyWarning, getErrorMessage]);

  const getFieldErrors = useCallback((error: ApiErrorType): Record<string, string[]> | null => {
    if (isValidationError(error) && error.field_errors) {
      return error.field_errors;
    }
    return null;
  }, []);

  const isRetryableError = useCallback((error: ApiErrorType): boolean => {
    if (isNetworkError(error)) {
      return true;
    }

    if (isServerError(error)) {
      return error.status !== 501;
    }

    if (isClientError(error)) {
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
