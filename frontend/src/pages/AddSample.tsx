import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AddSampleForm from '../components/AddSampleForm';

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

  return (
    <AddSampleForm
      isOpen={isFormOpen}
      onClose={handleClose}
      onSuccess={handleSuccess}
    />
  );
};

export default AddSample; 