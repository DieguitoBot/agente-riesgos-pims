#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "Este script requiere permisos de administrador para configurar el servicio de Ollama."
   echo "Por favor ejecútalo con: sudo bash $0"
   exit 1
fi

echo "=========================================================="
echo " Habilitando GPU integrada AMD Radeon en Ollama (Vulkan)"
echo "=========================================================="

echo "1. Creando directorio de configuración de anulación..."
mkdir -p /etc/systemd/system/ollama.service.d

echo "2. Configurando variable OLLAMA_IGPU_ENABLE=1..."
cat << 'EOF' > /etc/systemd/system/ollama.service.d/igpu.conf
[Service]
Environment="OLLAMA_IGPU_ENABLE=1"
EOF

echo "3. Recargando configuración de systemd..."
systemctl daemon-reload

echo "4. Reiniciando servicio ollama..."
systemctl restart ollama

echo "5. Verificando estado en el log de Ollama..."
sleep 2

if journalctl -u ollama -n 30 --no-pager | grep -i "RADV RENOIR\|Vulkan0"; then
    echo "=========================================================="
    echo " ¡ÉXITO! La GPU integrada AMD Radeon ha sido detectada y"
    echo " activada correctamente mediante la biblioteca Vulkan."
    echo "=========================================================="
else
    echo "Ollama se reinició. Revisa el log completo con: journalctl -u ollama -n 30"
fi
