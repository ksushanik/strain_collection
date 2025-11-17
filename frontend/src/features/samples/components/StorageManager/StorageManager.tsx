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

export interface StorageCell {
  id: number; // storage cell id
  cell_id: string;
  box_id: string;
  display_name?: string;
  is_primary?: boolean;
  allocated_at?: string | null;
  is_new?: boolean; // для отслеживания новых ячеек
}

interface StorageManagerProps {
  disabled?: boolean;
  value?: StorageCell[];
  onChange?: (cells: StorageCell[]) => void;
  existingAllocations?: StorageCell[];
  allowEmpty?: boolean;
  minCells?: number;
  required?: boolean; // обязательность заполнения
  refreshKey?: number | string;
}

// Компонент для управления всеми ячейками хранения образца
export const StorageManager: React.FC<StorageManagerProps> = ({
  disabled = false,
  value = [],
  onChange,
  existingAllocations = [],
  allowEmpty = false,
  minCells = 1,
  refreshKey,
}) => {
  const [boxes, setBoxes] = useState<BoxOption[]>([]);
  const [cells, setCells] = useState<CellOption[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | undefined>(undefined);
  const [selectedCellId, setSelectedCellId] = useState<number | undefined>(undefined);
  const [loadingBoxes, setLoadingBoxes] = useState(false);
  const [loadingCells, setLoadingCells] = useState(false);
  const [editingCellId, setEditingCellId] = useState<number | null>(null);
  const [editingBoxId, setEditingBoxId] = useState<string>('');
  const [editingNewCellId, setEditingNewCellId] = useState<number | undefined>(undefined);
  
  // Правильная инициализация с использованием lazy initialization
  const normalizeCells = useCallback((cells: StorageCell[]): StorageCell[] => {
    return cells.map((cell, index) => ({
      ...cell,
      display_name: cell.display_name ?? cell.cell_id,
      is_primary: index === 0,
    }));
  }, []);

  const [storageCells, setStorageCells] = useState<StorageCell[]>(() => {
    const initialCells: StorageCell[] = [];

    if (value && value.length > 0) {
      initialCells.push(...value);
    } else if (existingAllocations && existingAllocations.length > 0) {
      initialCells.push(...existingAllocations);
    }

    return normalizeCells(initialCells);
  });

  // Синхронизируем локальное состояние с переданным значением
  useEffect(() => {
    if (value === undefined) {
      return;
    }
    setStorageCells((prev) => {
      if (prev === value) {
        return prev;
      }
      return normalizeCells(value);
    });
  }, [value, normalizeCells]);

  const emitChange = useCallback((cells: StorageCell[]) => {
    const normalized = normalizeCells(cells);
    setStorageCells(normalized);
    onChange?.(normalized);
  }, [normalizeCells, onChange]);
  
  // Загрузка боксов
  const loadBoxes = useCallback(async (searchTerm: string = '') => {
    setLoadingBoxes(true);
    try {
      const response = await apiService.getFreeBoxes(searchTerm, 50);
      const formattedBoxes: BoxOption[] = response.boxes.map((boxSummary: StorageBoxSummary) => {
        const totalCells = boxSummary.total_cells;
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

      setBoxes(formattedBoxes);
    } catch (error) {
      console.error('Ошибка при загрузке боксов:', error);
      setBoxes([]);
    } finally {
      setLoadingBoxes(false);
    }
  }, []);

  // Загрузка ячеек для выбранного бокса
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

      setCells(formattedCells);
    } catch (error) {
      console.error('Ошибка при загрузке ячеек:', error);
      setCells([]);
    } finally {
      setLoadingCells(false);
    }
  }, [boxes]);

  // Загрузка боксов при монтировании
  useEffect(() => {
    loadBoxes();
  }, [loadBoxes]);

  // Загрузка ячеек при изменении выбранного бокса
  useEffect(() => {
    if (selectedBoxId) {
      loadCells(selectedBoxId);
    } else {
      setCells([]);
      setSelectedCellId(undefined);
    }
  }, [selectedBoxId, loadCells]);

  useEffect(() => {
    if (refreshKey !== undefined) {
      loadBoxes();
      if (selectedBoxId) {
        loadCells(selectedBoxId);
      }
    }
  }, [refreshKey, loadBoxes, loadCells, selectedBoxId]);

  // Добавление новой ячейки
  const addCell = useCallback(() => {
    if (!selectedBoxId || !selectedCellId) return;

    const selectedCell = cells.find(cell => cell.id === selectedCellId);
    if (!selectedCell) return;

    // Проверяем, что ячейка еще не добавлена
    if (storageCells.some(cell => cell.id === selectedCellId)) {
      alert('Эта ячейка уже добавлена');
      return;
    }

    const newCell: StorageCell = {
      id: selectedCell.id,
      cell_id: selectedCell.cell_id,
      box_id: selectedBoxId,
      display_name: selectedCell.display_name ?? selectedCell.cell_id,
      is_primary: storageCells.length === 0,
      is_new: true,
    };

    const updatedCells = [...storageCells, newCell];
    emitChange(updatedCells);

    // Сбрасываем выбор
    setSelectedBoxId(undefined);
    setSelectedCellId(undefined);
  }, [selectedBoxId, selectedCellId, cells, storageCells, emitChange]);

  // Удаление ячейки
  const removeCell = useCallback((cellId: number) => {
    const updatedCells = storageCells.filter(cell => cell.id !== cellId);
    emitChange(updatedCells);
  }, [storageCells, emitChange]);

  // Начало редактирования ячейки
  const startEditCell = useCallback((cellId: number) => {
    const cell = storageCells.find(c => c.id === cellId);
    if (!cell) return;

    setEditingCellId(cellId);
    setEditingBoxId(cell.box_id);
    setEditingNewCellId(cell.id);

    // Загружаем ячейки для текущего бокса
    loadCells(cell.box_id);
  }, [storageCells, loadCells]);

  // Сохранение изменений ячейки
  const saveEditCell = useCallback(() => {
    if (!editingCellId || !editingBoxId || !editingNewCellId) return;

    let newCell = cells.find(cell => cell.id === editingNewCellId);
    if (!newCell) {
      const existingCell = storageCells.find(cell => cell.id === editingNewCellId);
      if (!existingCell) {
        return;
      }
      newCell = {
        id: existingCell.id,
        cell_id: existingCell.cell_id,
        display_name: existingCell.display_name ?? existingCell.cell_id,
      };
    }

    // Проверяем, что новая ячейка не занята другой записью
    if (storageCells.some(cell => cell.id === editingNewCellId && cell.id !== editingCellId)) {
      alert('Эта ячейка уже используется');
      return;
    }

    const updatedCells = storageCells.map(cell =>
      cell.id === editingCellId
        ? {
            ...cell,
            id: newCell.id,
            cell_id: newCell.cell_id,
            box_id: editingBoxId,
            display_name: newCell.display_name ?? newCell.cell_id,
          }
        : cell
    );

    emitChange(updatedCells);

    // Сбрасываем режим редактирования
    setEditingCellId(null);
    setEditingBoxId('');
    setEditingNewCellId(undefined);
  }, [editingCellId, editingBoxId, editingNewCellId, cells, storageCells, emitChange]);

  // Отмена редактирования
  const cancelEdit = useCallback(() => {
    setEditingCellId(null);
    setEditingBoxId('');
    setEditingNewCellId(undefined);
  }, []);

  const canRemoveCell = () => {
    // Можно удалить если это не единственная ячейка (при minCells > 0) или разрешен пустой список
    return allowEmpty || storageCells.length > minCells;
  };

  // Мемоизируем getDisplayValue функции для предотвращения бесконечного ре-рендера
  const getBoxDisplayValue = useCallback((box: BoxOption) => {
    return box.display_name;
  }, []);
  
  const getCellDisplayValue = useCallback((cell: CellOption) => {
    return cell.display_name;
  }, []);
  
  const getCellOptionDisplayValue = useCallback((cellOption: CellOption) => {
    return cellOption.display_name;
  }, []);

  return (
    <div className="space-y-4">
      {/* Добавление новой ячейки */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Добавить ячейку хранения</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Выбор бокса */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Бокс</label>
            <Autocomplete<BoxOption>
              value={selectedBoxId}
              onChange={(value) => setSelectedBoxId(value as string | undefined)}
              options={boxes}
              onSearch={loadBoxes}
              placeholder="Выберите бокс..."
              disabled={disabled}
              loading={loadingBoxes}
              emptyMessage="Боксы не найдены"
              getDisplayValue={getBoxDisplayValue}
              renderOption={(box) => (
                <div>
                  <div className="font-medium text-gray-900">{box.display_name}</div>
                  <div className="text-sm text-gray-500">
                    Свободно: {box.free_cells} из {box.total_cells} ячеек
                  </div>
                </div>
              )}
            />
          </div>

          {/* Выбор ячейки */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ячейка</label>
            <Autocomplete<CellOption>
              value={selectedCellId}
              onChange={(value) => setSelectedCellId(value as number | undefined)}
              options={cells}
              placeholder={selectedBoxId ? "Выберите ячейку..." : "Сначала выберите бокс"}
              disabled={disabled || !selectedBoxId}
              loading={loadingCells}
              emptyMessage="Ячейки не найдены"
              getDisplayValue={getCellDisplayValue}
              renderOption={(cell) => (
                <div>
                  <div className="font-medium text-gray-900">{cell.display_name}</div>
                </div>
              )}
            />
          </div>

          {/* Кнопка добавления */}
          <div className="flex items-end">
            <button
              type="button"
              onClick={addCell}
              disabled={disabled || !selectedBoxId || !selectedCellId}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Добавить
            </button>
          </div>
        </div>
      </div>

      {/* Список выбранных ячеек */}
      {storageCells.length > 0 && (
        <div className="border rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Выбранные ячейки хранения ({storageCells.length})
          </h3>
          
          <div className="space-y-2">
            {storageCells.map((cell) => (
              <div
                key={cell.id}
                className="flex items-center justify-between p-3 border rounded-md bg-white border-gray-200"
              >
                <div className="flex-1">
                  {editingCellId === cell.id ? (
                    // Режим редактирования
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <Autocomplete<BoxOption>
                        value={editingBoxId}
                        onChange={(value) => {
                          const boxValue = value as string;
                          setEditingBoxId(boxValue);
                          setEditingNewCellId(undefined);
                          if (boxValue) {
                            loadCells(boxValue);
                          }
                        }}
                        options={boxes}
                        onSearch={loadBoxes}
                        placeholder="Выберите бокс..."
                        disabled={disabled}
                        loading={loadingBoxes}
                        emptyMessage="Боксы не найдены"
                        getDisplayValue={getBoxDisplayValue}
                      />
                      <Autocomplete<CellOption>
                        value={editingNewCellId}
                        onChange={(value) => setEditingNewCellId(value as number | undefined)}
                        options={
                          editingBoxId === cell.box_id
                            ? [
                                {
                                  id: cell.id,
                                  display_name: cell.display_name ?? cell.cell_id,
                                  cell_id: cell.cell_id,
                                },
                                ...cells.filter((option) => option.id !== cell.id),
                              ]
                            : cells
                        }
                        placeholder="Выберите ячейку..."
                        disabled={disabled || !editingBoxId}
                        loading={loadingCells}
                        emptyMessage="Ячейки не найдены"
                        getDisplayValue={getCellOptionDisplayValue}
                      />
                    </div>
                  ) : (
                    // Обычный режим
                    <div>
                      <div className="font-medium text-gray-900">
                        Бокс {cell.box_id}, ячейка {cell.cell_id}
                        {cell.is_new && (
                          <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            Новая
                          </span>
                        )}
                      </div>
                      {cell.allocated_at && (
                        <div className="text-sm text-gray-500">
                          Добавлена: {new Date(cell.allocated_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  {editingCellId === cell.id ? (
                    // Кнопки сохранения/отмены
                    <>
                      <button
                        type="button"
                        onClick={saveEditCell}
                        disabled={!editingBoxId || !editingNewCellId}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300"
                      >
                        Сохранить
                      </button>
                      <button
                        type="button"
                        onClick={cancelEdit}
                        className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                      >
                        Отмена
                      </button>
                    </>
                  ) : (
                    // Обычные кнопки
                    <>
                      <button
                        type="button"
                        onClick={() => startEditCell(cell.id)}
                        disabled={disabled}
                        className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:bg-gray-300"
                        title="Редактировать"
                      >
                        Изменить
                      </button>
                      {canRemoveCell() && (
                        <button
                          type="button"
                          onClick={() => removeCell(cell.id)}
                          disabled={disabled}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-300"
                          title="Удалить"
                        >
                          Удалить
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Сообщение о пустом списке */}
      {storageCells.length === 0 && !allowEmpty && (
        <div className="text-center py-8 text-gray-500">
          <p>Добавьте хотя бы одну ячейку хранения</p>
        </div>
      )}
    </div>
  );
};
