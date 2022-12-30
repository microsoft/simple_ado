import os
import json5
import sys
import requests
import msal

class AuthHelper:
    tenantId = os.environ["tenant_id"]
    scope = os.environ["scope"]
    authority = os.environ["authority"]
    appId = os.environ["appId"]
    accessToken = ""
    def __init__(self,**kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)

    def adoAuthenticate(self):
        mscache = msal.SerializableTokenCache()
        output = os.path.join("auth", "token.bin")
        if os.path.exists(output):
            mscache.deserialize(open(output, "r").read())
            
        app = msal.PublicClientApplication(
            client_id=self.appId,
            token_cache=mscache
        )

        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(
                scopes=[self.scope],
                account=accounts[0]
            )
            if mscache.has_state_changed:
                with open(output, "w") as cache_file:
                    cache_file.write(mscache.serialize())
            if result is not None:
                if "access_token" in result:
                    return result
                else:
                    raise RuntimeError(result.get("error_description"))

        flow = app.initiate_device_flow(scopes=[self.scope])

        if "user_code" not in flow:
            raise ValueError("User code not if result. Error: %s" % json5.dumps(flow, indent=5))

        result = app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            if os.path.exists(output):
                with open(output, "w") as cache_file:
                    cache_file.write(mscache.serialize())
                    cache_file.close()
            else:
                with open(output,"w+") as cache_file:
                    cache_file.write(mscache.serialize())
                    cache_file.close()
            return result
        else:
            raise RuntimeError(result.get("error_description"))
        return ""
