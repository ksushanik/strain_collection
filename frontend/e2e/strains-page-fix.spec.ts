import { test, expect } from '@playwright/test';

test.describe('Strains Page TypeError Fix', () => {
  test('should not have TypeError when loading strains page', async ({ page }) => {
    const jsErrors: Error[] = [];
    const consoleErrors: string[] = [];
    
    // Перехватываем JavaScript ошибки
    page.on('pageerror', error => {
      jsErrors.push(error);
      console.log('JS Error:', error.message);
    });
    
    // Перехватываем консольные ошибки
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log('Console Error:', msg.text());
      }
    });

    // Переходим на страницу штаммов
    await page.goto('/strains');
    
    // Ждем загрузки страницы
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(5000); // Даем время для полной загрузки React

    // Основная проверка: нет TypeError связанных с length или undefined
    const lengthTypeErrors = jsErrors.filter(error => 
      error.message.includes('TypeError') && 
      (error.message.includes('length') || 
       error.message.includes('undefined') ||
       error.message.includes('Cannot read properties'))
    );
    
    // Выводим найденные ошибки для отладки
    if (lengthTypeErrors.length > 0) {
      console.log('Found TypeError errors:', lengthTypeErrors.map(e => e.message));
    }
    
    expect(lengthTypeErrors).toHaveLength(0);

    // Проверяем консольные ошибки
    const lengthConsoleErrors = consoleErrors.filter(error => 
      error.includes('TypeError') && 
      (error.includes('length') || 
       error.includes('undefined') ||
       error.includes('Cannot read properties'))
    );
    
    if (lengthConsoleErrors.length > 0) {
      console.log('Found console errors:', lengthConsoleErrors);
    }
    
    expect(lengthConsoleErrors).toHaveLength(0);
  });

  test('should load page without critical errors', async ({ page }) => {
    const criticalErrors: string[] = [];
    
    page.on('pageerror', error => {
      criticalErrors.push(error.message);
    });

    await page.goto('/strains');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Проверяем, что страница загрузилась (есть какой-то контент)
    const bodyContent = await page.textContent('body');
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(0);

    // Проверяем отсутствие критических ошибок
    const typeErrorsCount = criticalErrors.filter(error => 
      error.includes('TypeError')
    ).length;
    
    expect(typeErrorsCount).toBe(0);
  });
});