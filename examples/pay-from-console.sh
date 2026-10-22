#!/usr/bin/env sh
# Buy API access from a console, no browser: crypto through NOWPayments. The e-mail owns the key.
#   ./pay-from-console.sh you@example.com full monthly
EMAIL="${1:?email}"; API="${2:-full}"; PERIOD="${3:-monthly}"
curl -sS -X POST https://www.sealagom.com/api/agent/checkout/ -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"api\": \"$API\", \"period\": \"$PERIOD\"}" -o order.json
cat order.json; echo
echo "Pay invoice_url with any wallet, then poll status_url until paid is true: it carries the key."
