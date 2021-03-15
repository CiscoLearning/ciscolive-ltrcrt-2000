echo "Installing required modules"
pip install pyats genie requests cmlutils

echo "Creating cml-iac directory"
mkdir -p ${HOME}/cml-iac
#cp -r ${LAB}/init/* ${HOME}/cml-iac
cp ${LAB}/init/virlrc ${HOME}/cml-iac/.virlrc

init_common

echo "Spinning up GitLab-CE"
cwd=$(pwd)
cd ${LAB}/gitlab
make
cd ${cwd}
