#!/bin/bash
set -ev
# If CI on master branch then tag with latest
echo $TRAVIS_BRANCH
echo $TRAVIS_PULL_REQUEST

if [ "$TRAVIS_BRANCH" = "master" ] && [ "$TRAVIS_PULL_REQUEST" = "false" ] ; then

    cd $BLUEBIRD_HOME

    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt update
    sudo apt -y install docker-ce
    echo '{ "experimental": true }' | sudo tee /etc/docker/daemon.json
    sudo service docker restart
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    # Although there is a warning, the creds are hashed on the travis end first
    cat /home/travis/.docker/config.json

    TAG_VERSION=`git describe --tags`
    echo $TAG_VERSION
    docker build --tag=bluebird .
    for tag in {$TAG_VERSION,latest}; do
        docker tag bluebird turinginst/bluebird:${tag}
        docker push turinginst/bluebird:${tag}
    done
fi
