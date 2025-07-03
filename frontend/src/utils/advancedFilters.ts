import type { FilterGroup } from '../components/AdvancedFilters';
import type { StrainFilters, SampleFilters } from '../types';

// Функция для конвертации расширенных фильтров в API параметры
export const convertAdvancedFiltersToAPI = (
  filterGroups: FilterGroup[], 
  _entityType: 'strains' | 'samples'
): StrainFilters | SampleFilters => {
  if (filterGroups.length === 0) {
    return {};
  }

  // Базовые фильтры
  const apiFilters: any = {};
  
  // Обрабатываем каждую группу фильтров
  filterGroups.forEach((group) => {
    group.conditions.forEach((condition) => {
      const { field, operator, value } = condition;
      
      // Пропускаем пустые значения
      if (!value && value !== false && value !== 0) {
        return;
      }

      // Формируем ключ для API параметра
      let apiKey = field;
      let apiValue: any = value;

      // Обрабатываем операторы
      switch (operator) {
        case 'equals':
          // Для обычного поиска используем базовое имя поля
          break;
          
        case 'contains':
          // Для текстового поиска используем оператор contains
          apiKey = field + '__contains';
          break;
          
        case 'starts_with':
          apiKey = field + '__startswith';
          break;
          
        case 'ends_with':
          apiKey = field + '__endswith';
          break;
          
        case 'greater_than':
          if (field === 'created_at') {
            apiKey = 'created_after';
          } else {
            apiKey = field + '__gt';
          }
          break;
          
        case 'less_than':
          if (field === 'created_at') {
            apiKey = 'created_before';
          } else {
            apiKey = field + '__lt';
          }
          break;
          
        case 'date_range':
          if (Array.isArray(value) && value.length === 2) {
            const [startDate, endDate] = value;
            if (startDate) {
              apiFilters[field === 'created_at' ? 'created_after' : field + '__gte'] = startDate;
            }
            if (endDate) {
              apiFilters[field === 'created_at' ? 'created_before' : field + '__lte'] = endDate;
            }
            return; // Не добавляем отдельное поле
          }
          break;
          
        case 'is_true':
          apiValue = true;
          break;
          
        case 'is_false':
          apiValue = false;
          break;
      }

      // Добавляем в API фильтры
      apiFilters[apiKey] = apiValue;
    });
  });

  return apiFilters;
};

// Функция для сохранения состояния фильтров в localStorage
export const saveFiltersToStorage = (filterGroups: FilterGroup[], entityType: 'strains' | 'samples') => {
  try {
    const storageKey = `advancedFilters_${entityType}`;
    localStorage.setItem(storageKey, JSON.stringify(filterGroups));
  } catch (error) {
    console.error('Ошибка сохранения фильтров в localStorage:', error);
  }
};

// Функция для загрузки состояния фильтров из localStorage
export const loadFiltersFromStorage = (entityType: 'strains' | 'samples'): FilterGroup[] => {
  try {
    const storageKey = `advancedFilters_${entityType}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (error) {
    console.error('Ошибка загрузки фильтров из localStorage:', error);
  }
  return [];
};

// Функция для очистки сохраненных фильтров
export const clearSavedFilters = (entityType: 'strains' | 'samples') => {
  try {
    const storageKey = `advancedFilters_${entityType}`;
    localStorage.removeItem(storageKey);
  } catch (error) {
    console.error('Ошибка очистки фильтров из localStorage:', error);
  }
};

// Функция для получения человекочитаемого описания фильтров
export const getFiltersDescription = (filterGroups: FilterGroup[]): string => {
  if (filterGroups.length === 0) {
    return 'Фильтры не применены';
  }

  const descriptions = filterGroups.map((group, groupIndex) => {
    const groupDescription = group.conditions.map((condition, conditionIndex) => {
      const { field, operator, value } = condition;
      
      // Получаем человекочитаемое название поля
      const fieldLabels: Record<string, string> = {
        short_code: 'Код штамма',
        identifier: 'Идентификатор',
        rrna_taxonomy: 'Таксономия',
        rcam_collection_id: 'RCAM ID',
        strain_id: 'Штамм',
        box_id: 'Box ID',
        source_type: 'Тип источника',
        organism_name: 'Организм',
        original_sample_number: 'Номер образца',
        has_photo: 'Есть фото',
        is_identified: 'Идентифицирован',
        has_antibiotic_activity: 'Антибиотическая активность',
        has_genome: 'Есть геном',
        has_biochemistry: 'Есть биохимия',
        seq_status: 'Статус секвенирования',
        created_at: 'Дата создания',
      };

      const fieldLabel = fieldLabels[field] || field;

      // Получаем описание оператора
      const operatorLabels: Record<string, string> = {
        equals: 'равно',
        contains: 'содержит',
        starts_with: 'начинается с',
        ends_with: 'заканчивается на',
        greater_than: 'больше',
        less_than: 'меньше',
        date_range: 'в диапазоне',
        is_true: 'да',
        is_false: 'нет',
      };

      const operatorLabel = operatorLabels[operator] || operator;

      // Формируем описание значения
      let valueDescription = '';
      if (operator === 'is_true') {
        valueDescription = '';
      } else if (operator === 'is_false') {
        valueDescription = '';
      } else if (operator === 'date_range' && Array.isArray(value)) {
        const [start, end] = value;
        valueDescription = `${start || '?'} - ${end || '?'}`;
      } else {
        valueDescription = String(value);
      }

      const prefix = conditionIndex > 0 ? ` ${group.logicalOperator} ` : '';
      return `${prefix}${fieldLabel} ${operatorLabel}${valueDescription ? ` "${valueDescription}"` : ''}`;
    }).join('');

    return groupIndex > 0 ? ` ИЛИ (${groupDescription})` : `(${groupDescription})`;
  }).join('');

  return descriptions;
};

// Функция для проверки валидности группы фильтров
export const validateFilterGroup = (group: FilterGroup): boolean => {
  return group.conditions.every(condition => {
    // Проверяем, что поле выбрано
    if (!condition.field) return false;
    
    // Для boolean полей значение может быть пустым
    if (condition.field.startsWith('has_') || condition.field === 'is_identified' || condition.field === 'seq_status') {
      return true;
    }
    
    // Для остальных полей проверяем наличие значения
    if (condition.operator === 'date_range') {
      return Array.isArray(condition.value) && (condition.value[0] || condition.value[1]);
    }
    
    return condition.value !== '' && condition.value != null;
  });
};

// Функция для подсчета активных фильтров
export const countActiveFilters = (filterGroups: FilterGroup[]): number => {
  return filterGroups.reduce((total, group) => {
    return total + group.conditions.filter(condition => {
      if (condition.operator === 'date_range') {
        return Array.isArray(condition.value) && (condition.value[0] || condition.value[1]);
      }
      return condition.value !== '' && condition.value != null;
    }).length;
  }, 0);
}; 