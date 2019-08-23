#!/bin/sh

cd $(dirname $0)/../../..

pgroup () {
  printf '##[group]'
  echo "$@"
  "$@"
  echo '##[endgroup]'
}

case "$1" in
  -c)
    printf '##[group]Set fedora remote'
    git remote rename origin github
    git remote add origin https://src.fedoraproject.org/rpms/ghdl.git
    git fetch origin
    git checkout -b tmp github/master
    git branch -u origin/master
    echo '##[endgroup]'

    pgroup dnf builddep -y ghdl.spec
    pgroup fedpkg sources
    pgroup fedpkg local
  ;;
  *)
    printf '##[group]Update GHDL tarball'
    git clone https://github.com/ghdl/ghdl
    cd ghdl
    GHDL_GITVER="$(git log -1 --date=short --pretty=format:%cd | sed 's/-//g')git$(git rev-parse --short=8 --verify HEAD)"
    cd ..
    tar cvJf ghdl.${GHDL_GITVER}.tar.bz2 --exclude-vcs ghdl
    sed -i.bak "s/.*ghdl.*/$(sha512sum ghdl.${GHDL_GITVER}.tar.bz2 | sed 's/\(.*\) \(.*\)/SHA512 (\2) = \1/g')/g" sources
    sed -i.bak 's/\(%global ghdlgitrev\).*/\1 .'"${GHDL_GITVER}"'/g' ghdl.spec
    echo '##[endgroup]'

    docker run --rm -v /$(pwd):/wrk -w //wrk ghdl/dist:rpm ./.github/actions/latest/run.sh -c
  ;;
esac
