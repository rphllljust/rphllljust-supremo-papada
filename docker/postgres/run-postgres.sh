#!/bin/sh
set -eu

/usr/local/bin/docker-entrypoint.sh postgres &
postgres_pid=$!

shutdown() {
    kill "$postgres_pid" 2>/dev/null || true
    wait "$postgres_pid" 2>/dev/null || true
}

trap shutdown INT TERM

sh /docker-entrypoint-startdb.d/run-catalog-seeds.sh

wait "$postgres_pid"