import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AddSampleForm, EditSampleForm } from '../features/samples/components';

const AddSample: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [isFormOpen, setIsFormOpen] = useState(true);
  
  // Определяем, находимся ли мы в режиме редактирования
  const isEditMode = Boolean(id);

  const handleClose = () => {
    setIsFormOpen(false);
    if (isEditMode) {
      // Если редактируем, возвращаемся к карточке образца
      navigate(`/samples/${id}`);
    } else {
      // Если создаем новый, идем в общий список
      navigate('/samples');
    }
  };

  const handleSuccess = () => {
    setIsFormOpen(false);
    if (isEditMode) {
      // Если редактировали, возвращаемся к карточке образца
      navigate(`/samples/${id}`);
    } else {
      // Если создавали новый, идем в общий список
      navigate('/samples');
    }
  };

  // Если редактируем - используем EditSampleForm, иначе AddSampleForm
  return isEditMode ? (
    <EditSampleForm
      isOpen={isFormOpen}
      onClose={handleClose}
      onSuccess={handleSuccess}
      sampleId={parseInt(id!)}
    />
  ) : (
    <AddSampleForm
      isOpen={isFormOpen}
      onClose={handleClose}
      onSuccess={handleSuccess}
    />
  );
};

export default AddSample;