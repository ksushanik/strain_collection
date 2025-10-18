import React, { createContext, useContext, useMemo, useState, useCallback, useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number; // ms
}

interface ToastContextValue {
  notify: (type: ToastType, message: string, options?: { title?: string; duration?: number }) => void;
  success: (message: string, options?: { title?: string; duration?: number }) => void;
  error: (message: string, options?: { title?: string; duration?: number }) => void;
  warning: (message: string, options?: { title?: string; duration?: number }) => void;
  info: (message: string, options?: { title?: string; duration?: number }) => void;
  remove: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  // Возвращаем noop-реализацию, если провайдер не подключен, чтобы тесты не падали
  if (!ctx) {
    const noop = () => {};
    return {
      notify: noop,
      success: noop,
      error: noop,
      warning: noop,
      info: noop,
      remove: noop
    };
  }
  return ctx;
};

const typeStyles: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const typeIcon: Record<ToastType, React.ReactNode> = {
  success: <span className="inline-block w-2 h-2 rounded-full bg-green-600" />,
  error: <span className="inline-block w-2 h-2 rounded-full bg-red-600" />,
  warning: <span className="inline-block w-2 h-2 rounded-full bg-yellow-600" />,
  info: <span className="inline-block w-2 h-2 rounded-full bg-blue-600" />,
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<ToastItem[]>([]);

  const remove = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const notify = useCallback((type: ToastType, message: string, options?: { title?: string; duration?: number }) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const duration = options?.duration ?? 4000;
    const title = options?.title;
    setItems((prev) => [...prev, { id, type, message, title, duration }]);
    // Автоудаление
    window.setTimeout(() => remove(id), duration);
  }, [remove]);

  const success = useCallback((message: string, options?: { title?: string; duration?: number }) => notify('success', message, options), [notify]);
  const error = useCallback((message: string, options?: { title?: string; duration?: number }) => notify('error', message, options), [notify]);
  const warning = useCallback((message: string, options?: { title?: string; duration?: number }) => notify('warning', message, options), [notify]);
  const info = useCallback((message: string, options?: { title?: string; duration?: number }) => notify('info', message, options), [notify]);

  const value = useMemo(() => ({ notify, success, error, warning, info, remove }), [notify, success, error, warning, info, remove]);

  useEffect(() => {
    // Очистка на навигацию/размонтирование (опционально)
    return () => setItems([]);
  }, []);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Контейнер уведомлений */}
      <div className="fixed top-4 right-4 z-50 space-y-2 w-[360px] max-w-[90vw]">
        {items.map((t) => (
          <div key={t.id} className={`border rounded-lg shadow-sm p-3 ${typeStyles[t.type]}`}>
            <div className="flex items-start">
              <div className="mr-2 mt-1">{typeIcon[t.type]}</div>
              <div className="flex-1">
                {t.title && <p className="text-sm font-semibold">{t.title}</p>}
                <p className="text-sm">{t.message}</p>
              </div>
              <button
                onClick={() => remove(t.id)}
                className="ml-3 text-xs text-gray-500 hover:text-gray-700"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};