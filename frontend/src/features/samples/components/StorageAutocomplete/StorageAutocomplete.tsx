import React, { useState, useEffect } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';
import apiService from '../../../../services/api';

interface BoxOption extends AutocompleteOption {
  id: string;
  display_name: string;
  box_id: string;
  total_cells: number;
  free_cells: number;
}

interface CellOption extends AutocompleteOption {
  id: number;
  display_name: string;
  cell_id: string;
}

interface StorageAutocompleteProps {
  boxValue?: string;
  cellValue?: number;
  onBoxChange: (value: string | undefined) => void;
  onCellChange: (value: number | undefined) => void;
  disabled?: boolean;
  required?: boolean;
}

export const StorageAutocomplete: React.FC<StorageAutocompleteProps> = ({
  boxValue,
  cellValue,
  onBoxChange,
  onCellChange,
  disabled = false,
  required = false
}) => {
  const [boxes, setBoxes] = useState<BoxOption[]>([]);
  const [cells, setCells] = useState<CellOption[]>([]);
  const [loadingBoxes, setLoadingBoxes] = useState(false);
  const [loadingCells, setLoadingCells] = useState(false);

  // Загрузка боксов
  const loadBoxes = async (searchTerm: string = '') => {
    setLoadingBoxes(true);
    try {
      const response = await apiService.getFreeBoxes(searchTerm, 50);
      
      const boxesData = response.results || response;
      const formattedBoxes: BoxOption[] = boxesData.map((box: any) => ({
        id: box.box_id,
        display_name: `${box.box_id} (${box.free_cells}/${box.total_cells} свободно)`,
        box_id: box.box_id,
        total_cells: box.total_cells,
        free_cells: box.free_cells
      }));
      
      setBoxes(formattedBoxes);
    } catch (error) {
      console.error('Ошибка при загрузке боксов:', error);
      setBoxes([]);
    } finally {
      setLoadingBoxes(false);
    }
  };

  // Загрузка ячеек для выбранного бокса
  const loadCells = async (boxId: string) => {
    if (!boxId) {
      setCells([]);
      return;
    }

    setLoadingCells(true);
    try {
      const response = await apiService.getFreeCells(boxId);
      
      const cellsData = response.results || response;
      const formattedCells: CellOption[] = cellsData.map((cell: any) => ({
        id: cell.id,
        display_name: cell.cell_id,
        cell_id: cell.cell_id
      }));
      
      setCells(formattedCells);
    } catch (error) {
      console.error('Ошибка при загрузке ячеек:', error);
      setCells([]);
    } finally {
      setLoadingCells(false);
    }
  };

  // Загрузка боксов при монтировании
  useEffect(() => {
    loadBoxes();
  }, []);

  // Загрузка ячеек при изменении выбранного бокса
  useEffect(() => {
    if (boxValue) {
      loadCells(boxValue);
    } else {
      setCells([]);
      onCellChange(undefined);
    }
  }, [boxValue]);

  const handleBoxChange = (value: string | undefined) => {
    onBoxChange(value);
    onCellChange(undefined); // Сбрасываем выбранную ячейку
  };

  return (
    <div className="space-y-4">
      {/* Выбор бокса */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Бокс для хранения {required && <span className="text-red-500">*</span>}
        </label>
        <Autocomplete
          value={boxValue}
          onChange={handleBoxChange}
          options={boxes}
          onSearch={loadBoxes}
          placeholder="Введите ID бокса..."
          disabled={disabled}
          required={required}
          loading={loadingBoxes}
          emptyMessage="Свободные боксы не найдены"
          getDisplayValue={(box) => box.display_name}
          renderOption={(box) => (
            <div>
              <div className="font-medium text-gray-900">Бокс {box.box_id}</div>
              <div className="text-sm text-gray-500">
                Свободно: {box.free_cells} из {box.total_cells} ячеек
              </div>
            </div>
          )}
        />
      </div>

      {/* Выбор ячейки */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Ячейка {required && <span className="text-red-500">*</span>}
        </label>
        <Autocomplete
          value={cellValue}
          onChange={onCellChange}
          options={cells}
          placeholder={boxValue ? "Выберите ячейку..." : "Сначала выберите бокс"}
          disabled={disabled || !boxValue}
          required={required}
          loading={loadingCells}
          emptyMessage="Свободные ячейки не найдены"
          getDisplayValue={(cell) => `Бокс ${boxValue}, ${cell.display_name}`}
          renderOption={(cell) => (
            <div>
              <div className="font-medium text-gray-900">{cell.display_name}</div>
              <div className="text-sm text-gray-500">Бокс {boxValue}</div>
            </div>
          )}
        />
      </div>
    </div>
  );
};