"""
.. module: hubcommander.auth_plugins.duo.plugin
    :platform: Unix
    :copyright: (c) 2017 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.

.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import json

from duo_client.client import Client

from hubcommander.bot_components.bot_classes import BotAuthPlugin
from hubcommander.bot_components.slack_comm import send_info, send_error, send_success


class InvalidDuoResponseError(Exception):
    pass


class CantDuoUserError(Exception):
    pass


class NoSecretsProvidedError(Exception):
    pass


class DuoPlugin(BotAuthPlugin):
    def __init__(self):
        super().__init__()

        self.clients = {}

    def setup(self, secrets, **kwargs):
        for variable, secret in secrets.items():
            if "DUO_" in variable:
                domain, host, ikey, skey = secret.split(",")
                self.clients[domain] = Client(ikey, skey, host)

        if not len(self.clients):
            raise NoSecretsProvidedError("Must provide secrets to enable authentication.")

    def authenticate(self, data, user_data, **kwargs):
        # Which domain does this user belong to?
        domain = user_data["profile"]["email"].split("@")[1]
        if not self.clients.get(domain):
            send_error(data["channel"], "💀 @{}: Duo in this bot is not configured for the domain: `{}`. It needs "
                                        "to be configured for you to run this command."
                       .format(user_data["name"], domain), markdown=True, thread=data["ts"])
            return False

        send_info(data["channel"], "🎟 @{}: Sending a Duo notification to your device. You must approve!"
                  .format(user_data["name"]), markdown=True, ephemeral_user=user_data["id"])

        try:
            result = self._perform_auth(user_data, self.clients[domain])
        except InvalidDuoResponseError as idre:
            send_error(data["channel"], "💀 @{}: There was a problem communicating with Duo. Got this status: {}. "
                                        "Aborting..."
                       .format(user_data["name"], str(idre)), markdown=True)
            return False

        except CantDuoUserError as _:
            send_error(data["channel"], "💀 @{}: I can't Duo authenticate you. Please consult with your identity team."
                                        " Aborting..."
                       .format(user_data["name"]), markdown=True)
            return False

        except Exception as e:
            send_error(data["channel"], "💀 @{}: I encountered some issue with Duo... Here are the details: ```{}```"
                       .format(user_data["name"], str(e)), markdown=True)
            return False

        if not result:
            send_error(data["channel"], "💀 @{}: Your Duo request was rejected. Aborting..."
                       .format(user_data["name"]), markdown=True, thread=data["ts"])
            return False

        # All Good:
        send_success(data["channel"], "🎸 @{}: Duo approved! Completing request..."
                     .format(user_data["name"]), markdown=True, ephemeral_user=user_data["id"])
        return True

    def _perform_auth(self, user_data, client):
        # Push to devices:
        duo_params = {
            "username": user_data["profile"]["email"],
            "factor": "push",
            "device": "auto"
        }
        response, data = client.api_call("POST", "/auth/v2/auth", duo_params)
        result = json.loads(data.decode("utf-8"))

        if response.status != 200:
            raise InvalidDuoResponseError(response.status)

        if result["stat"] != "OK":
            raise CantDuoUserError()

        if result["response"]["result"] == "allow":
            return True

        return False
