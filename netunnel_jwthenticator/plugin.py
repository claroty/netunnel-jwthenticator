"""
This plugin add support for JWThenticator on NETunnel.
IMPORTANT
We do not verify the tokens generated by the JWThenticator server, the setup must include
some type of reverse proxy which validates the tokens directly with JWThenticator.
"""
from uuid import UUID
from typing import Optional, Any, Dict
from netunnel.common.auth import NETunnelServerAuth, NETunnelClientAuth
from netunnel.client import NETunnelClient
from netunnel.common.exceptions import NETunnelNotAuthenticatedError, NETunnelAuthError
from jwthenticator.client import Client
from jwthenticator.exceptions import AuthenticationError
from aiohttp import web
from yurl import URL

import os
import ssl


def get_verify_ssl(ssl_context: Optional[ssl.SSLContext]) -> bool:
    """
    NETunnel expects an SSLContext object and None considered "True" while JWThenticator expects a boolean.
    We "degrade" the SSLContext to boolean value to support JWThenticator's expected value
    """
    if ssl_context is False or (isinstance(ssl_context, ssl.SSLContext) and ssl_context.verify_mode is ssl.VerifyMode.CERT_NONE):
        return False
    return True


class JWThenticatorAuthServer(NETunnelServerAuth):
    def __init__(self, remote_uri: Optional[str] = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._remote_uri = remote_uri or os.environ.get('JWTHENTICATOR_URI', '/jwthenticator')

    async def get_client_for_peer(self, key: Optional[str] = None, refresh_token: Optional[str] = None,
                                  uuid: Optional[UUID] = None) -> NETunnelClientAuth:
        return JWThenticatorAuthClient(key=key, refresh_token=refresh_token, uuid=uuid, remote_uri=self._remote_uri)

    async def is_authenticated(self, request: web.Request) -> bool:
        """
        As mentioned above, the request's headers should be verified by an external webserver.
        """
        return True

    async def authenticate(self, request: web.Request) -> None:
        """
        This will never be called. The JWThenticator on the server-side will validate the request
        """
        raise RuntimeError('Authentication should be handled by an external JWThenticator server')


class JWThenticatorAuthClient(NETunnelClientAuth):
    def __init__(self, key: Optional[str] = None, refresh_token: Optional[str] = None, remote_uri: Optional[str] = None,
                 uuid: Optional[str] = None, *args: Any, **kwargs: Any):
        self._remote_uri = remote_uri or os.environ.get('JWTHENTICATOR_URI', '/jwthenticator')
        super().__init__(*args, **kwargs)
        if key is None and refresh_token is None:
            raise ValueError('Either `key` or `refresh_token` must be given')
        self._key = key
        self._refresh_token = refresh_token
        self._uuid = UUID(uuid or "00000000-0000-0000-0000-000000000000")
        self._jwthenticator_client: Client = None

    async def authenticate(self, client: 'NETunnelClient', *args: Any, **kwargs: Any) -> None:
        netunnel_url = URL(client.server_url)
        jwthenticator_url = netunnel_url.replace(path=self._remote_uri)
        self._jwthenticator_client = Client(jwthenticator_url.as_string(), identifier=self._uuid, key=self._key,
                                      refresh_token=self._refresh_token, verify_ssl=get_verify_ssl(client.ssl))
        try:
            if self._key:
                await self._jwthenticator_client.authenticate()
                self._refresh_token = self._jwthenticator_client.refresh_token
            else:
                await self._jwthenticator_client.refresh()
        except AuthenticationError:
            raise NETunnelAuthError(f'Failed to authenticate with `{jwthenticator_url}`')

    async def is_authenticated(self) -> bool:
        return self._jwthenticator_client is not None and not self._jwthenticator_client.is_jwt_expired

    async def get_authorized_headers(self) -> Dict[str, str]:
        if not await self.is_authenticated():
            raise NETunnelNotAuthenticatedError('Cannot generate authorized headers without authenticating first')
        return {'Authorization': f"Bearer {self._jwthenticator_client.jwt}"}

    def dump_object(self) -> Dict[str, Any]:
        if self._refresh_token is None:
            raise NETunnelNotAuthenticatedError('Cannot dump object without authenticating first')
        return {'refresh_token': self._refresh_token, 'uuid': str(self._uuid)}
