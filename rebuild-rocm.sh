#!/bin/bash

# Limpieza total
echo "Limpiando el directorio de construcción..."
rm -rf ~/llama.cpp/build

# Variables de Entorno para Arch
export ROCM_PATH=/opt/rocm
export HIP_PATH=$ROCM_PATH
export PATH=$ROCM_PATH/bin:$PATH
export LD_LIBRARY_PATH=$ROCM_PATH/lib:$LD_LIBRARY_PATH

# Configuración CMake para RX 6600 (Usando gfx1030 para compatibilidad con rocBLAS en Arch)
echo "Configurando CMake para ROCm (gfx1030)..."
# La opción correcta es GGML_HIP=ON en versiones recientes
cmake -S ~/llama.cpp -B ~/llama.cpp/build \
    -DGGML_HIP=ON \
    -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DCMAKE_HIP_ARCHITECTURES=gfx1030 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=/opt/rocm

# Verificar si HIP fue activado en la configuración
if ! grep -q "GGML_HIP:BOOL=ON" ~/llama.cpp/build/CMakeCache.txt; then
    echo "ERROR: CMake no activó GGML_HIP. Revisa los logs superiores."
    exit 1
fi

# Compilación de targets específicos (evita errores en tests externos)
echo "Compilando llama-server y llama-cli con aceleración ROCm..."
cmake --build ~/llama.cpp/build --config Release -j$(nproc) --target llama-server llama-cli

# Verificación
echo "Verificando la compilación..."
if [ -f ~/llama.cpp/build/bin/llama-server ]; then
    VERSION_OUTPUT=$(~/llama.cpp/build/bin/llama-server --version 2>&1)
    echo "$VERSION_OUTPUT"

    if [ -f ~/llama.cpp/build/bin/libggml-hip.so ] || ~/llama.cpp/build/bin/llama-server --list-devices 2>&1 | grep -iqE "ROCm|HIP|Radeon"; then
        echo "¡Éxito! Soporte para HIP/ROCm detectado y listo para aceleración GPU."
    else
        echo "ERROR: No se detectó soporte para HIP en el binario compilado."
        exit 1
    fi
else
    echo "ERROR: No se encontró el binario llama-server en ~/llama.cpp/build/bin/"
    exit 1
fi
