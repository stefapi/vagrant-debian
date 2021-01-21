#!/usr/bin/env bash
# this file is used to destroy a vagrant machine from the project and launch a fresh new one

pipenv install
pipenv update
pipenv run pip freeze > requirements.txt
vagrant box list | grep -w "^debian"
if [[ $? != 0 ]]
then
  cd vagrant || exit
  pipenv run python ./create_debianbox.py create -c fr --clean --add --headless
  cd ..
fi
vagrant destroy -f
vagrant up
