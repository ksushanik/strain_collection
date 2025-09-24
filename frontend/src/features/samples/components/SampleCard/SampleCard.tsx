import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, Edit, Trash2, Beaker } from 'lucide-react';
import type { Sample } from '../../types';

interface SampleCardProps {
  sample: Sample;
  onDelete?: (id: number) => void;
  isSelected?: boolean;
  onSelect?: (id: number, selected: boolean) => void;
}

const SampleCard: React.FC<SampleCardProps> = ({
  sample,
  onDelete,
  isSelected = false,
  onSelect
}) => {
  const handleSelectChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSelect?.(sample.id, e.target.checked);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm(`Вы уверены, что хотите удалить образец ${sample.id}?`)) {
      onDelete?.(sample.id);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {onSelect && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={handleSelectChange}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          )}
          <div className="flex items-center space-x-2">
            <Beaker className="h-5 w-5 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {sample.original_sample_number || `Образец #${sample.id}`}
              </h3>
              {sample.strain && (
                <p className="text-sm text-gray-600">
                  Штамм: {sample.strain.short_code}
                </p>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Link
            to={`/samples/${sample.id}`}
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
            title="Просмотр"
          >
            <Eye size={16} />
          </Link>
          <Link
            to={`/samples/${sample.id}/edit`}
            className="p-2 text-gray-400 hover:text-green-600 transition-colors"
            title="Редактировать"
          >
            <Edit size={16} />
          </Link>
          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-2 text-gray-400 hover:text-red-600 transition-colors"
              title="Удалить"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-2 text-sm">
        {sample.source && (
          <div className="flex justify-between">
            <span className="text-gray-500">Источник:</span>
            <span className="text-gray-900">{sample.source.organism_name}</span>
          </div>
        )}
        {sample.location && (
          <div className="flex justify-between">
            <span className="text-gray-500">Местоположение:</span>
            <span className="text-gray-900">{sample.location.name}</span>
          </div>
        )}
        {sample.iuk_color && (
          <div className="flex justify-between">
            <span className="text-gray-500">Цвет ИУК:</span>
            <span className="text-gray-900">{sample.iuk_color.name}</span>
          </div>
        )}
        {sample.amylase_variant && (
          <div className="flex justify-between">
            <span className="text-gray-500">Вариант амилазы:</span>
            <span className="text-gray-900">{sample.amylase_variant.name}</span>
          </div>
        )}
        {sample.created_at && (
          <div className="flex justify-between">
            <span className="text-gray-500">Дата добавления:</span>
            <span className="text-gray-900">
              {new Date(sample.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>
        )}
      </div>

      {/* Индикаторы состояния */}
      <div className="mt-4 flex flex-wrap gap-2">
        {sample.is_identified && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Идентифицирован
          </span>
        )}
        {sample.has_antibiotic_activity && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Антибиотическая активность
          </span>
        )}
        {sample.storage && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            В хранилище: {sample.storage.box_id}-{sample.storage.cell_id}
          </span>
        )}
      </div>


    </div>
  );
};

export default SampleCard;