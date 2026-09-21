#!/usr/bin/env bash
set -e

# ==============================================================================
# SSL/TLS Certificate Provisioning Helper (CHIP DEP-07)
# Generates self-signed development certificates or guides Let's Encrypt setup.
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSL_DIR="${PROJECT_ROOT}/nginx/ssl"

mkdir -p "${SSL_DIR}"

if [ -f "${SSL_DIR}/cert.pem" ] && [ -f "${SSL_DIR}/key.pem" ]; then
    echo "Notice: SSL certificates already exist at ${SSL_DIR}"
    exit 0
fi

echo "Generating self-signed SSL certificates for development testing..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "${SSL_DIR}/key.pem" \
    -out "${SSL_DIR}/cert.pem" \
    -subj "/C=US/ST=Development/L=Local/O=CertCheck/OU=Security/CN=localhost"

chmod 600 "${SSL_DIR}/key.pem"
chmod 644 "${SSL_DIR}/cert.pem"

echo "=== SSL Setup Complete ==="
echo "Certificate: ${SSL_DIR}/cert.pem"
echo "Private Key: ${SSL_DIR}/key.pem"
echo ""
echo "For public production deployment, obtain trusted certificates via Certbot:"
echo "certbot certonly --webroot -w /usr/share/nginx/html -d yourdomain.com"
