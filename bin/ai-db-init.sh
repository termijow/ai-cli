#!/bin/bash

# Inicializar base de datos de métricas
DB_PATH="$HOME/.ai_cli_db.db"

if [[ ! -f "$DB_PATH" ]]; then
    echo "📊 Inicializando base de datos..."
    sqlite3 "$DB_PATH" < db/init.sql
    echo "✅ Base de datos creada: $DB_PATH"
else
    echo "📊 Base de datos ya existe: $DB_PATH"
fi
