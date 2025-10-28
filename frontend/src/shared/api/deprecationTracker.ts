export interface EndpointDeprecationNotice {
  endpoint?: string;
  message?: string | null;
  replacement?: string | null;
  firstSeenAt: number;
}

type DeprecationSubscriber = (notice: EndpointDeprecationNotice) => void;

const subscribers = new Set<DeprecationSubscriber>();
const seenKeys = new Set<string>();

const buildKey = (endpoint?: string, message?: string | null, replacement?: string | null): string => {
  return [endpoint ?? '', message ?? '', replacement ?? ''].join('||');
};

export const notifyEndpointDeprecated = (notice: {
  endpoint?: string;
  message?: string | null;
  replacement?: string | null;
}): void => {
  const key = buildKey(notice.endpoint, notice.message, notice.replacement);
  if (seenKeys.has(key)) {
    return;
  }

  seenKeys.add(key);
  const enriched: EndpointDeprecationNotice = {
    endpoint: notice.endpoint,
    message: notice.message,
    replacement: notice.replacement,
    firstSeenAt: Date.now(),
  };

  subscribers.forEach((listener) => {
    try {
      listener(enriched);
    } catch (error) {
      // Не даём упасть остальным подписчикам
      console.error('Deprecation subscriber failed', error);
    }
  });
};

export const subscribeEndpointDeprecations = (listener: DeprecationSubscriber): (() => void) => {
  subscribers.add(listener);
  return () => {
    subscribers.delete(listener);
  };
};

export const resetEndpointDeprecations = (): void => {
  seenKeys.clear();
};
