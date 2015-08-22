#!/bin/bash

/app/compose/django/entrypoint.sh :

USER=docker_{{ cookiecutter.repo_name }}

# rename django username to docker_{{ cookiecutter.repo_name }}
usermod -l $USER -m -d /home/$USER django
groupmod -n $USER django

mkdir /home/$USER/.ssh
cat /app/compose/debug/keys_to_docker/id_rsa.pub > /home/$USER/.ssh/authorized_keys

chmod 755 /home/$USER
chmod 700 /home/$USER/.ssh
chmod 600 /home/$USER/.ssh/authorized_keys
chown -R $USER:$USER /home/$USER

echo "$USER:docker" | chpasswd

service ssh start

cat /app/compose/debug/welcome_msg

sleep infinity
