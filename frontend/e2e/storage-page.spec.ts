import { test, expect } from '@playwright/test';

const storageOverviewPayload = {
  boxes: [
    {
      box_id: 'BOX-08',
      rows: 9,
      cols: 9,
      description: 'Тестовый бокс',
      occupied: 78,
      free_cells: 3,
      total_cells: 81,
      cells: [],
    },
    {
      box_id: 'BOX-10',
      rows: 10,
      cols: 10,
      description: 'Запасной бокс',
      occupied: 20,
      free_cells: 80,
      total_cells: 100,
      cells: [],
    },
  ],
  total_boxes: 2,
  total_cells: 181,
  occupied_cells: 98,
  free_cells: 83,
};

const buildBox08Detail = () => {
  const freeCells = new Set(['I7', 'I8', 'I9']);
  let storageId = 1;

  const grid = Array.from({ length: 9 }, (_, rowIndex) => {
    const rowLabel = String.fromCharCode('A'.charCodeAt(0) + rowIndex);
    return Array.from({ length: 9 }, (_, colIndex) => {
      const colNumber = colIndex + 1;
      const cellId = `${rowLabel}${colNumber}`;
      const isFree = freeCells.has(cellId);
      const cell = {
        row: rowIndex + 1,
        col: colNumber,
        cell_id: cellId,
        storage_id: storageId++,
        is_occupied: !isFree,
        sample_info: isFree
          ? null
          : {
              sample_id: 1000 + storageId,
              strain_id: 500 + storageId,
              strain_number: `STR-${cellId}`,
              comment: null,
              total_samples: 1,
            },
        total_samples: isFree ? 0 : 1,
      };
      return cell;
    });
  });

  return {
    box_id: 'BOX-08',
    rows: 9,
    cols: 9,
    description: 'Тестовый бокс',
    total_cells: 81,
    occupied_cells: 78,
    free_cells: 3,
    occupancy_percentage: 96.3,
    cells_grid: grid,
  };
};

test.describe('Storage Page', () => {
  test('renders snapshot summary and loads box details', async ({ page }) => {
    const detailPayload = buildBox08Detail();

    await page.route('**/api/storage/', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(storageOverviewPayload),
        });
        return;
      }
      await route.continue();
    });

    await page.route('**/api/storage/boxes/BOX-08/detail/', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(detailPayload),
        });
        return;
      }
      await route.continue();
    });

    await page.goto('/storage');

    await expect(page.getByTestId('storage-summary-total-boxes')).toHaveText('2');
    await expect(page.getByTestId('storage-summary-total-cells')).toHaveText('181');
    await expect(page.getByTestId('storage-summary-occupied-cells')).toHaveText('98');
    await expect(page.getByTestId('storage-summary-occupancy')).toHaveText('54.1%');

    const firstBox = page
      .getByTestId('storage-box-card')
      .filter({ has: page.locator('text=BOX-08') })
      .first();

    await expect(firstBox.getByTestId('storage-box-occupied')).toHaveText('78');
    await expect(firstBox.getByTestId('storage-box-free')).toHaveText('3');

    await firstBox.getByTestId('storage-box-expand').click();
    await page.waitForResponse((response) =>
      response.url().includes('/api/storage/boxes/BOX-08/detail/') && response.status() === 200,
    );

    await expect(firstBox.getByTestId('storage-box-free')).toHaveText('3');
    await expect(firstBox.locator('text=I7')).toBeVisible();
    await expect(firstBox.locator('text=I8')).toBeVisible();
    await expect(firstBox.locator('text=I9')).toBeVisible();
  });
});
