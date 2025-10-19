import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Microscope, 
  TestTube, 
  Edit,
  Download,
  Database,
  Calendar,
  BarChart3,
  Camera,
  CheckCircle,
  Trash2
} from 'lucide-react';
import apiService from '../services/api';
import type { Strain, Sample } from '../types';
import type { AxiosError } from 'axios';

const StrainDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [strain, setStrain] = useState<Strain | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [samplesLoading, setSamplesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchStrainDetails = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const strainData = await apiService.getStrain(parseInt(id));
        setStrain(strainData);
      } catch (err) {
        const axiosErr = err as AxiosError<{ error?: string; message?: string }>;
        const serverMessage = axiosErr.response?.data?.error || axiosErr.response?.data?.message;
        setError(serverMessage || axiosErr.message || 'Ошибка загрузки информации о штамме');
        console.error('Error fetching strain:', err);
      } finally {
        setLoading(false);
      }
    };

    const fetchSamples = async () => {
      if (!id) return;
      
      try {
        setSamplesLoading(true);
        const samplesData = await apiService.getSamplesByStrain(parseInt(id));
        setSamples(samplesData.samples || []);
      } catch (err) {
        console.error('Error fetching samples:', err);
      } finally {
        setSamplesLoading(false);
      }
    };

    fetchStrainDetails();
    fetchSamples();
  }, [id]);

  const handleDeleteStrain = async () => {
    if (!strain) return;
    
    setIsDeleting(true);
    try {
      await apiService.deleteStrain(strain.id);
      navigate('/strains');
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ error?: string; message?: string }>;
      const serverMessage = axiosErr.response?.data?.error || axiosErr.response?.data?.message;
      setError(serverMessage || axiosErr.message || 'Ошибка при удалении штамма');
      console.error('Error deleting strain:', err);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Загрузка штамма...</span>
      </div>
    );
  }

  if (error || !strain) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">{error || 'Штамм не найден'}</p>
        <button 
          onClick={() => navigate('/strains')}
          className="mt-2 text-blue-600 hover:text-blue-800"
        >
          ← Вернуться к списку штаммов
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
            onClick={() => navigate('/strains')}
            className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Штамм {strain.short_code}
            </h1>
            <p className="text-gray-600">{strain.identifier}</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => {
              // TODO: Реализовать экспорт штамма
              console.log('Экспорт штамма', strain.id);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Экспорт
          </button>
          <button 
            onClick={() => navigate(`/strains/${strain.id}/edit`)}
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
          <Microscope className="w-6 h-6 text-blue-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">
            Основная информация
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Короткий код
            </label>
            <p className="text-lg font-semibold text-gray-900">
              {strain.short_code}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Идентификатор
            </label>
            <p className="text-lg text-gray-900">
              {strain.identifier}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">
              RCAM ID коллекции
            </label>
            <p className="text-lg text-gray-900">
              {strain.rcam_collection_id || 'Не указан'}
            </p>
          </div>
          
          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium text-gray-500 mb-1">
              Таксономия rRNA
            </label>
            <p className="text-lg text-gray-900 bg-gray-50 p-3 rounded-lg">
              {strain.rrna_taxonomy}
            </p>
          </div>
          
          {strain.name_alt && (
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium text-gray-500 mb-1">
                Альтернативное название
              </label>
              <p className="text-lg text-gray-900">
                {strain.name_alt}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Metadata and Stats Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Metadata Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Calendar className="w-6 h-6 text-blue-600 mr-3" />
            <h2 className="text-lg font-semibold text-gray-900">
              Метаданные
            </h2>
          </div>
          
          <div className="space-y-4">
            {strain.created_at && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Дата создания
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(strain.created_at).toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            )}
            
            {strain.updated_at && (
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">
                  Последнее обновление
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(strain.updated_at).toLocaleString('ru-RU', {
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
                {strain.id}
              </p>
            </div>
          </div>
        </div>

        {/* Samples Statistics Card */}
        {strain.samples_stats && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <BarChart3 className="w-6 h-6 text-green-600 mr-3" />
              <h2 className="text-lg font-semibold text-gray-900">
                Статистика образцов
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Всего образцов</span>
                <span className="text-lg font-semibold text-gray-900">
                  {strain.samples_stats.total_count}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <Camera className="w-4 h-4 text-blue-500 mr-2" />
                    <span className="text-sm text-gray-600">С фотографиями</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-900">
                      {strain.samples_stats.with_photo_count}
                    </span>
                    <span className="text-xs text-gray-500 ml-1">
                      ({strain.samples_stats.photo_percentage}%)
                    </span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-600">Идентифицированы</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-900">
                      {strain.samples_stats.identified_count}
                    </span>
                    <span className="text-xs text-gray-500 ml-1">
                      ({strain.samples_stats.identified_percentage}%)
                    </span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <Database className="w-4 h-4 text-purple-500 mr-2" />
                    <span className="text-sm text-gray-600">С геномами</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {strain.samples_stats.with_genome_count}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <TestTube className="w-4 h-4 text-orange-500 mr-2" />
                    <span className="text-sm text-gray-600">С биохимией</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {strain.samples_stats.with_biochemistry_count}
                  </span>
                </div>
              </div>
              
              {/* Progress bars for percentages */}
              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>С фотографиями</span>
                    <span>{strain.samples_stats.photo_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${strain.samples_stats.photo_percentage}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Идентифицированы</span>
                    <span>{strain.samples_stats.identified_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${strain.samples_stats.identified_percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Samples Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <TestTube className="w-6 h-6 text-green-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">
              Связанные образцы
            </h2>
            <span className="ml-3 bg-gray-100 text-gray-800 text-sm font-medium px-2.5 py-0.5 rounded-full">
              {samples.length}
            </span>
          </div>
          <button 
            onClick={() => navigate(`/samples?strain_id=${strain.id}`)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Просмотреть все →
          </button>
        </div>

        {samplesLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Загрузка образцов...</span>
          </div>
        ) : samples.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <TestTube className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Образцы для этого штамма не найдены</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Номер образца
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Источник
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Локация
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Хранилище
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Статус
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {samples.slice(0, 5).map((sample) => (
                  <tr key={sample.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {sample.original_sample_number || `Sample #${sample.id}`}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {sample.source?.organism_name || 'Не указан'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {sample.source?.source_type}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {sample.location?.name || 'Не указана'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {sample.storage ? `${sample.storage.box_id}-${sample.storage.cell_id}` : 'Не указано'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {sample.photos && sample.photos.length > 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Фото
                          </span>
                        )}
                        {/* Dynamic characteristics will be shown through the characteristics array */}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {samples.length > 5 && (
              <div className="mt-4 text-center">
                <button 
                  onClick={() => navigate(`/samples?strain_id=${strain.id}`)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Показать все {samples.length} образцов →
                </button>
              </div>
            )}
          </div>
        )}
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
              Вы уверены, что хотите удалить штамм <strong>{strain.short_code}</strong>? 
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
                onClick={handleDeleteStrain}
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

export default StrainDetail;