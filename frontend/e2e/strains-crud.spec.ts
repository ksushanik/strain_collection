import { test, expect } from '@playwright/test';

test.describe('Strains CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/strains');
  });

  test('should create a new strain', async ({ page }) => {
    // Нажимаем кнопку добавления штамма
    const addButton = page.locator('button:has-text("Добавить штамм")');
    await addButton.click();

    // Ждем появления модального окна или формы
    const modal = page.locator('[role="dialog"]').first();
    if (await modal.isVisible()) {
      // Заполняем форму
      await page.fill('input[name="strain_number"]', 'TEST-E2E-001');
      await page.fill('input[name="species"]', 'Test Species E2E');
      await page.fill('input[name="source"]', 'E2E Test Source');
      
      // Сохраняем
      const saveButton = page.locator('button:has-text("Сохранить")');
      await saveButton.click();
      
      // Ждем закрытия модального окна
      await expect(modal).not.toBeVisible();
      
      // Проверяем, что новый штамм появился в таблице
      await expect(page.locator('table')).toContainText('TEST-E2E-001');
    }
  });

  test('should view strain details', async ({ page }) => {
    // Ищем первую строку в таблице
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      // Кликаем на строку или кнопку просмотра
      const viewButton = firstRow.locator('button:has-text("Просмотр")');
      if (await viewButton.isVisible()) {
        await viewButton.click();
      } else {
        await firstRow.click();
      }
      
      // Ждем появления модального окна с деталями
      const modal = page.locator('[role="dialog"]').first();
      if (await modal.isVisible()) {
        // Проверяем наличие информации о штамме
        await expect(modal).toContainText('Номер штамма');
        await expect(modal).toContainText('Вид');
        await expect(modal).toContainText('Источник');
      }
    }
  });

  test('should edit strain', async ({ page }) => {
    // Ищем первую строку в таблице
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      // Кликаем на кнопку редактирования
      const editButton = firstRow.locator('button:has-text("Редактировать")');
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // Ждем появления формы редактирования
        const modal = page.locator('[role="dialog"]').first();
        if (await modal.isVisible()) {
          // Изменяем данные
          const speciesInput = page.locator('input[name="species"]');
          await speciesInput.clear();
          await speciesInput.fill('Updated Species E2E');
          
          // Сохраняем изменения
          const saveButton = page.locator('button:has-text("Сохранить")');
          await saveButton.click();
          
          // Ждем закрытия модального окна
          await expect(modal).not.toBeVisible();
          
          // Проверяем, что изменения отображаются в таблице
          await expect(page.locator('table')).toContainText('Updated Species E2E');
        }
      }
    }
  });

  test('should delete strain', async ({ page }) => {
    // Ищем строку с тестовым штаммом
    const testRow = page.locator('tr:has-text("TEST-E2E-001")');
    if (await testRow.isVisible()) {
      // Кликаем на кнопку удаления
      const deleteButton = testRow.locator('button:has-text("Удалить")');
      if (await deleteButton.isVisible()) {
        await deleteButton.click();
        
        // Подтверждаем удаление в диалоге
        const confirmDialog = page.locator('[role="dialog"]:has-text("Подтвердить удаление")');
        if (await confirmDialog.isVisible()) {
          const confirmButton = confirmDialog.locator('button:has-text("Удалить")');
          await confirmButton.click();
          
          // Ждем закрытия диалога
          await expect(confirmDialog).not.toBeVisible();
          
          // Проверяем, что штамм удален из таблицы
          await expect(page.locator('table')).not.toContainText('TEST-E2E-001');
        }
      }
    }
  });

  test('should handle validation errors', async ({ page }) => {
    // Нажимаем кнопку добавления штамма
    const addButton = page.locator('button:has-text("Добавить штамм")');
    await addButton.click();

    // Ждем появления модального окна
    const modal = page.locator('[role="dialog"]').first();
    if (await modal.isVisible()) {
      // Пытаемся сохранить без заполнения обязательных полей
      const saveButton = page.locator('button:has-text("Сохранить")');
      await saveButton.click();
      
      // Проверяем появление ошибок валидации
      const errorMessages = page.locator('.error, .text-red-500, [role="alert"]');
      await expect(errorMessages.first()).toBeVisible();
      
      // Закрываем модальное окно
      const cancelButton = page.locator('button:has-text("Отмена")');
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
      }
    }
  });

  test('should export strains', async ({ page }) => {
    // Ищем кнопку экспорта
    const exportButton = page.locator('button:has-text("Экспорт")');
    if (await exportButton.isVisible()) {
      // Настраиваем обработчик загрузки файла
      const downloadPromise = page.waitForEvent('download');
      
      await exportButton.click();
      
      // Ждем начала загрузки
      const download = await downloadPromise;
      
      // Проверяем, что файл загружается
      expect(download.suggestedFilename()).toMatch(/strains.*\.(csv|xlsx)$/);
    }
  });
});