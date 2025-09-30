| Endpoint | Actual Route | Status | Notes | Consumers |
|---|---|---|---|---|
| /api/strains/ | strain_management.urls:list_strains | OK | Active in modular app | frontend/src/services/api.ts:216 |
| /api/strains/create/ | strain_management.urls:create_strain | OK | Modular POST create | frontend/src/services/api.ts:226 |
| /api/strains/<id>/ | strain_management.urls:get_strain | OK | Modular detail view | frontend/src/services/api.ts:221 |
| /api/strains/<id>/update/ | strain_management.urls:update_strain | OK | Modular PUT | frontend/src/services/api.ts:231 |
| /api/strains/<id>/delete/ | strain_management.urls:delete_strain | OK | Modular DELETE | frontend/src/services/api.ts:236 |
| /api/strains/validate/ | strain_management.urls:validate_strain | OK | Modular validation | frontend/src/services/api.ts:241 |
| /api/strains/bulk-delete/ | strain_management.urls:bulk_delete_strains | OK | Implemented in modular app | frontend/src/services/api.ts:335; frontend/src/features/strains/services/strains-api.ts:49 |
| /api/strains/bulk-update/ | strain_management.urls:bulk_update_strains | OK | Implemented in modular app | frontend/src/services/api.ts:343 |
| /api/strains/export/ | strain_management.urls:export_strains | OK | Implemented in modular app | frontend/src/services/api.ts:372; frontend/src/features/strains/services/strains-api.ts:70 |
| /api/samples/ | sample_management.urls:list_samples | OK | Modular list | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/create/ | sample_management.urls:create_sample | OK | Modular create | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/<id>/ | sample_management.urls:get_sample | OK | Modular detail | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/<id>/update/ | sample_management.urls:update_sample | OK | Modular update | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/<id>/delete/ | sample_management.urls:delete_sample | OK | Modular delete | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/validate/ | sample_management.urls:validate_sample | OK | Modular validation | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/search/ | sample_management.urls:search_samples | OK | Modular autocomplete/search endpoint | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/bulk-delete/ | sample_management.urls:bulk_delete_samples | OK | Modular bulk delete with audit logging | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/bulk-update/ | sample_management.urls:bulk_update_samples | OK | Modular bulk update incl. characteristics | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/export/ | sample_management.urls:export_samples | OK | Modular export (CSV/JSON/Excel) | frontend/src/features/samples/services/samples-api.ts |
| /api/samples/stats/ | sample_management.urls:samples_stats | OK | Modular statistics endpoint | frontend/src/features/samples/services/samples-api.ts |
| /api/reference-data/ | collection_manager.urls:get_reference_data | OK | Legacy endpoint still routed | frontend/src/services/api.ts:161 |
| /api/reference-data/boxes/ | collection_manager.urls:get_boxes | Legacy | Proxy kept for backward compatibility; prefer `/api/storage/boxes/` | frontend/src/services/api.ts |
| /api/reference-data/boxes/<id>/ | collection_manager.urls:get_box | Legacy | Proxy kept for backward compatibility; prefer `/api/storage/boxes/<box_id>/` | frontend/src/services/api.ts |
| /api/reference-data/boxes/<id>/cells/ | collection_manager.urls:get_box_cells | Legacy | Proxy kept for backward compatibility; prefer `/api/storage/boxes/<box_id>/cells/` | frontend/src/services/api.ts |
| /api/reference-data/boxes/<id>/detail/ | collection_manager.urls:get_box_detail | Legacy | Proxy kept for backward compatibility; prefer `/api/storage/boxes/<box_id>/detail/` | frontend/src/pages/Storage.tsx |
| /api/storage/ | storage_management.urls:storage_overview | OK | Modular storage overview | frontend/src/services/api.ts:243 |
| /api/storage/boxes/ | storage_management.urls:list_storage_boxes | OK | Modular storage list | frontend/src/services/api.ts |
| /api/storage/boxes/<box_id>/ | storage_management.urls:get_storage_box | OK | Metadata + occupancy stats | frontend/src/services/api.ts |
| /api/storage/boxes/<box_id>/detail/ | storage_management.urls:storage_box_details | OK | Detailed cell grid | frontend/src/pages/Storage.tsx |
| /api/storage/boxes/<box_id>/cells/ | storage_management.urls:get_box_cells | OK | Modular free-cell listing | frontend/src/services/api.ts |
| /api/storage/boxes/<box_id>/cells/assign/ | storage_management.urls:assign_cell | OK | Modular assign | frontend/src/services/api.ts |
| /api/storage/boxes/<box_id>/cells/clear/ | storage_management.urls:clear_cell | OK | Modular clear | frontend/src/services/api.ts |
| /api/storage/boxes/<box_id>/cells/bulk-assign/ | storage_management.urls:bulk_assign_cells | OK | Modular bulk assign | frontend/src/services/api.ts |
| /api/audit/ | (missing) | Missing | Include lacks base route; consider add list endpoint | IMPLEMENTATION_CONTEXT.md:30; DEVELOPER_GUIDE.md:44 |
| /api/audit/batch-log/ | audit_logging.urls:create_batch_log | OK | Modular batch log create | backend/audit_logging/tests.py:155 |
| /api/audit/batch/<batch_id>/ | audit_logging.urls:get_batch_operations | OK | Modular batch retrieval | backend/audit_logging/tests.py:358 |
| /api/audit/user-activity/ | audit_logging.urls:get_user_activity | Partially OK | Actual route expects numeric user id segment | backend/audit_logging/tests.py:127 |
| /api/stats/ | collection_manager.urls:api_stats | OK | Legacy stats endpoint | frontend/src/services/api.ts:83; DEVELOPER_GUIDE.md:38 |
| /api/analytics/ | collection_manager.urls:analytics_data | OK | Legacy analytics endpoint | frontend/src/services/api.ts:91 |
| /api/health/ | collection_manager.urls:api_health | OK | Legacy health endpoint | DEPLOYMENT_README.md:235; scripts/check_production_status.sh:58 |
| /api/schema/ | strain_tracker_project.urls:SpectacularAPIView | OK | Auto schema | backend/strain_tracker_project/urls.py:26 |
| /docs/ | strain_tracker_project.urls:SpectacularSwaggerView | OK | Swagger UI | API_ACCESS_GUIDE.md:54 |


