import os
import json
from functools import cache


@cache
def load_credentials():

    ai_core_credentials = None
    if "VCAP_SERVICES" in os.environ:
        vcap_services = json.loads(os.getenv("VCAP_SERVICES"))
        ai_core_credentials = vcap_services["aicore"][0]["credentials"]
    else:
        with open('key.json') as f:
            ai_core_credentials = json.load(f)

    return ai_core_credentials
