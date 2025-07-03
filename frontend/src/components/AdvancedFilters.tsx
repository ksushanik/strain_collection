import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Filter, X, RotateCcw } from 'lucide-react';
import StrainAutocomplete from './StrainAutocomplete';

// Типы для расширенных фильтров
export interface FilterCondition {
  id: string;
  field: string;
  operator: 'equals' | 'contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'date_range' | 'is_true' | 'is_false';
  value: string | boolean | number | [string, string];
  logicalOperator?: 'AND' | 'OR';
}

export interface FilterGroup {
  id: string;
  conditions: FilterCondition[];
  logicalOperator: 'AND' | 'OR';
}

export interface AdvancedFiltersConfig {
  entityType: 'strains' | 'samples';
  filters?: FilterGroup[];
  onFiltersChange: (filters: FilterGroup[]) => void;
  onReset: () => void;
}

export interface FilterField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'select';
  options?: Array<{ value: string; label: string }>;
}

const AdvancedFilters: React.FC<AdvancedFiltersConfig> = ({
  entityType,
  filters = [],
  onFiltersChange,
  onReset
}) => {
  const [filterGroups, setFilterGroups] = useState<FilterGroup[]>(filters);
  const [isExpanded, setIsExpanded] = useState(false);

  // Поля для штаммов
  const strainFields: FilterField[] = [
    { key: 'short_code', label: 'Код штамма', type: 'text' },
    { key: 'identifier', label: 'Идентификатор', type: 'text' },
    { key: 'rrna_taxonomy', label: 'Таксономия', type: 'text' },
    { key: 'rcam_collection_id', label: 'RCAM ID', type: 'text' },
    { key: 'created_at', label: 'Дата создания', type: 'date' },
  ];

  // Поля для образцов
  const sampleFields: FilterField[] = [
    { key: 'strain_id', label: 'Штамм', type: 'select' },
    { key: 'box_id', label: 'Box ID', type: 'text' },
    { key: 'source_type', label: 'Тип источника', type: 'text' },
    { key: 'organism_name', label: 'Организм', type: 'text' },
    { key: 'original_sample_number', label: 'Номер образца', type: 'text' },
    { key: 'has_photo', label: 'Есть фото', type: 'boolean' },
    { key: 'is_identified', label: 'Идентифицирован', type: 'boolean' },
    { key: 'has_antibiotic_activity', label: 'Антибиотическая активность', type: 'boolean' },
    { key: 'has_genome', label: 'Есть геном', type: 'boolean' },
    { key: 'has_biochemistry', label: 'Есть биохимия', type: 'boolean' },
    { key: 'seq_status', label: 'Статус секвенирования', type: 'boolean' },
    { key: 'created_at', label: 'Дата создания', type: 'date' },
  ];

  const currentFields = entityType === 'strains' ? strainFields : sampleFields;

  // Операторы для разных типов полей
  const getOperatorsForFieldType = (fieldType: string) => {
    switch (fieldType) {
      case 'text':
        return [
          { value: 'equals', label: 'Равно' },
          { value: 'contains', label: 'Содержит' },
          { value: 'starts_with', label: 'Начинается с' },
          { value: 'ends_with', label: 'Заканчивается на' },
        ];
      case 'number':
        return [
          { value: 'equals', label: 'Равно' },
          { value: 'greater_than', label: 'Больше' },
          { value: 'less_than', label: 'Меньше' },
        ];
      case 'boolean':
        return [
          { value: 'is_true', label: 'Да' },
          { value: 'is_false', label: 'Нет' },
        ];
      case 'date':
        return [
          { value: 'equals', label: 'Равно' },
          { value: 'greater_than', label: 'После' },
          { value: 'less_than', label: 'До' },
          { value: 'date_range', label: 'В диапазоне' },
        ];
      case 'select':
        return [
          { value: 'equals', label: 'Равно' }
        ];
      default:
        return [{ value: 'equals', label: 'Равно' }];
    }
  };

  // Создание нового условия фильтра
  const createNewCondition = (): FilterCondition => ({
    id: `condition_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    field: currentFields[0]?.key || '',
    operator: 'equals',
    value: '',
    logicalOperator: 'AND'
  });

  // Создание новой группы фильтров
  const createNewGroup = (): FilterGroup => ({
    id: `group_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    conditions: [createNewCondition()],
    logicalOperator: 'AND'
  });

  // Добавление новой группы
  const addFilterGroup = () => {
    const newGroup = createNewGroup();
    setFilterGroups(prev => [...prev, newGroup]);
  };

  // Удаление группы
  const removeFilterGroup = (groupId: string) => {
    setFilterGroups(prev => prev.filter(group => group.id !== groupId));
  };

  // Добавление условия в группу
  const addConditionToGroup = (groupId: string) => {
    setFilterGroups(prev => prev.map(group => 
      group.id === groupId 
        ? { ...group, conditions: [...group.conditions, createNewCondition()] }
        : group
    ));
  };

  // Удаление условия из группы
  const removeConditionFromGroup = (groupId: string, conditionId: string) => {
    setFilterGroups(prev => prev.map(group => 
      group.id === groupId 
        ? { ...group, conditions: group.conditions.filter(c => c.id !== conditionId) }
        : group
    ));
  };

  // Обновление условия
  const updateCondition = (groupId: string, conditionId: string, updates: Partial<FilterCondition>) => {
    setFilterGroups(prev => prev.map(group => 
      group.id === groupId 
        ? {
            ...group,
            conditions: group.conditions.map(condition => 
              condition.id === conditionId 
                ? { ...condition, ...updates }
                : condition
            )
          }
        : group
    ));
  };

  // Обновление логического оператора группы
  const updateGroupOperator = (groupId: string, operator: 'AND' | 'OR') => {
    setFilterGroups(prev => prev.map(group => 
      group.id === groupId 
        ? { ...group, logicalOperator: operator }
        : group
    ));
  };

  // Сброс всех фильтров
  const resetAllFilters = () => {
    setFilterGroups([]);
    onReset();
  };

  // Синхронизация с пропсом filters
  useEffect(() => {
    setFilterGroups(filters);
  }, [filters]);

  // Добавление первой группы при разворачивании
  useEffect(() => {
    if (isExpanded && filterGroups.length === 0) {
      addFilterGroup();
    }
  }, [isExpanded]);

  // Уведомление родителя об изменениях (только если это изменение от пользователя)
  useEffect(() => {
    // Избегаем бесконечного цикла: не уведомляем если фильтры идентичны пропсу
    if (JSON.stringify(filterGroups) !== JSON.stringify(filters)) {
      onFiltersChange(filterGroups);
    }
  }, [filterGroups, onFiltersChange, filters]);

  // Рендер поля ввода в зависимости от типа
  const renderValueInput = (condition: FilterCondition, groupId: string) => {
    const field = currentFields.find(f => f.key === condition.field);
    if (!field) return null;

    // Для boolean полей не нужен input
    if (field.type === 'boolean') {
      return null;
    }

    // Для диапазона дат
    if (condition.operator === 'date_range') {
      const [startDate, endDate] = Array.isArray(condition.value) ? condition.value : ['', ''];
      return (
        <div className="flex space-x-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => updateCondition(groupId, condition.id, { 
              value: [e.target.value, endDate] 
            })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <span className="self-center text-gray-500">—</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => updateCondition(groupId, condition.id, { 
              value: [startDate, e.target.value] 
            })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      );
    }

    // Специальный автокомплит для выбора штамма
    if (field.type === 'select' && field.key === 'strain_id') {
      return (
        <StrainAutocomplete
          value={typeof condition.value === 'number' ? condition.value : null}
          onChange={(selectedId) => updateCondition(groupId, condition.id, { value: selectedId || '' })}
          placeholder={`Выберите ${field.label.toLowerCase()}`}
        />
      );
    }

    // Обычные поля
    const inputType = field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text';
    return (
      <input
        type={inputType}
        value={typeof condition.value === 'string' || typeof condition.value === 'number' ? condition.value : ''}
        onChange={(e) => updateCondition(groupId, condition.id, { 
          value: field.type === 'number' ? Number(e.target.value) : e.target.value 
        })}
        placeholder={`Введите ${field.label.toLowerCase()}`}
        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    );
  };

  return (
    <div className="border border-gray-300 rounded-lg bg-white">
      {/* Заголовок */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900">Расширенные фильтры</h3>
          {filterGroups.length > 0 && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
              {filterGroups.reduce((acc, group) => acc + group.conditions.length, 0)} условий
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {filterGroups.length > 0 && (
            <button
              onClick={resetAllFilters}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Сбросить все фильтры"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            {isExpanded ? <X className="w-4 h-4" /> : <Filter className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Содержимое фильтров */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {filterGroups.map((group, groupIndex) => (
            <div key={group.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              {/* Заголовок группы */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-700">
                    Группа {groupIndex + 1}
                  </span>
                  <select
                    value={group.logicalOperator}
                    onChange={(e) => updateGroupOperator(group.id, e.target.value as 'AND' | 'OR')}
                    className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="AND">И (все условия)</option>
                    <option value="OR">ИЛИ (любое условие)</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => addConditionToGroup(group.id)}
                    className="p-1 text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded"
                    title="Добавить условие"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  {filterGroups.length > 1 && (
                    <button
                      onClick={() => removeFilterGroup(group.id)}
                      className="p-1 text-red-600 hover:text-red-700 hover:bg-red-100 rounded"
                      title="Удалить группу"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Условия группы */}
              <div className="space-y-3">
                {group.conditions.map((condition, conditionIndex) => {
                  const field = currentFields.find(f => f.key === condition.field);
                  const operators = field ? getOperatorsForFieldType(field.type) : [];
                  
                  return (
                    <div key={condition.id} className="flex items-center space-x-3 bg-white p-3 rounded-lg">
                      {/* Логический оператор для связи условий */}
                      {conditionIndex > 0 && (
                        <span className="text-sm font-medium text-gray-600 min-w-[30px]">
                          {group.logicalOperator}
                        </span>
                      )}
                      
                      {/* Поле */}
                      <select
                        value={condition.field}
                        onChange={(e) => updateCondition(group.id, condition.id, { 
                          field: e.target.value,
                          operator: 'equals',
                          value: ''
                        })}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {currentFields.map(field => (
                          <option key={field.key} value={field.key}>
                            {field.label}
                          </option>
                        ))}
                      </select>

                      {/* Оператор */}
                      <select
                        value={condition.operator}
                        onChange={(e) => updateCondition(group.id, condition.id, { 
                          operator: e.target.value as any,
                          value: field?.type === 'boolean' ? true : ''
                        })}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {operators.map(op => (
                          <option key={op.value} value={op.value}>
                            {op.label}
                          </option>
                        ))}
                      </select>

                      {/* Значение */}
                      {renderValueInput(condition, group.id)}

                      {/* Удаление условия */}
                      {group.conditions.length > 1 && (
                        <button
                          onClick={() => removeConditionFromGroup(group.id, condition.id)}
                          className="p-2 text-red-600 hover:text-red-700 hover:bg-red-100 rounded"
                          title="Удалить условие"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Добавление новой группы */}
          <div className="flex justify-center">
            <button
              onClick={addFilterGroup}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Добавить группу фильтров</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedFilters; 