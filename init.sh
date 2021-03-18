echo "Installing required modules"
pip install -U pyats genie requests cmlutils ansible==2.19.17

init_common

echo "Copying initial files"
cp -f ${LAB}/init/virlrc ${HOME}/.virlrc

echo "Shutting down default CML lab"
cml down -n "Multi Platform Network"

echo "Spinning up lab HOLOPS-2800 lab topologies"
cml up -f ${LAB}/helper-files/Production.yaml
cml up -f ${LAB}/helper-files/Testing.yaml

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
