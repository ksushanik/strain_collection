import React, { useState, useEffect, useCallback } from 'react';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';
import apiService from '../../../../services/api';
import type { StorageBoxSummary } from '../../../../types';

type BoxOption = AutocompleteOption & {
  id: string;
  display_name: string;
  box_id: string;
  total_cells: number;
  free_cells: number;
  rows?: number;
  cols?: number;
  description?: string;
};

type CellOption = AutocompleteOption & {
  id: number;
  display_name: string;
  cell_id: string;
};

interface StorageAutocompleteProps {
  boxValue?: string;
  cellValue?: number;
  onBoxChange: (value: string | undefined) => void;
  onCellChange: (value: number | undefined) => void;
  disabled?: boolean;
  required?: boolean;
  currentCellData?: {
    id: number;
    cell_id: string;
    box_id: string;
  };
}

export const StorageAutocomplete: React.FC<StorageAutocompleteProps> = ({
  boxValue,
  cellValue,
  onBoxChange,
  onCellChange,
  disabled = false,
  required = false,
  currentCellData
}) => {
  const [boxes, setBoxes] = useState<BoxOption[]>([]);
  const [cells, setCells] = useState<CellOption[]>([]);
  const [loadingBoxes, setLoadingBoxes] = useState(false);
  const [loadingCells, setLoadingCells] = useState(false);

  // Загрузка боксов
  const loadBoxes = useCallback(async (searchTerm: string = '') => {
    setLoadingBoxes(true);
    try {
      const response = await apiService.getFreeBoxes(searchTerm, 50);

      const formattedBoxes: BoxOption[] = response.boxes.map((boxSummary: StorageBoxSummary) => {
        const geometryTotal =
          boxSummary.rows && boxSummary.cols
            ? boxSummary.rows * boxSummary.cols
            : undefined;
        const totalCells = geometryTotal ?? boxSummary.total_cells;
        const freeCells = boxSummary.free_cells;
        const dims = boxSummary.rows && boxSummary.cols ? `${boxSummary.rows}×${boxSummary.cols}` : undefined;
        const descSuffix = boxSummary.description ? ` — ${boxSummary.description}` : '';
        const displayName = `${boxSummary.box_id}${dims ? ` (${dims})` : ''} — свободно ${freeCells}/${totalCells}${descSuffix}`;

        return {
          id: boxSummary.box_id,
          display_name: displayName,
          box_id: boxSummary.box_id,
          total_cells: totalCells,
          free_cells: freeCells,
          rows: boxSummary.rows,
          cols: boxSummary.cols,
          description: boxSummary.description,
        };
      });

      // Если текущий бокс уже в списке, но без метаданных (rows/cols/description) — обогащаем его
      if (currentCellData && currentCellData.box_id) {
        const idx = formattedBoxes.findIndex(box => box.box_id === currentCellData.box_id);
        if (idx !== -1) {
          const existing = formattedBoxes[idx];
          const missingMeta = !existing.rows || !existing.cols || existing.description === undefined;
          if (missingMeta) {
            try {
              const currentBoxResponse = await apiService.getFreeBoxes(currentCellData.box_id, 1);
              const currentSummary = currentBoxResponse.boxes.find(
                (box) => box.box_id === currentCellData.box_id,
              );
              if (currentSummary) {
                const geometryTotal =
                  currentSummary.rows && currentSummary.cols
                    ? currentSummary.rows * currentSummary.cols
                    : undefined;
                const totalCells = geometryTotal ?? currentSummary.total_cells;
                const dims = currentSummary.rows && currentSummary.cols ? `${currentSummary.rows}×${currentSummary.cols}` : undefined;
                const descSuffix = currentSummary.description ? ` — ${currentSummary.description}` : '';
                const displayName = `${currentSummary.box_id}${dims ? ` (${dims})` : ''} — свободно ${currentSummary.free_cells}/${totalCells}${descSuffix}`;
                formattedBoxes[idx] = {
                  ...existing,
                  display_name: displayName,
                  rows: currentSummary.rows,
                  cols: currentSummary.cols,
                  description: currentSummary.description,
                };
              }
            } catch {
              // ignore
            }
          }
        }
      }

      // Если есть текущий бокс и его нет в списке свободных, добавляем его
      if (currentCellData && currentCellData.box_id) {
        const currentBoxExists = formattedBoxes.some(box => box.box_id === currentCellData.box_id);
        if (!currentBoxExists) {
          try {
            const currentBoxResponse = await apiService.getFreeBoxes(currentCellData.box_id, 1);
            const currentSummary = currentBoxResponse.boxes.find(
              (box) => box.box_id === currentCellData.box_id,
            );

            const geometryTotal =
              currentSummary?.rows && currentSummary?.cols
                ? currentSummary.rows * currentSummary.cols
                : undefined;
            const totalCells = geometryTotal ?? currentSummary?.total_cells ?? 0;
            const freeCells = currentSummary?.free_cells ?? 0;
            const dims = currentSummary?.rows && currentSummary?.cols ? `${currentSummary.rows}×${currentSummary.cols}` : undefined;
            const descSuffix = currentSummary?.description ? ` — ${currentSummary.description}` : '';
            const displayName = `${currentCellData.box_id}${dims ? ` (${dims})` : ''} — свободно ${freeCells}/${totalCells}${descSuffix}`;

            formattedBoxes.unshift({
              id: currentCellData.box_id,
              display_name: `${displayName} — текущий`,
              box_id: currentCellData.box_id,
              total_cells: totalCells,
              free_cells: freeCells,
              rows: currentSummary?.rows,
              cols: currentSummary?.cols,
              description: currentSummary?.description,
            });
          } catch (currentError) {
            console.error('Ошибка при загрузке данных текущего бокса:', currentError);
            formattedBoxes.unshift({
              id: currentCellData.box_id,
              display_name: `${currentCellData.box_id} (текущий)`,
              box_id: currentCellData.box_id,
              total_cells: 0,
              free_cells: 0,
            });
          }
        }
      }
      
      setBoxes(formattedBoxes);
    } catch (error) {
      console.error('Ошибка при загрузке боксов:', error);
      setBoxes([]);
    } finally {
      setLoadingBoxes(false);
    }
  }, [currentCellData]);

  // Загрузка ячеек для выбранного бокса
  const loadCells = useCallback(async (boxId: string) => {
     if (!boxId) {
       setCells([]);
       return;
     }

     setLoadingCells(true);
     try {
       const response = await apiService.getFreeCells(boxId);

       const cellsData: Array<{ id: number; cell_id: string; display_name?: string }> =
         response.cells ?? [];
       const formattedCells: CellOption[] = cellsData.map((cell) => ({
         id: cell.id,
         display_name: cell.display_name ?? cell.cell_id,
         cell_id: cell.cell_id,
       }));
       
       // Если есть текущая ячейка и она принадлежит этому боксу, добавляем её в список
       if (currentCellData && currentCellData.box_id === boxId) {
         const currentCellExists = formattedCells.some(cell => cell.id === currentCellData.id);
         if (!currentCellExists) {
           formattedCells.unshift({
             id: currentCellData.id,
             display_name: `${currentCellData.cell_id} (текущая)`,
             cell_id: currentCellData.cell_id
           });
         }
       }
       
       setCells(formattedCells);
     } catch (error) {
       console.error('Ошибка при загрузке ячеек:', error);
       setCells([]);
     } finally {
       setLoadingCells(false);
     }
   }, [currentCellData]);

  // Загрузка боксов при монтировании
   useEffect(() => {
     loadBoxes();
  }, [loadBoxes]);

  // Загрузка ячеек при изменении выбранного бокса
   useEffect(() => {
     if (boxValue) {
       loadCells(boxValue);
     } else {
       setCells([]);
       onCellChange(undefined);
     }
  }, [boxValue, loadCells, onCellChange]);

  // Инициализация значений при монтировании компонента
   useEffect(() => {
     if (currentCellData && !boxValue) {
       // Устанавливаем бокс из текущих данных
       onBoxChange(currentCellData.box_id);
    }
    if (currentCellData && !cellValue) {
      // Устанавливаем ячейку из текущих данных
      onCellChange(currentCellData.id);
    }
  }, [currentCellData, boxValue, cellValue, onBoxChange, onCellChange]);

  const handleBoxChange = (value: string | undefined) => {
    onBoxChange(value);
    onCellChange(undefined); // Сбрасываем выбранную ячейку
  };

  // Мемоизируем getDisplayValue для предотвращения бесконечного ре-рендера
  const getBoxDisplayValue = useCallback((box: BoxOption) => {
    return box.display_name;
  }, []);

  const getCellDisplayValue = useCallback((cell: CellOption) => {
    return `Бокс ${boxValue}, ${cell.display_name}`;
  }, [boxValue]);

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
          getDisplayValue={getBoxDisplayValue}
          renderOption={(box) => (
            <div>
              <div className="font-medium text-gray-900">Бокс {box.box_id}{box.rows && box.cols ? ` (${box.rows}×${box.cols})` : ''}</div>
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
          getDisplayValue={getCellDisplayValue}
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
