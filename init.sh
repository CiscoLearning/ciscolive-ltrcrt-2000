echo "Installing required modules"
pip install -U pyats[full] genie cryptography==3.3.1 requests cmlutils Jinja2=2.11.2 ansible==2.9.17

init_common

echo "Cleaning up leftover cmlutils files"
rm -rf ${HOME}/.virl

echo "Copying initial files"
cp -f ${LAB}/init/virlrc ${HOME}/.virlrc
cp -rf ${LAB}/init/iac-infra ${LABDIR}
cp -f ${LAB}/init/vlan-fabric.yml ${LABDIR}

echo "Shutting down default CML lab"
cml down -n "Multi Platform Network"

echo "Shutting down and deleting any previous labs"
(cml use -n "Production" && cml rm -f --no-confirm) >/dev/null 2>&1 || true
(cml use -n "Testing" && cml rm -f --no-confirm) >/dev/null 2>&1 || true

echo "Spinning up lab HOLOPS-2800 lab topologies"
cml up -f ${LAB}/helper-files/Production.yaml >/dev/null 2>&1
cml up -f ${LAB}/helper-files/Testing.yaml >/dev/null 2>&1

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
