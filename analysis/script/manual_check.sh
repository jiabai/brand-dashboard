#!/usr/bin/env bash

set -u

stop_on_first_error=0
pylint_full=0
python_exe="python"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stop-on-first-error)
      stop_on_first_error=1
      shift
      ;;
    --pylint-full)
      pylint_full=1
      shift
      ;;
    --python)
      python_exe="${2:-}"
      shift 2
      ;;
    -h|--help)
      printf '%s\n' "Usage: $0 [--stop-on-first-error] [--pylint-full] [--python <python_exe>]"
      exit 0
      ;;
    *)
      printf '%s\n' "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

had_failure=0
skipped=()

test_cmd() {
  command -v "$1" >/dev/null 2>&1
}

in_venv() {
  "$python_exe" -c 'import sys; print(int(sys.prefix != sys.base_prefix))' 2>/dev/null
}

ensure_pip() {
  if "$python_exe" -m pip --version >/dev/null 2>&1; then
    return 0
  fi
  "$python_exe" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$python_exe" -m pip --version >/dev/null 2>&1
}

pip_install() {
  local pkg="$1"
  if ! ensure_pip; then
    return 1
  fi

  local user_flag=()
  if [[ "$(in_venv || echo 0)" != "1" ]]; then
    user_flag=(--user)
  fi

  "$python_exe" -m pip install -q "${user_flag[@]}" "$pkg"
}

test_python_module() {
  if ! test_cmd "$python_exe"; then
    printf '%s\n' "Python executable not found: $python_exe" >&2
    exit 2
  fi
  "$python_exe" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" >/dev/null 2>&1
}

ensure_python_module() {
  local module="$1"
  local pkg="${2:-$1}"

  if test_python_module "$module"; then
    return 0
  fi
  if pip_install "$pkg" >/dev/null 2>&1; then
    test_python_module "$module"
    return $?
  fi
  return 1
}

run_step() {
  local name="$1"
  shift
  printf '%s\n' "==> $name"
  "$@"
  local code=$?
  if [[ $code -ne 0 ]]; then
    printf '%s\n' "FAIL ($code): $name" >&2
    had_failure=1
    if [[ $stop_on_first_error -eq 1 ]]; then
      exit "$code"
    fi
    return "$code"
  fi
  printf '%s\n' "OK: $name"
}

run_python_module() {
  local name="$1"
  local module="$2"
  shift 2
  run_step "$name" "$python_exe" -m "$module" "$@"
}

run_python_module_if_present() {
  local name="$1"
  local module="$2"
  local pkg="${3:-$module}"
  shift 2
  if ! ensure_python_module "$module" "$pkg"; then
    skipped+=("$name (missing python module: $module)")
    return 0
  fi
  run_python_module "$name" "$module" "$@"
}

get_python_files() {
  if test_cmd git; then
    if git ls-files -- "*.py" >/dev/null 2>&1; then
      git ls-files -- "*.py"
      return 0
    fi
  fi
  find src tests -type f -name "*.py" 2>/dev/null || true
}

run_python_module_if_present "black (check)" "black" --check src tests
run_python_module_if_present "isort (check-only)" "isort" --check-only src tests
run_python_module_if_present "flake8" "flake8" src tests
run_python_module_if_present "ruff" "ruff" check src tests

if ensure_python_module "pylint" "pylint"; then
  if [[ $pylint_full -eq 1 ]]; then
    run_python_module "pylint" "pylint" src tests
  else
    run_python_module "pylint (errors-only)" "pylint" --errors-only src tests
  fi
else
  skipped+=("pylint (missing python module: pylint)")
fi

py_files_raw="$(get_python_files)"
if [[ -n "${py_files_raw}" ]] && ensure_python_module "pyupgrade" "pyupgrade"; then
  if "$python_exe" -m pyupgrade --help 2>&1 | grep -Eq '(^|[[:space:]])--diff([[:space:]]|$)'; then
    mapfile -t py_files <<<"$py_files_raw"
    run_python_module "pyupgrade (diff)" "pyupgrade" --py38-plus --diff "${py_files[@]}"
  else
    skipped+=("pyupgrade (--diff unsupported)")
  fi
else
  if ! test_python_module "pyupgrade"; then
    skipped+=("pyupgrade (missing python module: pyupgrade)")
  fi
fi

run_python_module_if_present "radon cc" "radon" cc src -a

if test_cmd npx; then
  if npx --yes prettier --version >/dev/null 2>&1; then
    run_step "prettier (check)" npx --yes prettier --check '**/*.{md,json,yml,yaml}' --ignore-unknown
  else
    skipped+=("prettier (npx prettier unavailable)")
  fi
elif test_cmd npm; then
  if npm exec --yes prettier --version >/dev/null 2>&1; then
    run_step "prettier (check)" npm exec --yes prettier --check '**/*.{md,json,yml,yaml}' --ignore-unknown
  else
    skipped+=("prettier (npm exec prettier unavailable)")
  fi
else
  skipped+=("prettier (missing command: npx/npm)")
fi

if [[ ${#skipped[@]} -gt 0 ]]; then
  printf '\n%s\n' "Skipped:"
  for item in "${skipped[@]}"; do
    printf ' - %s\n' "$item"
  done
fi

if [[ $had_failure -ne 0 ]]; then
  exit 1
fi
exit 0
