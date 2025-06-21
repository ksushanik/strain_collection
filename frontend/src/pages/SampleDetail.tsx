import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Download, 
  Calendar,
  Beaker,
  Microscope,
  MapPin,
  TestTube,
  Camera,
  Dna,
  FlaskConical,
  Eye,
  CheckCircle,
  Info,
  Loader2,
  Trash2
} from 'lucide-react';
import apiService from '../services/api';
import type { Sample } from '../types';

const SampleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [sample, setSample] = useState<Sample | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

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

  const getCharacteristicsBadges = (sample: Sample) => {
    const badges = [];
    
    if (sample.has_photo) badges.push({ 
      icon: Camera, 
      label: 'Фото', 
      color: 'green',
      description: 'Образец сфотографирован'
    });
    if (sample.is_identified) badges.push({ 
      icon: Eye, 
      label: 'Идентифицирован', 
      color: 'blue',
      description: 'Образец идентифицирован'
    });
    if (sample.has_antibiotic_activity) badges.push({ 
      icon: TestTube, 
      label: 'Антибиотическая активность', 
      color: 'purple',
      description: 'Обнаружена антибиотическая активность'
    });
    if (sample.has_genome) badges.push({ 
      icon: Dna, 
      label: 'Геном', 
      color: 'red',
      description: 'Геном секвенирован'
    });
    if (sample.has_biochemistry) badges.push({ 
      icon: FlaskConical, 
      label: 'Биохимические данные', 
      color: 'yellow',
      description: 'Проведен биохимический анализ'
    });
    if (sample.seq_status) badges.push({ 
      icon: Dna, 
      label: 'Секвенирование', 
      color: 'indigo',
      description: 'Выполнено секвенирование'
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/samples')}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Образец #{sample.id}
            </h1>
            <p className="text-gray-600">
              {sample.original_sample_number ? `Номер образца: ${sample.original_sample_number}` : 'Детальная информация об образце'}
            </p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => {
              // TODO: Реализовать экспорт образца
              console.log('Экспорт образца', sample.id);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Экспорт
          </button>
          <button 
            onClick={() => navigate(`/samples/${sample.id}/edit`)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
          >
            <Edit className="w-4 h-4 mr-2" />
            Редактировать
          </button>
          <button 
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Удалить
          </button>
        </div>
      </div>

      {/* Main Info Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Beaker className="w-6 h-6 text-blue-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">
            Основная информация
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              ID образца
            </label>
            <p className="text-lg font-semibold text-gray-900">
              #{sample.id}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Номер образца
            </label>
            <p className="text-lg text-gray-900">
              {sample.original_sample_number || 'Не указан'}
            </p>
          </div>

          {sample.index_letter && (
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                Индексное письмо
              </label>
              <p className="text-lg text-gray-900">
                {sample.index_letter.letter_value}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Related Entities Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strain Info */}
        {sample.strain && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Microscope className="w-6 h-6 text-green-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Связанный штамм
              </h2>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Короткий код
                </label>
                <p className="text-sm font-medium text-gray-900">
                  {sample.strain.short_code}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Идентификатор
                </label>
                <p className="text-sm text-gray-900">
                  {sample.strain.identifier}
                </p>
              </div>

              {sample.strain.rrna_taxonomy && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Таксономия rRNA
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                    {sample.strain.rrna_taxonomy}
                  </p>
                </div>
              )}

              <button
                onClick={() => navigate(`/strains/${sample.strain!.id}`)}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Просмотреть штамм →
              </button>
            </div>
          </div>
        )}

        {/* Storage Info */}
        {sample.storage && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <MapPin className="w-6 h-6 text-purple-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Хранение
              </h2>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Бокс
                </label>
                <p className="text-lg font-medium text-gray-900">
                  {sample.storage.box_id}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Ячейка
                </label>
                <p className="text-lg font-medium text-gray-900">
                  {sample.storage.cell_id}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Полный адрес
                </label>
                <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded font-mono">
                  {sample.storage.box_id} - {sample.storage.cell_id}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Source Info */}
        {sample.source && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Info className="w-6 h-6 text-orange-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Источник
              </h2>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Организм
                </label>
                <p className="text-sm font-medium text-gray-900">
                  {sample.source.organism_name}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Тип источника
                </label>
                <p className="text-sm text-gray-900">
                  {sample.source.source_type}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Категория
                </label>
                <p className="text-sm text-gray-900">
                  {sample.source.category}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Location Info */}
        {sample.location && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <MapPin className="w-6 h-6 text-red-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Местоположение
              </h2>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                Название локации
              </label>
              <p className="text-lg font-medium text-gray-900">
                {sample.location.name}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Characteristics Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
          <h2 className="text-lg font-semibold text-gray-900">
            Характеристики и анализы
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {getCharacteristicsBadges(sample).map(({ icon: Icon, label, color, description }, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-2 ${
                color === 'green' ? 'border-green-200 bg-green-50' :
                color === 'blue' ? 'border-blue-200 bg-blue-50' :
                color === 'purple' ? 'border-purple-200 bg-purple-50' :
                color === 'red' ? 'border-red-200 bg-red-50' :
                color === 'yellow' ? 'border-yellow-200 bg-yellow-50' :
                'border-indigo-200 bg-indigo-50'
              }`}
            >
              <div className="flex items-center space-x-2 mb-2">
                <Icon className={`w-5 h-5 ${
                  color === 'green' ? 'text-green-600' :
                  color === 'blue' ? 'text-blue-600' :
                  color === 'purple' ? 'text-purple-600' :
                  color === 'red' ? 'text-red-600' :
                  color === 'yellow' ? 'text-yellow-600' :
                  'text-indigo-600'
                }`} />
                <span className={`font-medium ${
                  color === 'green' ? 'text-green-800' :
                  color === 'blue' ? 'text-blue-800' :
                  color === 'purple' ? 'text-purple-800' :
                  color === 'red' ? 'text-red-800' :
                  color === 'yellow' ? 'text-yellow-800' :
                  'text-indigo-800'
                }`}>{label}</span>
              </div>
              <p className="text-sm text-gray-600">{description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Comments and Notes */}
        {(sample.comment || sample.appendix_note) && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Info className="w-6 h-6 text-gray-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Комментарии и заметки
              </h2>
            </div>
            
            <div className="space-y-4">
              {sample.comment && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Комментарий
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {sample.comment.text}
                  </p>
                </div>
              )}
              
              {sample.appendix_note && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-1">
                    Приложение
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                    {sample.appendix_note.text}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Calendar className="w-6 h-6 text-gray-600 mr-3" />
            <h2 className="text-lg font-semibold text-gray-900">
              Метаданные
            </h2>
          </div>
          
          <div className="space-y-4">
            {sample.created_at && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Дата создания
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(sample.created_at).toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            )}
            
            {sample.updated_at && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Последнее обновление
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(sample.updated_at).toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                ID записи
              </label>
              <p className="text-sm text-gray-900 font-mono">
                {sample.id}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
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