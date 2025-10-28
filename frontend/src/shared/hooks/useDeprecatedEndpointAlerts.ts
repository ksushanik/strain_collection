import { useEffect } from 'react';
import { subscribeEndpointDeprecations } from '../api/deprecationTracker';
import { useToast } from '../notifications';

const formatReplacement = (replacement?: string | null): string | null => {
  if (!replacement) {
    return null;
  }

  return replacement.startsWith('http') ? replacement : `Используйте ${replacement}`;
};

export const useDeprecatedEndpointAlerts = (): void => {
  const { warning } = useToast();

  useEffect(() => {
    const unsubscribe = subscribeEndpointDeprecations((notice) => {
      const parts: string[] = [];
      if (notice.message) {
        parts.push(notice.message);
      } else if (notice.endpoint) {
        parts.push(`Ручка ${notice.endpoint} помечена как устаревшая.`);
      }

      const replacementHint = formatReplacement(notice.replacement);
      if (replacementHint) {
        parts.push(replacementHint);
      }

      const text = parts.join(' ');
      if (text) {
        warning(text, {
          title: 'Устаревший API',
          duration: 8000,
        });
      }
    });

    return unsubscribe;
  }, [warning]);
};
