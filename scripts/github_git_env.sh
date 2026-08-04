# GitHub access helper for this machine (bash).
# Usage:
#   source scripts/github_git_env.sh
#   git fetch && git push
#
# Fixes:
#   1) EDA LD_LIBRARY_PATH breaks system ssh OpenSSL
#   2) Direct DNS/SSH to github.com fails — HTTP proxy via ncat
#   3) Prefer SCL git 2.x + httpd24 libcurl for HTTPS remotes
#
# Override: export GITHUB_HTTP_PROXY=127.0.0.1:7890

_GITHUB_PROXY="${GITHUB_HTTP_PROXY:-127.0.0.1:7890}"
_NCAT="${NCAT_BIN:-/usr/bin/ncat}"
_SSH_BIN="${SSH_BIN:-/usr/bin/ssh}"

if [ ! -x "$_NCAT" ]; then
  echo "WARN: ncat not found at $_NCAT; SSH ProxyCommand may fail" >&2
fi

# Must be one string; ProxyCommand value quoted for ssh
# Note: OpenSSH 7.4 has no StrictHostKeyChecking=accept-new
export GIT_SSH_COMMAND="env -u LD_LIBRARY_PATH ${_SSH_BIN} -o ConnectTimeout=30 -o ProxyCommand=\"${_NCAT} --proxy ${_GITHUB_PROXY} --proxy-type http %h %p\""

if [ -z "${http_proxy:-}" ]; then
  export http_proxy="http://${_GITHUB_PROXY}"
fi
if [ -z "${https_proxy:-}" ]; then
  export https_proxy="http://${_GITHUB_PROXY}"
fi
export HTTP_PROXY="${HTTP_PROXY:-$http_proxy}"
export HTTPS_PROXY="${HTTPS_PROXY:-$https_proxy}"

if [ -f /opt/rh/rh-git227/enable ]; then
  # shellcheck disable=SC1091
  . /opt/rh/rh-git227/enable 2>/dev/null || true
fi
if [ -d /opt/rh/httpd24/root/usr/lib64 ]; then
  case ":${LD_LIBRARY_PATH:-}:" in
    *":/opt/rh/httpd24/root/usr/lib64:"*) ;;
    *) export LD_LIBRARY_PATH="/opt/rh/httpd24/root/usr/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
  esac
fi

_repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$_repo_root" ]; then
  # local config: plain git push uses this without re-sourcing
  git -C "$_repo_root" config --local core.sshCommand \
    "env -u LD_LIBRARY_PATH ${_SSH_BIN} -o ConnectTimeout=30 -o ProxyCommand=\"${_NCAT} --proxy ${_GITHUB_PROXY} --proxy-type http %h %p\""
fi

echo "github_git_env: proxy=${_GITHUB_PROXY}"
echo "github_git_env: git=$(command -v git 2>/dev/null) ($(git --version 2>/dev/null | head -1))"
echo "github_git_env: ready (ssh via ncat; https via proxy + rh-git if present)"
