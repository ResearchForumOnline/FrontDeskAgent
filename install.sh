#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${FRONTDESKAGENT_DIR:-$HOME/frontdeskagent}"
REPO_URL="${FRONTDESKAGENT_REPO:-https://github.com/ResearchForumOnline/FrontDeskAgent.git}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Installing FrontDeskAgent into ${APP_DIR}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install git first." >&2
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3.10+ first." >&2
  exit 1
fi

if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> Created .env from template."
  if [[ "${FRONTDESKAGENT_SKIP_WIZARD:-0}" != "1" ]]; then
    echo "==> Running setup wizard. Press Enter for defaults if unsure."
    python -m frontdeskagent.setup_wizard --env .env --force || true
  fi
fi

mkdir -p data runtime
python -m compileall frontdeskagent >/dev/null

cat <<EOF

FrontDeskAgent installed.

Start it now:
  cd ${APP_DIR}
  source .venv/bin/activate
  python -m frontdeskagent.app

Open:
  http://localhost:8088

For systemd:
  sudo cp systemd/frontdeskagent.service /etc/systemd/system/frontdeskagent.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now frontdeskagent

EOF
