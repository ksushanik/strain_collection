import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, Edit, Trash2 } from 'lucide-react';
import type { Strain } from '../../types';

interface StrainCardProps {
  strain: Strain;
  onDelete?: (id: number) => void;
  isSelected?: boolean;
  onSelect?: (id: number, selected: boolean) => void;
}

const StrainCard: React.FC<StrainCardProps> = ({
  strain,
  onDelete,
  isSelected = false,
  onSelect
}) => {
  const handleSelectChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSelect?.(strain.id, e.target.checked);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm(`Вы уверены, что хотите удалить штамм ${strain.short_code}?`)) {
      onDelete?.(strain.id);
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
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {strain.short_code}
            </h3>
            {strain.name_alt && (
              <p className="text-sm text-gray-600">{strain.name_alt}</p>
            )}
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Link
            to={`/strains/${strain.id}`}
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
            title="Просмотр"
          >
            <Eye size={16} />
          </Link>
          <Link
            to={`/strains/${strain.id}/edit`}
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
        {strain.identifier && (
          <div className="flex justify-between">
            <span className="text-gray-500">Идентификатор:</span>
            <span className="text-gray-900">{strain.identifier}</span>
          </div>
        )}
        {strain.rrna_taxonomy && (
          <div className="flex justify-between">
            <span className="text-gray-500">Таксономия rRNA:</span>
            <span className="text-gray-900">{strain.rrna_taxonomy}</span>
          </div>
        )}
        {strain.rcam_collection_id && (
          <div className="flex justify-between">
            <span className="text-gray-500">RCAM ID:</span>
            <span className="text-gray-900">{strain.rcam_collection_id}</span>
          </div>
        )}
        {strain.created_at && (
          <div className="flex justify-between">
            <span className="text-gray-500">Дата создания:</span>
            <span className="text-gray-900">
              {new Date(strain.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>
        )}
      </div>


    </div>
  );
};

export default StrainCard;