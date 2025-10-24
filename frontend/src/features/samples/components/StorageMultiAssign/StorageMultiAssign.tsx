import React, { useEffect, useState, useCallback } from 'react';
import apiService from '../../../../services/api';
import { Autocomplete, type AutocompleteOption } from '../../../../shared/components/Autocomplete';
import type { StorageBoxSummary } from '../../../../types';

// Типы для опций боксов и ячеек
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

export interface AssignedCell {
  id: number; // storage cell id
  cell_id: string;
  box_id: string;
}

interface StorageMultiAssignProps {
  disabled?: boolean;
  currentPrimaryCell?: { id: number; cell_id: string; box_id: string };
  onChange?: (cells: AssignedCell[]) => void;
  existingAllocations?: Array<{ id: number; cell_id: string; box_id: string; allocated_at?: string | null }>;
}

// Компонент для удобного выбора нескольких ячеек хранения
export const StorageMultiAssign: React.FC<StorageMultiAssignProps> = ({
  disabled = false,
  currentPrimaryCell,
  onChange,
  existingAllocations = [],
}) => {
  const [boxes, setBoxes] = useState<BoxOption[]>([]);
  const [cells, setCells] = useState<CellOption[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | undefined>(undefined);
  const [selectedCellId, setSelectedCellId] = useState<number | undefined>(undefined);
  const [assignedCells, setAssignedCells] = useState<AssignedCell[]>([]);
  const [loadingBoxes, setLoadingBoxes] = useState(false);
  const [loadingCells, setLoadingCells] = useState(false);

  // Загрузка боксов
  const loadBoxes = useCallback(async (searchTerm: string = '') => {
    setLoadingBoxes(true);
    try {
      const response = await apiService.getFreeBoxes(searchTerm, 50);
      const formattedBoxes: BoxOption[] = response.boxes.map((boxSummary) => {
        const freeCells = boxSummary.free_cells;
        const totalCells = boxSummary.total_cells;
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

      // Добавляем текущий бокс, если он не в списке свободных
      if (currentPrimaryCell?.box_id) {
        const exists = formattedBoxes.some((b) => b.box_id === currentPrimaryCell.box_id);
        if (!exists) {
          try {
            const curResp = await apiService.getFreeBoxes(currentPrimaryCell.box_id, 1);
            const curSummary = curResp.boxes.find((b: StorageBoxSummary) => b.box_id === currentPrimaryCell.box_id);
            const totalCells = curSummary?.total_cells ?? 0;
            const freeCells = curSummary?.free_cells ?? 0;
            const dims = curSummary?.rows && curSummary?.cols ? `${curSummary.rows}×${curSummary.cols}` : undefined;
            const descSuffix = curSummary?.description ? ` — ${curSummary.description}` : '';
            const displayName = `${currentPrimaryCell.box_id}${dims ? ` (${dims})` : ''} — свободно ${freeCells}/${totalCells}${descSuffix}`;
            formattedBoxes.unshift({
              id: currentPrimaryCell.box_id,
              display_name: `${displayName} — текущий`,
              box_id: currentPrimaryCell.box_id,
              total_cells: totalCells,
              free_cells: freeCells,
              rows: curSummary?.rows,
              cols: curSummary?.cols,
              description: curSummary?.description,
            });
          } catch {
            formattedBoxes.unshift({
              id: currentPrimaryCell.box_id,
              display_name: `${currentPrimaryCell.box_id} (текущий)`,
              box_id: currentPrimaryCell.box_id,
              total_cells: 0,
              free_cells: 0,
            });
          }
        }
      }

      setBoxes(formattedBoxes);
    } catch (e) {
      console.error('Ошибка при загрузке боксов:', e);
      setBoxes([]);
    } finally {
      setLoadingBoxes(false);
    }
  }, [currentPrimaryCell?.box_id]);

  // Загрузка ячеек выбранного бокса
  const loadCells = useCallback(async (boxId: string) => {
    if (!boxId) {
      setCells([]);
      return;
    }
    setLoadingCells(true);
    try {
      const response = await apiService.getFreeCells(boxId);
      const cellsData: Array<{ id: number; cell_id: string; display_name?: string }> = response.cells ?? [];
      const formattedCells: CellOption[] = cellsData.map((cell) => ({
        id: cell.id,
        display_name: cell.display_name ?? cell.cell_id,
        cell_id: cell.cell_id,
      }));

      // Текущая ячейка, если относится к выбранному боксу
      if (currentPrimaryCell && currentPrimaryCell.box_id === boxId) {
        const exists = formattedCells.some((c) => c.id === currentPrimaryCell.id);
        if (!exists) {
          formattedCells.unshift({
            id: currentPrimaryCell.id,
            display_name: `${currentPrimaryCell.cell_id} (текущая)`,
            cell_id: currentPrimaryCell.cell_id,
          });
        }
      }

      setCells(formattedCells);
    } catch (e) {
      console.error('Ошибка при загрузке ячеек:', e);
      setCells([]);
    } finally {
      setLoadingCells(false);
    }
  }, [currentPrimaryCell]);

  // Инициализация данных
  useEffect(() => {
    loadBoxes();
  }, [loadBoxes]);

  useEffect(() => {
    if (selectedBoxId) {
      loadCells(selectedBoxId);
    } else {
      setCells([]);
      setSelectedCellId(undefined);
    }
  }, [selectedBoxId, loadCells]);

  // Синхронизация наружу
  useEffect(() => {
    onChange?.(assignedCells);
  }, [assignedCells, onChange]);

  const handleAddCell = () => {
    if (!selectedBoxId || !selectedCellId) return;
    const cell = cells.find((c) => c.id === selectedCellId);
    if (!cell) return;

    const already = assignedCells.some((a) => a.id === selectedCellId) || existingAllocations?.some((a) => a.id === selectedCellId);
    if (already) return;

    setAssignedCells((prev) => [
      ...prev,
      { id: selectedCellId, cell_id: cell.cell_id, box_id: selectedBoxId },
    ]);
  };

  const handleRemoveCell = (id: number) => {
    setAssignedCells((prev) => prev.filter((c) => c.id !== id));
  };

  const handleClearAll = () => {
    setAssignedCells([]);
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Дополнительные ячейки хранения
        </label>
        <Autocomplete
          value={selectedBoxId}
          onChange={setSelectedBoxId}
          options={boxes}
          onSearch={loadBoxes}
          placeholder="Введите ID бокса..."
          disabled={disabled}
          loading={loadingBoxes}
          emptyMessage="Свободные боксы не найдены"
          getDisplayValue={(box) => box.display_name}
          renderOption={(box) => (
            <div>
              <div className="font-medium text-gray-900">Бокс {box.box_id}{box.rows && box.cols ? ` (${box.rows}×${box.cols})` : ''}</div>
              <div className="text-sm text-gray-500">Свободно: {box.free_cells} из {box.total_cells} ячеек</div>
            </div>
          )}
        />
      </div>

      <div className="space-y-2">
        <Autocomplete
          value={selectedCellId}
          onChange={setSelectedCellId}
          options={cells}
          placeholder={selectedBoxId ? 'Выберите ячейку...' : 'Сначала выберите бокс'}
          disabled={disabled || !selectedBoxId}
          loading={loadingCells}
          emptyMessage="Свободные ячейки не найдены"
          getDisplayValue={(cell) => `Бокс ${selectedBoxId}, ${cell.display_name}`}
          renderOption={(cell) => (
            <div>
              <div className="font-medium text-gray-900">{cell.display_name}</div>
              <div className="text-sm text-gray-500">Бокс {selectedBoxId}</div>
            </div>
          )}
        />

        {selectedBoxId && !loadingCells && cells.length === 0 && (
          <div className="text-sm text-gray-500">
            В выбранном боксе нет свободных ячеек.
            {existingAllocations?.filter((c) => c.box_id === selectedBoxId).length > 0
              ? ' Есть ранее добавленные ячейки для этого бокса.'
              : ''}
          </div>
        )}
        <div>
          <button
            type="button"
            onClick={handleAddCell}
            disabled={disabled || !selectedBoxId || !selectedCellId}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Добавить ячейку
          </button>
        </div>
      </div>

      {existingAllocations.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Сохранённые ячейки: {existingAllocations.length}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {existingAllocations.map((c) => (
              <span key={c.id} className="inline-flex items-center px-2 py-1 bg-gray-100 rounded-full text-sm">
                Бокс {c.box_id}, {c.cell_id}{c.allocated_at ? ` — добавлено ${new Date(c.allocated_at).toLocaleDateString()}` : ''}
              </span>
            ))}
          </div>
        </div>
      )}

      {assignedCells.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Выбрано: {assignedCells.length}</span>
            <button
              type="button"
              onClick={handleClearAll}
              className="text-sm text-red-600 hover:underline"
            >
              Очистить все
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {assignedCells.map((c) => (
              <span key={c.id} className="inline-flex items-center px-2 py-1 bg-gray-100 rounded-full text-sm">
                Бокс {c.box_id}, {c.cell_id}
                <button
                  type="button"
                  onClick={() => handleRemoveCell(c.id)}
                  className="ml-2 text-gray-500 hover:text-gray-700"
                  aria-label="Удалить ячейку"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-gray-500">
-        Примечание: сохранение нескольких ячеек требует обновления backend. Пока сохраняется только основная ячейка.
+        Примечание: выбранные дополнительные ячейки сохраняются при отправке формы.
      </p>
    </div>
  );
}