"""Helper class for MSAL Device flow authentication."""

import json
import os
import pathlib
from typing import Any

import msal


class DeviceFlowHelper:

    tenant_id: str
    scope: str
    authority: str
    app_id: str
    accessToken: str

    def __init__(self, tenant_id: str, scope: str, authority: str, app_id: str):
        self.tenant_id = tenant_id
        self.scope = scope
        self.authority = authority
        self.app_id = app_id

    def ado_authenticate(self) -> Any:
        mscache = msal.SerializableTokenCache()
        output = pathlib.Path(__file__).parent / pathlib.Path("token.bin")

        if os.path.exists(output):
            print("Deserializing cached credentials.")
            with open(output, "r", encoding="utf-8") as cache_file:
                mscache.deserialize(cache_file.read())

        app = msal.PublicClientApplication(client_id=self.app_id, token_cache=mscache)
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes=[self.scope], account=accounts[0])
            if mscache.has_state_changed:
                with open(output, "w", encoding="utf-8") as cache_file:
                    print("Caching credentials.")
                    cache_file.write(mscache.serialize())

            if result is not None:
                if "access_token" in result:
                    print("Found access token.")
                    return result
                raise RuntimeError(result.get("error_description"))

        print("Initiating device flow.")

        flow = app.initiate_device_flow(scopes=[self.scope])

        if "user_code" not in flow:
            raise ValueError("User code not if result. Error: %s" % json.dumps(flow, indent=4))

        print(flow["message"])

        result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            print("No access token found.")
            raise RuntimeError(result.get("error_description"))

        print("Access token acquired.")

        if not os.path.exists(output):
            with open(output, "w", encoding="utf-8") as cache_file:
                print("Writing cached credentials.")
                cache_file.write(mscache.serialize())
                cache_file.close()

        else:
            with open(output, "w+", encoding="utf-8") as cache_file:
                print("Writing cached credentials.")
                cache_file.write(mscache.serialize())
                cache_file.close()

        return result
