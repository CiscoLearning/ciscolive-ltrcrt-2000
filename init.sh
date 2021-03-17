echo "Installing required modules"
pip install pyats genie requests cmlutils

init_common

echo "Copying initial files"
cp ${LAB}/init/virlrc ${HOME}/.virlrc

echo "Shutting down default CML lab"
cml down -n "Multi Platform Network"

# TODO: Import Production configuration

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
