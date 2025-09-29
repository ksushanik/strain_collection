import React, { useState, useEffect } from 'react';
import { Plus, X, Edit2, Check, Loader2 } from 'lucide-react';
import apiService from '../../../../services/api';
import type { GrowthMedium } from '../../../../types';

interface GrowthMediaSelectorProps {
  selectedIds: number[];
  onChange: (selectedIds: number[]) => void;
  disabled?: boolean;
}

export const GrowthMediaSelector: React.FC<GrowthMediaSelectorProps> = ({
  selectedIds,
  onChange,
  disabled = false
}) => {
  const [growthMedia, setGrowthMedia] = useState<GrowthMedium[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [newMediumName, setNewMediumName] = useState('');
  const [newMediumDescription, setNewMediumDescription] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');
  const [editingDescription, setEditingDescription] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchGrowthMedia = async () => {
      try {
        setLoading(true);
        const media = await apiService.getGrowthMedia();
        setGrowthMedia(media);
      } catch (err) {
        console.error('Error fetching growth media:', err);
        setError('Ошибка загрузки сред роста');
      } finally {
        setLoading(false);
      }
    };

    fetchGrowthMedia();
  }, []);

  const handleToggleSelection = (mediumId: number) => {
    if (disabled) return;
    
    const newSelectedIds = selectedIds.includes(mediumId)
      ? selectedIds.filter(id => id !== mediumId)
      : [...selectedIds, mediumId];
    
    onChange(newSelectedIds);
  };

  const handleAddNew = async () => {
    if (!newMediumName.trim() || saving) return;

    try {
      setSaving(true);
      const newMedium = await apiService.createGrowthMedium({
        name: newMediumName.trim(),
        description: newMediumDescription.trim() || undefined
      });
      
      setGrowthMedia(prev => [...prev, newMedium]);
      setNewMediumName('');
      setNewMediumDescription('');
      setIsAddingNew(false);
      
      // Автоматически выбираем новую среду
      onChange([...selectedIds, newMedium.id]);
    } catch (err) {
      console.error('Error creating growth medium:', err);
      setError('Ошибка создания среды роста');
    } finally {
      setSaving(false);
    }
  };

  const handleStartEdit = (medium: GrowthMedium) => {
    setEditingId(medium.id);
    setEditingName(medium.name);
    setEditingDescription(medium.description || '');
  };

  const handleSaveEdit = async () => {
    if (!editingName.trim() || !editingId || saving) return;

    try {
      setSaving(true);
      const updatedMedium = await apiService.updateGrowthMedium(editingId, {
        name: editingName.trim(),
        description: editingDescription.trim() || undefined
      });
      
      setGrowthMedia(prev => 
        prev.map(medium => 
          medium.id === editingId ? updatedMedium : medium
        )
      );
      
      setEditingId(null);
      setEditingName('');
      setEditingDescription('');
    } catch (err) {
      console.error('Error updating growth medium:', err);
      setError('Ошибка обновления среды роста');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingName('');
    setEditingDescription('');
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h4 className="text-md font-medium text-gray-800">Среды роста (выберите несколько)</h4>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600">Загрузка сред роста...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h4 className="text-md font-medium text-gray-800">Среды роста (выберите несколько)</h4>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-md font-medium text-gray-800">Среды роста (выберите несколько)</h4>
        {!disabled && (
          <button
            type="button"
            onClick={() => setIsAddingNew(true)}
            className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700"
            disabled={isAddingNew || saving}
          >
            <Plus className="w-4 h-4" />
            <span>Добавить среду</span>
          </button>
        )}
      </div>

      {/* Форма добавления новой среды */}
      {isAddingNew && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Название среды <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={newMediumName}
              onChange={(e) => setNewMediumName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Введите название среды"
              disabled={saving}
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Описание (необязательно)
            </label>
            <textarea
              value={newMediumDescription}
              onChange={(e) => setNewMediumDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              placeholder="Введите описание среды"
              disabled={saving}
            />
          </div>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={handleAddNew}
              className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              disabled={!newMediumName.trim() || saving}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              <span>Добавить</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setIsAddingNew(false);
                setNewMediumName('');
                setNewMediumDescription('');
              }}
              className="flex items-center space-x-1 px-3 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              disabled={saving}
            >
              <X className="w-4 h-4" />
              <span>Отмена</span>
            </button>
          </div>
        </div>
      )}

      {/* Список сред роста */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {growthMedia.map((medium) => (
          <div
            key={medium.id}
            className={`border rounded-lg p-3 transition-colors ${
              selectedIds.includes(medium.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            {editingId === medium.id ? (
              // Режим редактирования
              <div className="space-y-2">
                <input
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                  disabled={saving}
                />
                <textarea
                  value={editingDescription}
                  onChange={(e) => setEditingDescription(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  placeholder="Описание"
                  disabled={saving}
                />
                <div className="flex space-x-1">
                  <button
                    type="button"
                    onClick={handleSaveEdit}
                    className="flex items-center space-x-1 px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50"
                    disabled={!editingName.trim() || saving}
                  >
                    {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                    <span>Сохранить</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="flex items-center space-x-1 px-2 py-1 bg-gray-300 text-gray-700 rounded text-xs hover:bg-gray-400"
                    disabled={saving}
                  >
                    <X className="w-3 h-3" />
                    <span>Отмена</span>
                  </button>
                </div>
              </div>
            ) : (
              // Обычный режим
              <div className="flex items-start justify-between">
                <label className="flex items-start space-x-2 cursor-pointer flex-1">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(medium.id)}
                    onChange={() => handleToggleSelection(medium.id)}
                    className="w-4 h-4 mt-0.5 appearance-none border-2 border-gray-300 rounded bg-white checked:bg-blue-600 checked:border-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 relative checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:absolute checked:after:top-0 checked:after:left-0.5 checked:after:font-bold"
                    disabled={disabled}
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">{medium.name}</span>
                    {medium.description && (
                      <p className="text-xs text-gray-600 mt-1">{medium.description}</p>
                    )}
                  </div>
                </label>
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => handleStartEdit(medium)}
                    className="ml-2 p-1 text-gray-400 hover:text-gray-600"
                    disabled={saving}
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {growthMedia.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>Среды роста не настроены</p>
        </div>
      )}
    </div>
  );
};