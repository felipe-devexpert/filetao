#!/bin/sh -eu

reassign_prefixed_variables() {
    prefix=$1
    new_prefix=$2
    for var in $(env | grep "^$prefix" | sed 's/=.*//'); do
        new_var_name=$(echo "$var" | sed "s/^$prefix/$new_prefix/")
        eval new_var_value=\$"$var"
        # shellcheck disable=SC2154
        export "$new_var_name"="$new_var_value"
    done
}

reassign_prefixed_variables "$(echo "FILETAO_${FILETAO_NODE}_" | tr '[:lower:]' '[:upper:]')" FILETAO_

if [ $# -eq 0 ]; then
  # shellcheck disable=SC2046,SC2086
  exec filetao run "${FILETAO_NODE}" \
      --wallet.name "${FILETAO_WALLET}" \
      --wallet.hotkey "${FILETAO_HOTKEY}" \
      --netuid "${FILETAO_NETUID:-21}" \
      $( [ -n "${FILETAO_IP:-}" ] && echo "--axon.ip ${FILETAO_IP}" ) \
      --axon.port "${FILETAO_EXTERNAL_PORT}" \
      --axon.external_port "${FILETAO_EXTERNAL_PORT}" \
      --subtensor.network "${FILETAO_SUBTENSOR}" \
      --database.host "${REDIS_HOST:-127.0.0.1}" \
      --database.port "${REDIS_PORT:-6379}" \
      $( [ -n "${REDIS_PASSWORD:-}" ] && echo "--database.password ${REDIS_PASSWORD}" ) \
      ${FILETAO_EXTRA_OPTIONS}
else
  exec "$@"
fi
