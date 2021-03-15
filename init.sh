echo "Installing required modules"
pip install pyats genie requests cmlutils

init_common

echo "Copying initial files"
cp ${LAB}/init/virlrc ${LABDIR}/.virlrc


echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
