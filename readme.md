https://www.vultr.com/docs/how-to-deploy-fastapi-applications-with-gunicorn-and-nginx-on-ubuntu-20-04/

todo: https://github.com/tiangolo/fastapi/issues/858


to renew the certificate run:
    sudo certbot renew --dry-run
    
 
## Docker Usage
You are able to deploy a PostgreSQL server and the LleidaHack Backend through Docker:
> `docker compose up --build`

**NOTE:** You are able to change the database default password and username modifying the `docker-compose.yaml` file. Nevertheless, is strongly recommended to modify the DB password after setting up.