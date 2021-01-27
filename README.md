# NETunnel-JWThenticator
An authentication plugin of [NETunnel](https://github.com/claroty/netunnel) that
uses [JWThenticator](https://github.com/claroty/jwthenticator) to provide key-based
authentication between **peers**.

The plugin designed to be used in a server-server NETunnel models (although it can
be used in a client-server model as well) where each machine has a web server
that exposes a JWThenticator and a NETunnel service.
The web server protects the NETunnel routes by verifying that the JWT token
in every request's `Authorization` header is signed by the local JWThenticator
service.

When a new peer is registered on a NETunnel server, you'll need to provide a
key, which you're obligated to make sure it is registered on the remote
JWThenticator server.
The plugin will make a request to the remote JWThenticator server for a refresh
token, using the provided key. The refresh token will be stored as the auth data
of this peer, and for every new request, the plugin will make sure there is a
valid JWT token that it received from the remote JWTheneticator server using the
refresh token. 

## Getting Started
### Installing
```bash
pip install netunnel-jwthenticator
```
### Usage
The plugin was designed to be used in a server-server model of NETunnel, so the
examples will focus on that. Each machine should have a running JWThenticator server
and a NETunnel server with this plugin activated:
```bash
python -m netunnel.server --auth-plugin netunnel_jwthenticator.JWThenticatorAuthServer
```
Make sure both the JWThenticator and NETunnel are listening only on localhost, and
have your web server proxy NETunnel on `/netunnel` and JWThenticator on `/jwthenticator`.
expose only the "public" routes for JWThenticator:
- `/authenticate`
- `/refresh`
- `/validate`
- `/jwks`

As for NETunnel, have your web server expose the following routes only after validating
the JWT token of each request: 
- `/version`
- `/channels`
- `/channels/*`

For example, for an NGINX web server, you could use the `auth_request` directive to
achieve that:
```
http {
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    server {
        listen 443 ssl;
        
        location /netunnel/ {
            auth_request _jwthenticator_validate;
            if ($uri !~ "^/netunnel/version$|^/netunnel/channels$|^/netunnel/channels/.+$") {
                return 403;
            }
            rewrite /netunnel/(.*) /$1 break;
            proxy_pass http://127.0.0.1:4040;

            # support websockets
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
        }
        
        location /jwthenticator/ {
            if ($uri !~ "^/jwthenticator/authenticate$|^/jwthenticator/refresh$|^/jwthenticator/validate$|^/jwthenticator/jwks$") {
                return 403;
            }
            rewrite /jwthenticator/(.*) /$1 break;
            proxy_pass http://127.0.0.1:5050;
        }
        
        location _jwthenticator_validate {
            internal;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_pass http://127.0.0.1:5050/validate_request;
        }
    }
}
```

### Custom URIs
If you wish to use different URIs than `/netunnel` and `/jwthenticator`, you can do so for NETunnel, you'll
anyway need to provide the full URL when registering the peer.
As for JWThenticator, the plugin assumes the remote JWThenticator is at `/jwthenticator`,
so you'll have to initialize it differently by either providing the following flag to
netunnel server: `--auth-data '{"remote_uri": "<new-uri>"}'` or by settings the following
environment before starting the server: `export JWTHENTICATOR_URI=<new-uri>`
