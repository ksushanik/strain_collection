import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import apiService from '../../../../services/api';
import type { SampleCharacteristic } from '../../../../types';

interface SampleCharacteristicsProps {
  data: { [key: string]: any };
  onChange: (field: string, value: any) => void;
  disabled?: boolean;
  sampleId?: number; // For editing existing samples
}

export const SampleCharacteristics: React.FC<SampleCharacteristicsProps> = ({
  data,
  onChange,
  disabled = false
}) => {
  const [characteristics, setCharacteristics] = useState<SampleCharacteristic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCharacteristics = async () => {
      try {
        setLoading(true);
        const fetchedCharacteristics = await apiService.getCharacteristics();
        setCharacteristics(fetchedCharacteristics);
      } catch (err) {
        console.error('Error fetching characteristics:', err);
        setError('Ошибка загрузки характеристик');
      } finally {
        setLoading(false);
      }
    };

    fetchCharacteristics();
  }, []);

  const handleCharacteristicChange = (characteristic: SampleCharacteristic, value: any) => {
    console.log('🔧 SampleCharacteristics: handleCharacteristicChange called with:', {
      characteristic: characteristic.name,
      characteristicId: characteristic.id,
      type: characteristic.characteristic_type,
      value: value
    });
    
    // For dynamic characteristics, we store them in a characteristics object
    const currentCharacteristics = data.characteristics || {};
    const updatedCharacteristics = {
      ...currentCharacteristics,
      [characteristic.name]: {
        characteristic_id: characteristic.id,
        characteristic_type: characteristic.characteristic_type,
        value: value
      }
    };
    
    console.log('🔧 SampleCharacteristics: Updated characteristics object:', updatedCharacteristics);
    
    onChange('characteristics', updatedCharacteristics);
  };



  const getCharacteristicValue = (characteristic: SampleCharacteristic): any => {
    const characteristicData = data.characteristics?.[characteristic.name];
    return characteristicData?.value ?? false;
  };

  const renderCharacteristicInput = (characteristic: SampleCharacteristic) => {
    const value = getCharacteristicValue(characteristic);

    switch (characteristic.characteristic_type) {
      case 'boolean':
        return (
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={Boolean(value)}
              onChange={(e) => handleCharacteristicChange(characteristic, e.target.checked)}
              className="w-4 h-4 appearance-none border-2 border-gray-300 rounded bg-white checked:bg-blue-600 checked:border-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 relative checked:after:content-['✓'] checked:after:text-white checked:after:text-xs checked:after:absolute checked:after:top-0 checked:after:left-0.5 checked:after:font-bold"
              disabled={disabled}
            />
            <span className="text-sm text-gray-700">{characteristic.display_name}</span>
          </label>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              {characteristic.display_name}
              {characteristic.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <select
              value={value || ''}
              onChange={(e) => handleCharacteristicChange(characteristic, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={disabled}
              required={characteristic.is_required}
            >
              <option value="">Не выбрано</option>
              {characteristic.options?.map((option) => (
                <option key={option.id} value={option.value}>
                  {option.display_value}
                </option>
              ))}
            </select>
          </div>
        );

      case 'text':
        return (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              {characteristic.display_name}
              {characteristic.is_required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
              value={value || ''}
              onChange={(e) => handleCharacteristicChange(characteristic, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              disabled={disabled}
              required={characteristic.is_required}
              placeholder={characteristic.description || `Введите ${characteristic.display_name.toLowerCase()}`}
            />
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h3 className="text-lg font-medium text-gray-900">Характеристики образца</h3>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600">Загрузка характеристик...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h3 className="text-lg font-medium text-gray-900">Характеристики образца</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  // Separate characteristics by type for better organization
  const booleanCharacteristics = characteristics.filter(c => c.characteristic_type === 'boolean');
  const selectCharacteristics = characteristics.filter(c => c.characteristic_type === 'select');
  const textCharacteristics = characteristics.filter(c => c.characteristic_type === 'text');

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900">Характеристики образца</h3>



      {/* Boolean characteristics in a grid */}
      {booleanCharacteristics.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-800 mb-3">Характеристики (да/нет)</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {booleanCharacteristics.map((characteristic) => (
              <div key={characteristic.id}>
                {renderCharacteristicInput(characteristic)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Select characteristics */}
      {selectCharacteristics.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-800 mb-3">Характеристики (выбор)</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selectCharacteristics.map((characteristic) => (
              <div key={characteristic.id}>
                {renderCharacteristicInput(characteristic)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Text characteristics */}
      {textCharacteristics.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-800 mb-3">Характеристики (текст)</h4>
          <div className="space-y-4">
            {textCharacteristics.map((characteristic) => (
              <div key={characteristic.id}>
                {renderCharacteristicInput(characteristic)}
              </div>
            ))}
          </div>
        </div>
      )}

      {characteristics.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>Характеристики не настроены</p>
        </div>
      )}
    </div>
  );
};