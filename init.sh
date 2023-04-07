if [ -z "${VIRTUAL_ENV}" ]; then
    cd ${HOME}
    python3 -m venv py3env
    . ${HOME}/py3env/bin/activate
    echo "source ~/py3env/bin/activate" >> ~/.bashrc
fi
echo "Installing required modules"
pip install -U pyats[full]==21.12 genie==21.12 pyopenssl==21.0.0 markupsafe==2.0.1 cryptography==3.3.1 requests cmlutils Jinja2==2.11.3 ansible==2.9.27 paramiko==2.12.0 chardet==3.0.4

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
cml up -f ${LAB}/helper-files/Production.yaml >/dev/null 2>&1
cml up -f ${LAB}/helper-files/Testing.yaml >/dev/null 2>&1

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
