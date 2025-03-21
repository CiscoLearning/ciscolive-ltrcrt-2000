if [ -z "${VIRTUAL_ENV}" ]; then
    cd ${HOME}
    python3 -m venv .venv
    . ${HOME}/.venv/bin/activate
    echo "source ~/.venv/bin/activate" >>~/.bashrc
fi
echo "Installing required modules"
pip install -r $LAB/dependencies/requirements.txt

init_common

echo "Cleaning up leftover cmlutils files"
rm -rf ${HOME}/.virl

echo "Copying initial files"
cp -f ${LAB}/init/virlrc ${HOME}/.virlrc
cp -rf ${LAB}/init/iac-infra ${LABDIR}
cp -f ${LAB}/init/vlan-fabric.yml ${LABDIR}

echo "Shutting down and deleting any previous labs"
(cml use -n "Production" && cml rm -f --no-confirm) >/dev/null 2>&1 || true
(cml use -n "Testing" && cml rm -f --no-confirm) >/dev/null 2>&1 || true

echo "Spinning up LTRCRT-2000 lab topologies"
cml up -f ${LAB}/helper-files/production-iol.yaml >/dev/null 2>&1
cml up -f ${LAB}/helper-files/testing-iol-new.yaml >/dev/null 2>&1

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
