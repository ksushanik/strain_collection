import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Trash2, 
  Beaker, 
  Microscope, 
  MapPin, 
  Info, 
  CheckCircle, 
  Calendar, 
  Camera, 
  Loader2,
  ChevronUp,
  ChevronDown,
  MessageSquare,
  ZoomIn,
  X,
  // Новые иконки для характеристик
  Eye,
  Dna,
  FlaskConical,
  TestTube,
  Zap,
  Palette,
  Sparkles
} from 'lucide-react';
import apiService from '../services/api';
import type { Sample } from '../types';
import { API_BASE_URL } from '../config/api';

const SampleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [sample, setSample] = useState<Sample | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState({
    characteristics: true,
    photos: true,
    comments: true
  });



  useEffect(() => {
    if (!id) return;

    const fetchSampleDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getSample(parseInt(id));
        setSample(data);
      } catch (err: any) {
        console.error('Ошибка загрузки образца:', err);
        setError(err.response?.data?.error || err.message || 'Ошибка загрузки образца');
      } finally {
        setLoading(false);
      }
    };

    fetchSampleDetails();
  }, [id]);

  const handleDeleteSample = async () => {
    if (!sample) return;
    
    setIsDeleting(true);
    try {
      await apiService.deleteSample(sample.id);
      navigate('/samples');
    } catch (err: any) {
      setError(err.message || 'Ошибка при удалении образца');
      console.error('Error deleting sample:', err);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handlePhotoDelete = async (photoId: number) => {
    try {
      await apiService.deleteSamplePhoto(sample!.id, photoId);
      setSample(prev => prev ? { ...prev, photos: prev.photos?.filter(p => p.id !== photoId) } : prev);
    } catch (err) {
      console.error('Ошибка удаления фото', err);
      alert('Ошибка удаления фото');
    }
  };

  // Функция для получения имени файла из пути
  const getFileName = (imagePath: string): string => {
    const parts = imagePath.split('/');
    const fileName = parts[parts.length - 1];
    
    // Django добавляет хеш к именам файлов в формате: originalname_hash.extension
    // Пытаемся восстановить оригинальное имя
    const hashPattern = /_[a-zA-Z0-9]{7,}\.([a-zA-Z0-9]+)$/;
    if (hashPattern.test(fileName)) {
      // Убираем хеш, оставляя оригинальное имя и расширение
      const nameWithoutHash = fileName.replace(hashPattern, '.$1');
      return nameWithoutHash;
    }
    
    // Если паттерн не найден, возвращаем имя как есть
    return fileName;
  };

  // Функция для получения полного URL изображения
  const getImageUrl = (imagePath: string): string => {
    return `${API_BASE_URL}${imagePath}`;
  };

  const handlePhotoUpload = async () => {
    if (!sample || uploadFiles.length === 0) return;
    try {
      await apiService.uploadSamplePhotos(sample.id, uploadFiles);
      // reload sample
      const updated = await apiService.getSample(sample.id);
      setSample(updated);
      setUploadFiles([]);
      setShowUpload(false);
    } catch (err) {
      console.error('Ошибка загрузки фото', err);
      alert('Ошибка загрузки фото');
    }
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getCharacteristicsBadges = (sample: Sample) => {
    const badges = [];

    // Фотография
    if (sample.has_photo) badges.push({
      icon: Camera,
      label: 'Фото',
      color: 'green',
      description: 'Есть фотография образца'
    });

    // Основные характеристики
    if (sample.is_identified) badges.push({
      icon: Eye,
      label: 'Идентифицирован',
      color: 'blue',
      description: 'Образец идентифицирован'
    });
    if (sample.has_antibiotic_activity) badges.push({
      icon: TestTube,
      label: 'АБ активность',
      color: 'purple',
      description: 'Антибиотическая активность'
    });
    if (sample.has_genome) badges.push({
      icon: Dna,
      label: 'Геном',
      color: 'red',
      description: 'Геном секвенирован'
    });
    if (sample.has_biochemistry) badges.push({
      icon: FlaskConical,
      label: 'Биохимия',
      color: 'yellow',
      description: 'Биохимический анализ'
    });
    if (sample.seq_status) badges.push({
      icon: Microscope,
      label: 'Секвенирование',
      color: 'indigo',
      description: 'Выполнено секвенирование'
    });

    // Новые характеристики
    if (sample.mobilizes_phosphates) badges.push({
      icon: Zap,
      label: 'Фосфаты',
      color: 'orange',
      description: 'Мобилизует фосфаты'
    });
    if (sample.stains_medium) badges.push({
      icon: Palette,
      label: 'Окрашивание',
      color: 'pink',
      description: 'Окрашивает среду'
    });
    if (sample.produces_siderophores) badges.push({
      icon: Sparkles,
      label: 'Сидерофоры',
      color: 'cyan',
      description: 'Вырабатывает сидерофоры'
    });

    return badges;
  };



  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-gray-600">Загрузка образца...</span>
        </div>
      </div>
    );
  }

  if (error || !sample) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error || 'Образец не найден'}</p>
        <button 
          onClick={() => navigate('/samples')}
          className="mt-2 text-blue-600 hover:text-blue-800"
        >
          ← Вернуться к списку образцов
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Компактный Header */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/samples')}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Образец #{sample.id}
            </h1>
            {sample.original_sample_number && (
              <p className="text-sm text-gray-600">
                {sample.original_sample_number}
              </p>
            )}
          </div>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={() => navigate(`/samples/${sample.id}/edit`)}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center text-sm"
          >
            <Edit className="w-4 h-4 mr-1" />
            Редактировать
          </button>
          <button 
            onClick={() => setShowDeleteConfirm(true)}
            className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center text-sm"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            Удалить
          </button>
        </div>
      </div>

      {/* Основная информация об образце */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Info className="w-5 h-5 text-blue-600 mr-2" />
            Основная информация
          </h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-sm">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">ID</label>
            <p className="font-semibold text-gray-900">#{sample.id}</p>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Номер образца</label>
            <p className="text-gray-900">{sample.original_sample_number || 'Не указан'}</p>
          </div>

          {sample.index_letter && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Индекс</label>
              <p className="text-gray-900">{sample.index_letter.letter_value}</p>
            </div>
          )}

          {sample.strain && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Штамм</label>
              <button
                onClick={() => navigate(`/strains/${sample.strain?.id}`)}
                className="text-blue-600 hover:text-blue-800 font-medium underline decoration-dotted underline-offset-2 hover:decoration-solid transition-all duration-200"
                title={`Перейти к штамму: ${sample.strain?.identifier}`}
              >
                {sample.strain?.short_code}
              </button>
            </div>
          )}

          {sample.source && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <Microscope className="w-3 h-3 mr-1" />
                Источник
              </label>
              <p className="text-gray-900 font-medium">{sample.source.organism_name}</p>
              {sample.source.source_type && (
                <p className="text-xs text-gray-500 mt-1">{sample.source.source_type}</p>
              )}
            </div>
          )}

          {sample.location && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <MapPin className="w-3 h-3 mr-1" />
                Локация
              </label>
              <p className="text-gray-900 font-medium">{sample.location.name}</p>
            </div>
          )}

          {sample.storage && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <Beaker className="w-3 h-3 mr-1" />
                Хранение
              </label>
              <div className="bg-gray-100 px-2 py-1 rounded text-xs font-mono font-semibold text-gray-800">
                {sample.storage.box_id}-{sample.storage.cell_id}
              </div>
            </div>
          )}

          {/* Новые поля из формы редактирования */}
          {sample.iuk_color && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <Palette className="w-3 h-3 mr-1" />
                IUK цвет
              </label>
              <div className="flex items-center space-x-2">
                <div 
                  className="w-4 h-4 rounded-full border border-gray-300"
                  style={{ backgroundColor: sample.iuk_color.hex_code }}
                  title={sample.iuk_color.hex_code}
                ></div>
                <p className="text-gray-900 font-medium">{sample.iuk_color.name}</p>
              </div>
            </div>
          )}

          {sample.amylase_variant && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <FlaskConical className="w-3 h-3 mr-1" />
                Амилаза
              </label>
              <p className="text-gray-900 font-medium">{sample.amylase_variant.name}</p>
              {sample.amylase_variant.description && (
                <p className="text-xs text-gray-500 mt-1">{sample.amylase_variant.description}</p>
              )}
            </div>
          )}

          {sample.growth_media && sample.growth_media.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <FlaskConical className="w-3 h-3 mr-1" />
                Среды роста
              </label>
              <div className="flex flex-wrap gap-1">
                {sample.growth_media.map((media, index) => (
                  <span 
                    key={index}
                    className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium"
                  >
                    {media.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Компактные характеристики */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            Характеристики
          </h3>
          <button
            onClick={() => toggleSection('characteristics')}
            className="p-1 rounded hover:bg-gray-100"
          >
            {expandedSections.characteristics ? 
              <ChevronUp className="w-4 h-4" /> : 
              <ChevronDown className="w-4 h-4" />
            }
          </button>
        </div>
        
        {expandedSections.characteristics && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {getCharacteristicsBadges(sample).map(({ icon: Icon, label, color, description }, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  color === 'green' ? 'border-green-200 bg-green-50' :
                  color === 'blue' ? 'border-blue-200 bg-blue-50' :
                  color === 'purple' ? 'border-purple-200 bg-purple-50' :
                  color === 'red' ? 'border-red-200 bg-red-50' :
                  color === 'yellow' ? 'border-yellow-200 bg-yellow-50' :
                  color === 'orange' ? 'border-orange-200 bg-orange-50' :
                  color === 'pink' ? 'border-pink-200 bg-pink-50' :
                  color === 'cyan' ? 'border-cyan-200 bg-cyan-50' :
                  'border-indigo-200 bg-indigo-50'
                }`}
                title={description}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`w-4 h-4 ${
                    color === 'green' ? 'text-green-600' :
                    color === 'blue' ? 'text-blue-600' :
                    color === 'purple' ? 'text-purple-600' :
                    color === 'red' ? 'text-red-600' :
                    color === 'yellow' ? 'text-yellow-600' :
                    color === 'orange' ? 'text-orange-600' :
                    color === 'pink' ? 'text-pink-600' :
                    color === 'cyan' ? 'text-cyan-600' :
                    'text-indigo-600'
                  }`} />
                  <span className={`text-sm font-medium ${
                    color === 'green' ? 'text-green-800' :
                    color === 'blue' ? 'text-blue-800' :
                    color === 'purple' ? 'text-purple-800' :
                    color === 'red' ? 'text-red-800' :
                    color === 'yellow' ? 'text-yellow-800' :
                    color === 'orange' ? 'text-orange-800' :
                    color === 'pink' ? 'text-pink-800' :
                    color === 'cyan' ? 'text-cyan-800' :
                    'text-indigo-800'
                  }`}>{label}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Компактная галерея фотографий с превью */}
      {sample.photos && sample.photos.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Camera className="w-5 h-5 text-blue-600 mr-2" />
              Фотографии ({sample.photos.length})
            </h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowUpload(true)}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Добавить
              </button>
              <button
                onClick={() => toggleSection('photos')}
                className="p-1 rounded hover:bg-gray-100"
              >
                {expandedSections.photos ? 
                  <ChevronUp className="w-4 h-4" /> : 
                  <ChevronDown className="w-4 h-4" />
                }
              </button>
            </div>
          </div>
          
          {expandedSections.photos && (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
              {sample.photos.map(photo => (
                <div key={photo.id} className="relative group">
                  <div className="relative">
                    <img 
                      src={getImageUrl(photo.image)} 
                      alt={getFileName(photo.image)} 
                      className="w-full h-20 object-cover rounded cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => setSelectedPhoto(getImageUrl(photo.image))}
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-1 rounded-b truncate">
                      {getFileName(photo.image)}
                    </div>
                  </div>
                  <button 
                    onClick={() => handlePhotoDelete(photo.id)} 
                    className="absolute top-1 right-1 bg-red-500 bg-opacity-80 hover:bg-opacity-100 text-white p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                  <button 
                    onClick={() => setSelectedPhoto(getImageUrl(photo.image))} 
                    className="absolute top-1 left-1 bg-blue-500 bg-opacity-80 hover:bg-opacity-100 text-white p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <ZoomIn className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Комментарии и заметки */}
      {(sample.comment || sample.appendix_note) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <MessageSquare className="w-5 h-5 text-gray-600 mr-2" />
              Комментарии
            </h3>
            <button
              onClick={() => toggleSection('comments')}
              className="p-1 rounded hover:bg-gray-100"
            >
              {expandedSections.comments ? 
                <ChevronUp className="w-4 h-4" /> : 
                <ChevronDown className="w-4 h-4" />
              }
            </button>
          </div>
          
          {expandedSections.comments && (
            <div className="space-y-3">
              {sample.comment && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Комментарий
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {sample.comment}
                  </p>
                </div>
              )}

              {sample.appendix_note && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Приложение
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {sample.appendix_note}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Метаданные */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center mb-3">
          <Calendar className="w-4 h-4 text-gray-600 mr-2" />
          Метаданные
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs">
          {sample.created_at && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <Calendar className="w-3 h-3 mr-1" />
                Создан
              </label>
              <p className="text-gray-900 font-medium">
                {new Date(sample.created_at).toLocaleDateString('ru-RU', {
                  day: '2-digit',
                  month: '2-digit', 
                  year: 'numeric'
                })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(sample.created_at).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          )}
          
          {sample.updated_at && (
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
                <Edit className="w-3 h-3 mr-1" />
                Обновлен
              </label>
              <p className="text-gray-900 font-medium">
                {new Date(sample.updated_at).toLocaleDateString('ru-RU', {
                  day: '2-digit',
                  month: '2-digit', 
                  year: 'numeric'
                })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(sample.updated_at).toLocaleTimeString('ru-RU', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          )}
          
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1 flex items-center">
              <Info className="w-3 h-3 mr-1" />
              ID записи
            </label>
            <div className="bg-gray-100 px-2 py-1 rounded text-xs font-mono font-semibold text-gray-800">
              #{sample.id}
            </div>
          </div>
        </div>
      </div>

      {/* Модальное окно для просмотра фото в полном размере */}
      {selectedPhoto && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedPhoto(null)}
              className="absolute top-4 right-4 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 z-10"
            >
              <X className="w-6 h-6" />
            </button>
            <img 
              src={selectedPhoto} 
              alt="sample full size" 
              className="max-w-full max-h-full object-contain rounded-lg"
            />
          </div>
        </div>
      )}

      {/* Модальное окно загрузки фото */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md rounded-lg p-6 space-y-4">
            <h3 className="text-lg font-semibold">Загрузить фотографии</h3>
            <input 
              type="file" 
              multiple 
              accept="image/jpeg,image/png" 
              onChange={(e) => {
                if (e.target.files) {
                  setUploadFiles(Array.from(e.target.files));
                }
              }} 
            />
            {uploadFiles.length > 0 && (
              <div className="grid grid-cols-3 gap-2">
                {uploadFiles.map((f, idx) => (
                  <img 
                    key={idx} 
                    src={URL.createObjectURL(f)} 
                    className="w-full h-20 object-cover rounded" 
                    alt="preview"
                  />
                ))}
              </div>
            )}
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setShowUpload(false)} 
                className="px-4 py-2 border rounded"
              >
                Отмена
              </button>
              <button 
                onClick={handlePhotoUpload} 
                className="px-4 py-2 bg-blue-600 text-white rounded"
              >
                Загрузить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно подтверждения удаления */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <Trash2 className="w-6 h-6 text-red-600 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Подтвердите удаление
              </h3>
            </div>
            
            <p className="text-gray-600 mb-6">
              Вы уверены, что хотите удалить образец <strong>#{sample.id}</strong>
              {sample.original_sample_number && ` (${sample.original_sample_number})`}? 
              Это действие нельзя отменить.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Отмена
              </button>
              <button
                onClick={handleDeleteSample}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center"
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Удаление...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Удалить
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SampleDetail;