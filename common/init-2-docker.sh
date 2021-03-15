# Prune the Docker system

echo "Pruning Docker system"
[ -n "$(docker ps -aq)" ] && docker stop $(docker ps -aq) >/dev/null 2>&1
[ -n "$(docker ps -aq)" ] && docker rm -f $(docker ps -aq) >/dev/null 2>&1
[ -n "$(docker images -q)" ] && docker rmi $(docker images -q) >/dev/null 2>&1
[ -n "$(docker volume ls -q)" ] && docker volume rm $(docker volume ls -q) >/dev/null 2>&1
docker system prune -a -f >/dev/null 2>&1
