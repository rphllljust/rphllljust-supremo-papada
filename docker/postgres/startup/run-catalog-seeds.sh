#!/bin/sh
set -eu

DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-postgres}"
SEED_DIR="/docker-entrypoint-startdb.d"
WAIT_SECONDS="${POSTGRES_CATALOG_SEED_WAIT_SECONDS:-120}"

wait_for_database() {
    until pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
        sleep 1
    done
}

wait_for_table() {
    table_name="$1"
    elapsed=0

    while [ "$elapsed" -lt "$WAIT_SECONDS" ]; do
        exists="$(psql -U "$DB_USER" -d "$DB_NAME" -tAqc "SELECT to_regclass('public.${table_name}') IS NOT NULL")"
        if [ "$exists" = "t" ]; then
            return 0
        fi

        elapsed=$((elapsed + 1))
        sleep 1
    done

    return 1
}

wait_for_database

for table_name in cursos_eixotecnologico cursos_tipocomponente cursos_nivelensino; do
    if ! wait_for_table "$table_name"; then
        echo "Catalog seed skipped: table $table_name was not created within ${WAIT_SECONDS}s."
        exit 0
    fi
done

for sql_file in "$SEED_DIR"/*.sql; do
    [ -f "$sql_file" ] || continue
    echo "Applying startup SQL: $sql_file"
    psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
done

echo "Catalog startup SQL scripts applied."