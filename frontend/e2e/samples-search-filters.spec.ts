import { test, expect } from '@playwright/test';

test.describe('Samples Search and Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/samples');
    // Ждем загрузки страницы
    await page.waitForSelector('[data-testid="samples-page"]', { timeout: 10000 });
  });

  test('should display search input', async ({ page }) => {
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
  });

  test('should display filter button', async ({ page }) => {
    const filterButton = page.locator('[data-testid="filter-button"]');
    await expect(filterButton).toBeVisible();
  });

  test('should display clear filters button when filters are applied', async ({ page }) => {
    // Вводим текст в поиск
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('test');
    
    // Проверяем, что кнопка очистки появилась
    const clearButton = page.locator('[data-testid="clear-filters-button"]');
    await expect(clearButton).toBeVisible();
  });

  test('should clear search when clear button is clicked', async ({ page }) => {
    // Вводим текст в поиск
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('test search');
    
    // Кликаем кнопку очистки
    const clearButton = page.locator('[data-testid="clear-filters-button"]');
    await clearButton.click();
    
    // Проверяем, что поле поиска очистилось
    await expect(searchInput).toHaveValue('');
  });

  test('should show advanced filters when filter button is clicked', async ({ page }) => {
    const filterButton = page.locator('[data-testid="filter-button"]');
    await filterButton.click();
    
    // Проверяем, что появились дополнительные фильтры
    const advancedFilters = page.locator('[data-testid="advanced-filters"]');
    await expect(advancedFilters).toBeVisible();
  });

  test('should display samples table', async ({ page }) => {
    // Проверяем наличие таблицы образцов
    const table = page.locator('[data-testid="samples-table"]');
    await expect(table).toBeVisible();
    
    // Проверяем заголовки таблицы
    await expect(page.locator('th:has-text("Номер образца")')).toBeVisible();
    await expect(page.locator('th:has-text("Штамм")')).toBeVisible();
    await expect(page.locator('th:has-text("Хранение")')).toBeVisible();
  });

  test('should display pagination', async ({ page }) => {
    // Проверяем наличие пагинации
    const pagination = page.locator('[data-testid="pagination"]');
    await expect(pagination).toBeVisible();
  });
});