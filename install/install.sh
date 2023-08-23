mkdir static
mkdir socket
mkdir log

chmod 777 socket
branch = "x"
psql -d test -c "create database backend_$(echo $branch);"
psql -d echo "backend_$(echo $branch)" -c "GRANT ;"