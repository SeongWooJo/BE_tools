UNAME=$(uname -s)

if [[ "$UNAME" == MINGW* || "$UNAME" == CYGWIN* || "$UNAME" == MSYS* ]]; then
    # Windows (Git Bash 등)
    HOST_DIR=$(pwd -W)  # Windows 절대경로로 변환
    echo "[*] Windows 환경 감지됨 → HOST_DIR=${HOST_DIR}"
else
    # Linux / WSL / macOS
    HOST_DIR=$PWD
    echo "[*] Linux/macOS 환경 감지됨 → HOST_DIR=${HOST_DIR}"
fi

docker build -t bufgen .

MSYS_NO_PATHCONV=1 docker run --rm \
  -v "$HOST_DIR":/workspace \
  -w /workspace \
  bufgen \
  generate

find gen/python -type d -exec touch {}/__init__.py \;