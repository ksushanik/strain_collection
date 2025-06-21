from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
import pandas as pd
import os
from collection_manager.models import *
from collection_manager.schemas import *


def validate_boolean_from_csv(value):
    """Преобразование CSV значений в булев тип"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    return bool(value)


class Command(BaseCommand):
    help = 'Импорт данных из CSV файлов'

    def add_arguments(self, parser):
        parser.add_argument('--table', type=str, choices=['all', 'storage', 'samples', 'strains'], 
                          default='all', help='Какую таблицу импортировать')
        parser.add_argument('--force', action='store_true', 
                          help='Принудительно очистить таблицы перед импортом')

    def handle(self, *args, **options):
        table = options['table']
        force = options['force']
        
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data')
        
        self.stdout.write("🚀 Запуск импорта данных...")
        
        if table == 'all' or table == 'storage':
            self.import_storage_data(data_dir, force)
            
        if table == 'all' or table == 'samples':
            self.import_samples_data(data_dir, force)
            
        if table == 'all' or table == 'strains':
            self.import_strains_data(data_dir, force)
            
        self.stdout.write("✅ Импорт завершен!")

    @transaction.atomic
    def import_storage_data(self, data_dir, force):
        """Импорт данных хранилища"""
        self.stdout.write("📦 Импорт данных хранилища...")
        
        if force:
            Storage.objects.all().delete()
            self.stdout.write("Очищена таблица Storage")
        
        file_path = os.path.join(data_dir, 'Storage_Table.csv')
        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)
        
        storage_objects = []
        validated_count = 0
        
        for index, row in df.iterrows():
            try:
                storage_data = ImportStorageSchema.model_validate(row.to_dict())
                storage_objects.append(Storage(
                    id=storage_data.StorageID,
                    box_id=storage_data.BoxIDValue,
                    cell_id=storage_data.CellIDValue
                ))
                validated_count += 1
            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                return
        
        Storage.objects.bulk_create(storage_objects, batch_size=500)
        self.stdout.write(f"✅ Импортировано {validated_count} записей хранилища")

    @transaction.atomic  
    def import_samples_data(self, data_dir, force):
        """Импорт образцов с корректными связями"""
        self.stdout.write("🧪 Импорт образцов...")
        
        if force:
            Sample.objects.all().delete()
            self.stdout.write("Очищена таблица Sample")
        
        file_path = os.path.join(data_dir, 'Samples_Table.csv')
        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)
        
        validated_count = 0
        
        for index, row in df.iterrows():
            try:
                # Подготовка данных для валидации
                row_dict = row.to_dict()
                for key, value in row_dict.items():
                    if pd.isna(value) or value == "":
                        row_dict[key] = None if '_FK' in key or key == 'OriginalSampleNumber' else ""
                    elif key.startswith('Has') or key == 'IsIdentified' or key == 'SEQStatus':
                        row_dict[key] = str(value).lower()
                
                validated_data = ImportSampleSchema.model_validate(row_dict)
                
                # Получение связанных объектов
                def get_foreign_object(model_class, field_id):
                    if field_id is None:
                        return None
                    try:
                        return model_class.objects.get(id=field_id)
                    except model_class.DoesNotExist:
                        self.stdout.write(f"⚠️ {model_class.__name__} с ID {field_id} не найден")
                        return None
                
                index_letter = get_foreign_object(IndexLetter, validated_data.IndexLetterID_FK)
                strain = get_foreign_object(Strain, validated_data.StrainID_FK)
                storage = get_foreign_object(Storage, validated_data.StorageID_FK)
                source = get_foreign_object(Source, validated_data.SourceID_FK)
                location = get_foreign_object(Location, validated_data.LocationID_FK)
                appendix_note = get_foreign_object(AppendixNote, validated_data.AppendixNoteID_FK)
                comment = get_foreign_object(Comment, validated_data.CommentID_FK)
                
                Sample.objects.get_or_create(
                    id=validated_data.SampleRowID,
                    defaults={
                        'index_letter': index_letter,
                        'strain': strain,
                        'storage': storage,
                        'original_sample_number': validated_data.OriginalSampleNumber,
                        'source': source,
                        'location': location,
                        'appendix_note': appendix_note,
                        'comment': comment,
                        'has_photo': validate_boolean_from_csv(validated_data.HasPhoto),
                        'is_identified': validate_boolean_from_csv(validated_data.IsIdentified),
                        'has_antibiotic_activity': validate_boolean_from_csv(validated_data.HasAntibioticActivity),
                        'has_genome': validate_boolean_from_csv(validated_data.HasGenome),
                        'has_biochemistry': validate_boolean_from_csv(validated_data.HasBiochemistry),
                        'seq_status': validate_boolean_from_csv(validated_data.SEQStatus)
                    }
                )
                validated_count += 1
                
            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                continue
        
        self.stdout.write(f"✅ Импортировано {validated_count} образцов")

    @transaction.atomic
    def import_strains_data(self, data_dir, force):
        """Импорт штаммов"""
        self.stdout.write("🦠 Импорт штаммов...")
        
        if force:
            Strain.objects.all().delete()
            self.stdout.write("Очищена таблица Strain")
        
        file_path = os.path.join(data_dir, 'Strains_Table.csv')
        df = pd.read_csv(file_path, dtype=str)
        df = df.where(pd.notna(df), None)
        
        validated_count = 0
        
        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                for key, value in row_dict.items():
                    if pd.isna(value) or value == "":
                        row_dict[key] = None
                
                validated_data = ImportStrainSchema.model_validate(row_dict)
                
                Strain.objects.get_or_create(
                    id=validated_data.StrainID,
                    defaults={
                        'short_code': validated_data.ShortStrainCode,
                        'rrna_taxonomy': validated_data.RRNATaxonomy,
                        'identifier': validated_data.StrainIdentifierValue,
                        'name_alt': validated_data.StrainNameAlt,
                        'rcam_collection_id': validated_data.RCAMCollectionID
                    }
                )
                validated_count += 1
                
            except Exception as e:
                self.stdout.write(f"❌ Ошибка в строке {index + 2}: {e}")
                continue
        
        self.stdout.write(f"✅ Импортировано {validated_count} штаммов") 