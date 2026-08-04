# GitHub access helper for this machine (csh/tcsh).
# Usage:
#   source scripts/github_git_env.csh
#   git fetch / git push

if (! $?GITHUB_HTTP_PROXY) setenv GITHUB_HTTP_PROXY 127.0.0.1:7890
if (! $?NCAT_BIN) setenv NCAT_BIN /usr/bin/ncat
if (! $?SSH_BIN) setenv SSH_BIN /usr/bin/ssh

setenv GIT_SSH_COMMAND "env -u LD_LIBRARY_PATH ${SSH_BIN} -o ConnectTimeout=30 -o ProxyCommand=\"${NCAT_BIN} --proxy ${GITHUB_HTTP_PROXY} --proxy-type http %h %p\""

if (! $?http_proxy) setenv http_proxy "http://${GITHUB_HTTP_PROXY}"
if (! $?https_proxy) setenv https_proxy "http://${GITHUB_HTTP_PROXY}"
if (! $?HTTP_PROXY) setenv HTTP_PROXY "$http_proxy"
if (! $?HTTPS_PROXY) setenv HTTPS_PROXY "$https_proxy"

if ( -f /opt/rh/rh-git227/enable ) then
  # enable script is bash; set PATH/LD manually for csh
  if ( -d /opt/rh/rh-git227/root/usr/bin ) then
    setenv PATH /opt/rh/rh-git227/root/usr/bin:$PATH
  endif
endif
if ( -d /opt/rh/httpd24/root/usr/lib64 ) then
  if ($?LD_LIBRARY_PATH) then
    setenv LD_LIBRARY_PATH /opt/rh/httpd24/root/usr/lib64:$LD_LIBRARY_PATH
  else
    setenv LD_LIBRARY_PATH /opt/rh/httpd24/root/usr/lib64
  endif
endif

set _repo_root = `git rev-parse --show-toplevel`
if ( "$status" == 0 && "$_repo_root" != "" ) then
  git -C "$_repo_root" config --local core.sshCommand "env -u LD_LIBRARY_PATH ${SSH_BIN} -o ConnectTimeout=30 -o ProxyCommand=\"${NCAT_BIN} --proxy ${GITHUB_HTTP_PROXY} --proxy-type http %h %p\""
endif

echo "github_git_env: proxy=${GITHUB_HTTP_PROXY}"
echo "github_git_env: GIT_SSH_COMMAND set"
