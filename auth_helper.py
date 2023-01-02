import os
import pathlib
import json
from typing import Optional, Union

import msal
import logging


class AuthError(RuntimeError):

    """Handle Auth Errors when attempting device_flow or recovery from cached token.
        :param result: The result of the failed attempt
    """

    result: Union[dict[str, Optional[int]], dict, dict[str, str], dict[str, Union[int, dict[str, str], str]], None]

    def __init__(self, result: Union[
                            dict[str, Optional[int]],
                            dict,
                            dict[str, str],
                            dict[str, Union[int, dict[str, str], str]],
                            None
                        ]
                 ) -> None:
        super().__init__()
        self.result = result

    def __str__(self) -> str:
        """Generate and return the string representation of the object.
        :return: A string representation of the object
        """
        if not self.result.get("error_message"):
            return f"AuthError: Fatal error in authentication - {self.result.__str__()}"
        else:
            return f"AuthError: Fatal error in authentication - {self.result.get('error_message')}"


class AuthHelper:
    def __init__(self, scope: Optional[str], app_id: Optional[str], log: Optional[logging.Logger]):
        if not scope:
            self.scope = os.environ["scope"]
        else:
            self.scope = scope
        if not app_id:
            self.app_id = os.environ["appId"]
        else:
            self.app_id = app_id
        if not log:
            self.log = logging.getLogger("ado")
            self.log.getChild("AuthHelper")
        else:
            self.log = log
            self.log.getChild("AuthHelper")

    def device_flow_auth(self) -> \
            Union[
                dict[str, Optional[int]],
                dict,
                dict[str, str],
                dict[str, Union[int, dict[str, str], str]],
                None
            ]:
        mscache = msal.SerializableTokenCache()
        output = pathlib.Path.home() / pathlib.Path("tokens") / pathlib.Path("token.bin")
        if os.path.exists(output):
            self.log.debug("Deserializing cached credentials.")
            mscache.deserialize(open(output, "r", encoding="utf-8").read())
            
        app = msal.PublicClientApplication(
            client_id=self.app_id,
            token_cache=mscache
        )
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(
                scopes=[self.scope],
                account=accounts[0]
            )
            if mscache.has_state_changed:
                with open(output, "w", encoding='utf-8') as cache_file:
                    self.log.debug("Caching credentials.")
                    cache_file.write(mscache.serialize())
                    cache_file.close()
            if result is not None:
                if "access_token" in result:
                    self.log.debug("Found access token.")
                    return result
                else:
                    raise AuthError(result=result)
        self.log.debug("Initiating device flow.")
        flow = app.initiate_device_flow(scopes=[self.scope])
        if "user_code" not in flow:
            raise ValueError("User code not in result. Error: %s" % json.dumps(flow, indent=5))
        print(flow["message"])  # Think this one needs to stay as a print so user sees the prompt
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            self.log.debug("Access token acquired.")
            if not pathlib.Path.is_dir(output.parent):
                pathlib.Path.mkdir(output.parent)
            if not pathlib.Path.exists(output):
                with open(output, "w", encoding='utf-8') as cache_file:
                    self.log.debug("Writing cached credentials.")
                    cache_file.write(mscache.serialize())
                    cache_file.close()
            else:
                with open(output, "w+", encoding='utf-8') as cache_file:
                    self.log.debug("Writing cached credentials.")
                    cache_file.write(mscache.serialize())
                    cache_file.close()
            return result
        else:
            self.log.debug("No access token found.")
            raise AuthError(result)
