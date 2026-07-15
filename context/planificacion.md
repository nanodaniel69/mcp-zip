# Planificación — mcp-zip

## Sprint Actual: MVP + Publicación (COMPLETADO)

### Fase 1: Bugs Críticos ✅
- [x] Fix _parsear_contenido() — contenido con espacios
- [x] Fix mover_a_boveda() — sincronización SQLite
- [x] Tests para ambos fixes

### Fase 2: TF-IDF ✅
- [x] Módulo tfidf.py — tokenizador español
- [x] MotorTFIDF — re-ranking 60% TF-IDF + 40% FTS5
- [x] Integración con MotorBusqueda
- [x] 11 tests para TF-IDF

### Fase 2.5: JSON Secundario ✅
- [x] almacenamiento_json.py — lectura/escritura JSON
- [x] Sync automático con .md
- [x] 10 tests para JSON

### Fase 3: Funcionalidad ✅
- [x] memoria_estadisticas() — métricas de ahorro
- [x] memoria_sincronizar() — sync global
- [x] memoria_exportar_zip() — formato .mcp-zip
- [x] memoria_importar_zip() — importar desde .mcp-zip
- [x] memoria_listar_zip() — listar contenido .mcp-zip
- [x] 11 tests para Fase 3

### Fase 4: Publicación ✅
- [x] pyproject.toml actualizado (v0.2.0)
- [x] README reescrito con arquitectura completa
- [x] demo.tape para GIF
- [x] Publicación en PyPI

## Próximos Pasos (Futuro)

### Fase 5: Distribución
- [ ] Agregar topics a GitHub (mcp, memory, ai, tokens, spanish)
- [ ] Crear GIF con VHS
- [ ] Documentación de API
- [ ] Ejemplos de uso

### Fase 6: Mejoras
- [ ] Soporte para idiomas adicionales
- [ ] API REST para acceso externo
- [ ] Sincronización entre dispositivos
- [ ] Métricas de uso detalladas

### Fase 7: Comunidad
- [ ] Contributing guide
- [ ] Issues templates
- [ ] CI/CD con GitHub Actions
- [ ] Coverage report
