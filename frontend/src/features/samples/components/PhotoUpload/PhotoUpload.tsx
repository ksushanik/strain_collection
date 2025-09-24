import React from 'react';
import { X, Upload } from 'lucide-react';

interface PhotoUploadProps {
  photos: File[];
  onChange: (photos: File[]) => void;
  disabled?: boolean;
  maxFiles?: number;
  maxSizeBytes?: number;
}

export const PhotoUpload: React.FC<PhotoUploadProps> = ({
  photos,
  onChange,
  disabled = false,
  maxFiles = 10,
  maxSizeBytes = 1024 * 1024 // 1MB
}) => {
  const handleFileSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Фильтрация файлов по размеру
    const validFiles = files.filter(file => {
      if (file.size > maxSizeBytes) {
        alert(`Файл ${file.name} слишком большой. Максимальный размер: ${maxSizeBytes / (1024 * 1024)}MB`);
        return false;
      }
      return true;
    });

    // Ограничение количества файлов
    const newPhotos = [...photos, ...validFiles].slice(0, maxFiles);
    onChange(newPhotos);
    
    // Очистка input для возможности повторного выбора того же файла
    e.target.value = '';
  };

  const removePhoto = (index: number) => {
    const newPhotos = photos.filter((_, i) => i !== index);
    onChange(newPhotos);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Фотографии (JPEG/PNG, ≤{formatFileSize(maxSizeBytes)})
        </label>
        
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg border border-blue-200 hover:bg-blue-100 cursor-pointer transition-colors">
            <Upload className="w-4 h-4" />
            <span className="text-sm font-medium">Выбрать фото</span>
            <input
              type="file"
              multiple
              accept="image/jpeg,image/png"
              onChange={handleFileSelection}
              className="hidden"
              disabled={disabled || photos.length >= maxFiles}
            />
          </label>
          
          {photos.length > 0 && (
            <span className="text-sm text-gray-500">
              {photos.length} из {maxFiles} файлов
            </span>
          )}
        </div>
      </div>

      {/* Превью фотографий */}
      {photos.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {photos.map((file, index) => (
            <div key={`${file.name}-${file.size}-${index}`} className="relative group">
              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Preview ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
              
              {/* Кнопка удаления */}
              <button
                type="button"
                onClick={() => removePhoto(index)}
                className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                disabled={disabled}
              >
                <X className="w-3 h-3" />
              </button>
              
              {/* Информация о файле */}
              <div className="mt-1 text-xs text-gray-500 truncate">
                <div className="font-medium">{file.name}</div>
                <div>{formatFileSize(file.size)}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Подсказка */}
      {photos.length === 0 && (
        <div className="text-sm text-gray-500 bg-gray-50 rounded-lg p-4 border-2 border-dashed border-gray-200">
          <div className="text-center">
            <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p>Нажмите "Выбрать фото" чтобы добавить изображения</p>
            <p className="text-xs mt-1">
              Поддерживаются форматы JPEG и PNG, максимальный размер {formatFileSize(maxSizeBytes)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};