### This file generates the cert and key needed for flask to run ###
### Only needed once for setup ###
mkdir -p certs
cd certs
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=localhost"
