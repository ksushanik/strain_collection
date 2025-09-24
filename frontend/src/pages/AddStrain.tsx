import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { StrainForm } from '../features/strains/components';

const AddStrain: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [isFormOpen, setIsFormOpen] = useState(true);
  
  // Определяем, находимся ли мы в режиме редактирования
  const isEditMode = Boolean(id);

  const handleClose = () => {
    setIsFormOpen(false);
    if (isEditMode) {
      // Если редактируем, возвращаемся к карточке штамма
      navigate(`/strains/${id}`);
    } else {
      // Если создаем новый, идем в общий список
      navigate('/strains');
    }
  };

  const handleSuccess = () => {
    setIsFormOpen(false);
    if (isEditMode) {
      // Если редактировали, возвращаемся к карточке штамма
      navigate(`/strains/${id}`);
    } else {
      // Если создавали новый, идем в общий список
      navigate('/strains');
    }
  };

  return (
    <StrainForm
      isOpen={isFormOpen}
      onClose={handleClose}
      onSuccess={handleSuccess}
      strainId={id ? parseInt(id) : undefined}
    />
  );
};

export default AddStrain;