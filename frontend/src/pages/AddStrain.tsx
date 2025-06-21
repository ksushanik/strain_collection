import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AddStrainForm from '../components/AddStrainForm';

const AddStrain: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  // Определяем, находимся ли мы в режиме редактирования
  const isEditMode = Boolean(id);

  const handleClose = () => {
    if (isEditMode) {
      // Если редактируем, возвращаемся к карточке штамма
      navigate(`/strains/${id}`);
    } else {
      // Если создаем новый, идем в общий список
      navigate('/strains');
    }
  };

  const handleSuccess = () => {
    if (isEditMode) {
      // Если редактировали, возвращаемся к карточке штамма
      navigate(`/strains/${id}`);
    } else {
      // Если создавали новый, идем в общий список
      navigate('/strains');
    }
  };

  return (
    <AddStrainForm
      strainId={id}
      onCancel={handleClose}
      onSuccess={handleSuccess}
    />
  );
};

export default AddStrain; 