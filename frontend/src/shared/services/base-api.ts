import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { API_BASE_URL } from '../../config/api';
import type { 
  ApiErrorType, 
  ValidationError, 
  NetworkError, 
  ServerError, 
  ClientError 
} from '../types/api-errors';

// Функция для получения CSRF токена из cookies
const getCSRFToken = (): string | undefined => {
  const name = 'csrftoken=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return undefined;
};

export class BaseApiClient {
  protected api: AxiosInstance;

  constructor(baseURL?: string) {
    this.api = axios.create({
      baseURL: baseURL || `${API_BASE_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000, // 10 секунд таймаут
    });

    // Добавляем CSRF токен к каждому запросу
    this.api.interceptors.request.use((config) => {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
      return config;
    });

    // Улучшенная обработка ошибок
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError = this.transformError(error);
        console.error('API Error:', apiError);
        
        // Дополнительная обработка специфических ошибок
        if (apiError.status === 401) {
          this.handleUnauthorized();
        } else if (apiError.status && apiError.status >= 500) {
          this.handleServerError(apiError as ServerError);
        }
        
        return Promise.reject(apiError);
      }
    );
  }

  // Преобразование ошибок Axios в типизированные API ошибки
  private transformError(error: AxiosError): ApiErrorType {
    if (!error.response) {
      // Сетевая ошибка или таймаут
      const networkError: NetworkError = {
        message: error.message || 'Ошибка сети',
        isNetworkError: true,
        originalError: error,
      };
      return networkError;
    }

    const status = error.response.status;
    const data = error.response.data as any;

    if (status >= 400 && status < 500) {
      // Клиентская ошибка
      if (status === 400 && data?.field_errors) {
        // Ошибка валидации
        const validationError: ValidationError = {
          message: data.message || 'Ошибка валидации',
          status,
          field_errors: data.field_errors,
          non_field_errors: data.non_field_errors,
        };
        return validationError;
      }

      const clientError: ClientError = {
        message: data?.message || data?.detail || `Клиентская ошибка (${status})`,
        status,
        isClientError: true,
        details: data,
      };
      return clientError;
    }

    if (status >= 500) {
      // Серверная ошибка
      const serverError: ServerError = {
        message: data?.message || data?.detail || `Серверная ошибка (${status})`,
        status,
        isServerError: true,
        details: data,
      };
      return serverError;
    }

    // Общая ошибка
    return {
      message: data?.message || data?.detail || 'Неизвестная ошибка',
      status,
      details: data,
    };
  }

  // Обработка ошибок авторизации
  private handleUnauthorized(): void {
    // Можно добавить логику перенаправления на страницу входа
    console.warn('Пользователь не авторизован');
  }

  // Обработка серверных ошибок
  private handleServerError(error: ServerError): void {
    // Можно добавить логику уведомлений пользователя
    console.error('Серверная ошибка:', error.message);
  }

  // Типизированные методы HTTP запросов
  protected async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    console.log('BaseApiClient.get: Making request to:', url);
    console.log('BaseApiClient.get: Config:', config);
    try {
      const response: AxiosResponse<T> = await this.api.get(url, config);
      console.log('BaseApiClient.get: Response received:', response.status, response.data);
      return response.data;
    } catch (error) {
      console.error('BaseApiClient.get: Request failed:', error);
      throw error; // Ошибка уже обработана в interceptor
    }
  }

  protected async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.api.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  protected async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.api.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  protected async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.api.patch(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  protected async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.api.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Утилитарные методы для работы с API
  protected buildQueryParams(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, String(item)));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });
    
    return searchParams.toString();
  }

  // Метод для загрузки файлов
  protected async uploadFile<T>(
    url: string, 
    file: File, 
    additionalData?: Record<string, any>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    try {
      const response: AxiosResponse<T> = await this.api.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

}