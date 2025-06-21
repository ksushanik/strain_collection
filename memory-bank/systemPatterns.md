# Системные паттерны и архитектура

## Архитектурные паттерны

### Общая архитектура
**Паттерн**: Three-tier Architecture (Трехуровневая архитектура)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Application   │    │      Data       │
│     (React)     │◄──►│    (Django)     │◄──►│  (PostgreSQL)   │
│   Frontend UI   │    │   Backend API   │    │    Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Ключевые архитектурные решения

#### Backend (Django)
- **Model-View-Template (MVT)**: Стандартный Django паттерн
- **Django REST Framework**: API-first подход для интеграции с фронтендом
- **Repository Pattern**: Через Django ORM для абстракции работы с данными
- **Service Layer**: Бизнес-логика выделена в отдельные сервисы

#### Frontend (React)
- **Component-Based Architecture**: Переиспользуемые компоненты
- **Custom Hooks**: Для логики состояния и API вызовов
- **Centralized State Management**: Через React Context (без Redux)
- **Route-Based Code Splitting**: Ленивая загрузка страниц

#### Database (PostgreSQL)
- **Normalized Design**: Третья нормальная форма (3NF)
- **Foreign Key Constraints**: Обеспечение целостности данных
- **Indexing Strategy**: Индексы на часто используемые поля поиска
- **ACID Compliance**: Транзакционность для критических операций

## Паттерны проектирования

### Backend Patterns

#### API Design Pattern
```python
# Консистентная структура API responses
{
    "success": boolean,
    "data": object | array,
    "pagination": {
        "page": int,
        "limit": int,
        "total": int,
        "has_next": boolean,
        "has_previous": boolean
    },
    "message": string,
    "errors": array
}
```

#### Validation Pattern (Pydantic)
```python
# Схемы валидации для всех входящих данных
class StrainCreateSchema(BaseModel):
    strain_code: str = Field(..., min_length=1, max_length=50)
    species_id: int = Field(..., gt=0)
    source_id: Optional[int] = Field(None, gt=0)
    
    class Config:
        str_strip_whitespace = True
        validate_assignment = True
```

#### Repository Pattern
```python
# Абстракция доступа к данным
class StrainRepository:
    def get_all(self, filters: dict) -> QuerySet
    def get_by_id(self, id: int) -> Strain
    def create(self, data: dict) -> Strain
    def update(self, id: int, data: dict) -> Strain
    def delete(self, id: int) -> bool
```

### Frontend Patterns

#### Custom Hooks Pattern
```typescript
// Переиспользуемая логика для API вызовов
const useStrains = (filters: StrainFilters, page: number) => {
    const [data, setData] = useState<StrainsResponse>()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string>()
    
    // Fetch logic with debounce
    useEffect(() => {
        const debounceTimer = setTimeout(() => {
            fetchStrains(filters, page)
        }, 300)
        
        return () => clearTimeout(debounceTimer)
    }, [filters, page])
    
    return { data, loading, error, refetch }
}
```

#### Component Composition Pattern
```typescript
// Композиция компонентов вместо наследования
<DataTable>
    <DataTable.Header>
        <SearchBar onSearch={handleSearch} />
        <FilterPanel filters={filters} onChange={handleFilters} />
    </DataTable.Header>
    <DataTable.Body>
        <StrainList strains={strains} onSelect={handleSelect} />
    </DataTable.Body>
    <DataTable.Footer>
        <Pagination {...paginationProps} />
    </DataTable.Footer>
</DataTable>
```

#### Error Boundary Pattern
```typescript
// Централизованная обработка ошибок
<ErrorBoundary fallback={<ErrorPage />}>
    <Router>
        <Routes>
            <Route path="/strains" element={<StrainsPage />} />
            <Route path="/samples" element={<SamplesPage />} />
        </Routes>
    </Router>
</ErrorBoundary>
```

## Принципы кодирования

### DRY (Don't Repeat Yourself)
- **Переиспользуемые компоненты**: SearchBar, FilterPanel, Pagination
- **Общие утилиты**: formatDate, validateEmail, debounce
- **Базовые классы**: BaseModel, BaseView, BaseSerializer

### SOLID Principles

#### Single Responsibility
- Каждый компонент отвечает за одну функциональность
- Разделение логики: UI компоненты + бизнес хуки + API слой

#### Open/Closed
- Расширение функциональности через props и композицию
- Новые типы фильтров добавляются без изменения базового компонента

#### Dependency Inversion
- Frontend зависит от абстракций API, а не от конкретных implementations
- Backend использует Django ORM как абстракцию над базой данных

### Convention over Configuration
- **Стандартная структура папок**: components/, pages/, services/, types/
- **Именование файлов**: PascalCase для компонентов, camelCase для утилит
- **API endpoints**: RESTful соглашения (/api/strains/, /api/samples/)

## Паттерны данных

### Database Patterns

#### Normalized Schema
```sql
-- Основная таблица штаммов
strains (
    id, strain_code, species_id, source_id, 
    created_at, updated_at
)

-- Связанные справочники
species (id, name, genus, family)
sources (id, name, type, location)

-- Связующие таблицы M:N
strain_samples (strain_id, sample_id)
```

#### Indexing Strategy
```sql
-- Индексы для производительности поиска
CREATE INDEX idx_strains_code ON strains(strain_code);
CREATE INDEX idx_strains_species ON strains(species_id);
CREATE INDEX idx_samples_box_id ON samples(box_id);
CREATE INDEX idx_fulltext_search ON strains USING gin(to_tsvector('english', strain_code || ' ' || comments));
```

### API Patterns

#### Consistent Pagination
```python
# Единообразная пагинация для всех списков
class PaginatedResponse:
    page: int
    limit: int
    total: int
    has_next: bool
    has_previous: bool
    results: List[T]
```

#### Filter Standardization
```python
# Стандартизированные фильтры
class BaseFilters:
    search: Optional[str] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    ordering: str = "-created_at"
```

## Качество кода

### Testing Patterns
- **Unit Tests**: Для отдельных функций и методов
- **Integration Tests**: Для API endpoints
- **Component Tests**: Для React компонентов
- **E2E Tests**: Для критических пользовательских сценариев

### Code Review Process
- **Pull Request Reviews**: Обязательный review перед merge
- **Automated Checks**: ESLint, Prettier, mypy, flake8
- **Documentation**: Обновление документации при изменениях API

### Performance Monitoring
- **Database Query Optimization**: Django Debug Toolbar для профилирования
- **Frontend Performance**: React Developer Tools и Lighthouse
- **API Response Times**: Логирование медленных запросов (>500ms) 