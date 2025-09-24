import { test, expect } from '@playwright/test';

test.describe('Basic Navigation', () => {
  test('should navigate to main pages', async ({ page }) => {
    // Переходим на главную страницу
    await page.goto('/');
    
    // Проверяем, что загрузилась главная страница
    await expect(page).toHaveTitle(/Strain Collection/);
    
    // Проверяем наличие навигации
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();
    
    // Переходим на страницу штаммов
    await page.click('a[href="/strains"]');
    await expect(page).toHaveURL('/strains');
    await expect(page.locator('h1')).toContainText('Штаммы');
    
    // Переходим на страницу образцов
    await page.click('a[href="/samples"]');
    await expect(page).toHaveURL('/samples');
    await expect(page.locator('h1')).toContainText('Образцы');
    
    // Возвращаемся на главную
    await page.click('a[href="/"]');
    await expect(page).toHaveURL('/');
  });

  test('should display strains table', async ({ page }) => {
    await page.goto('/strains');
    
    // Ждем загрузки таблицы
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    // Проверяем заголовки таблицы
    await expect(page.locator('th')).toContainText(['Номер штамма', 'Вид', 'Источник']);
    
    // Проверяем наличие кнопки добавления
    const addButton = page.locator('button:has-text("Добавить штамм")');
    await expect(addButton).toBeVisible();
  });

  test('should display samples table', async ({ page }) => {
    await page.goto('/samples');
    
    // Ждем загрузки таблицы
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    // Проверяем заголовки таблицы
    await expect(page.locator('th')).toContainText(['Номер образца', 'Штамм', 'Цвет ИУК']);
    
    // Проверяем наличие кнопки добавления
    const addButton = page.locator('button:has-text("Добавить образец")');
    await expect(addButton).toBeVisible();
  });

  test('should handle search functionality', async ({ page }) => {
    await page.goto('/strains');
    
    // Ищем поле поиска
    const searchInput = page.locator('input[placeholder*="поиск" i]');
    if (await searchInput.isVisible()) {
      // Вводим поисковый запрос
      await searchInput.fill('test');
      
      // Ждем обновления результатов
      await page.waitForTimeout(500);
      
      // Проверяем, что таблица все еще видна
      const table = page.locator('table');
      await expect(table).toBeVisible();
    }
  });

  test('should handle pagination', async ({ page }) => {
    await page.goto('/strains');
    
    // Ищем элементы пагинации
    const pagination = page.locator('[role="navigation"]').last();
    if (await pagination.isVisible()) {
      // Проверяем наличие кнопок навигации
      const nextButton = page.locator('button:has-text("Следующая")');
      const prevButton = page.locator('button:has-text("Предыдущая")');
      
      // Если есть кнопка "Следующая", проверяем ее работу
      if (await nextButton.isVisible() && await nextButton.isEnabled()) {
        await nextButton.click();
        await page.waitForTimeout(500);
        
        // Проверяем, что таблица все еще видна
        const table = page.locator('table');
        await expect(table).toBeVisible();
      }
    }
  });
});