import React from 'react';

interface SampleCharacteristicsData {
  has_photo: boolean;
  is_identified: boolean;
  has_antibiotic_activity: boolean;
  has_genome: boolean;
  has_biochemistry: boolean;
  seq_status: boolean;
  mobilizes_phosphates: boolean;
  stains_medium: boolean;
  produces_siderophores: boolean;
  iuk_color_id?: number;
  amylase_variant_id?: number;
  growth_medium_ids: number[];
}

interface SampleCharacteristicsProps {
  data: SampleCharacteristicsData;
  onChange: (field: keyof SampleCharacteristicsData, value: any) => void;
  disabled?: boolean;
}

export const SampleCharacteristics: React.FC<SampleCharacteristicsProps> = ({
  data,
  onChange,
  disabled = false
}) => {
  const handleCheckboxChange = (field: keyof SampleCharacteristicsData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    onChange(field, e.target.checked);
  };

  const handleSelectChange = (field: keyof SampleCharacteristicsData) => (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const value = e.target.value ? parseInt(e.target.value) : undefined;
    onChange(field, value);
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Характеристики образца</h3>

      {/* Основные характеристики */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.has_photo}
            onChange={handleCheckboxChange('has_photo')}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Есть фото</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.is_identified}
            onChange={handleCheckboxChange('is_identified')}
            className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Идентифицирован</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.has_antibiotic_activity}
            onChange={handleCheckboxChange('has_antibiotic_activity')}
            className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Антибиотическая активность</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.has_genome}
            onChange={handleCheckboxChange('has_genome')}
            className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Есть геном</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.has_biochemistry}
            onChange={handleCheckboxChange('has_biochemistry')}
            className="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Есть биохимия</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.seq_status}
            onChange={handleCheckboxChange('seq_status')}
            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Статус секвенирования</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.mobilizes_phosphates}
            onChange={handleCheckboxChange('mobilizes_phosphates')}
            className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Мобилизует фосфаты</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.stains_medium}
            onChange={handleCheckboxChange('stains_medium')}
            className="w-4 h-4 text-pink-600 border-gray-300 rounded focus:ring-pink-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Окрашивает среду</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.produces_siderophores}
            onChange={handleCheckboxChange('produces_siderophores')}
            className="w-4 h-4 text-cyan-600 border-gray-300 rounded focus:ring-cyan-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700">Вырабатывает сидерофоры</span>
        </label>
      </div>

      {/* Дополнительные поля */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* ИУК цвет */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Цвет ИУК (если вырабатывает)
          </label>
          <select
            value={data.iuk_color_id || ''}
            onChange={handleSelectChange('iuk_color_id')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={disabled}
          >
            <option value="">Не выбрано</option>
            <option value="1">Розовый</option>
            <option value="2">Красный</option>
            <option value="3">Оранжевый</option>
            <option value="4">Желтый</option>
            <option value="5">Зеленый</option>
            <option value="6">Синий</option>
            <option value="7">Фиолетовый</option>
            <option value="8">Коричневый</option>
            <option value="9">Черный</option>
          </select>
        </div>

        {/* Вариант амилазы */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Вариант амилазы
          </label>
          <select
            value={data.amylase_variant_id || ''}
            onChange={handleSelectChange('amylase_variant_id')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={disabled}
          >
            <option value="">Не выбрано</option>
            <option value="1">Альфа-амилаза</option>
            <option value="2">Бета-амилаза</option>
            <option value="3">Гамма-амилаза</option>
            <option value="4">Глюкоамилаза</option>
            <option value="5">Пуллуланаза</option>
          </select>
        </div>
      </div>
    </div>
  );
};