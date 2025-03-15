import json
import time

from functools import cache

from gen_ai_hub.proxy.core import get_proxy_client
from ai_api_client_sdk.models.status import Status
from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
from ai_api_client_sdk.models.parameter_binding import ParameterBinding

from llm.ai_core_credentials import load_credentials

RESOURCE_GROUP = "default"

@cache
def get_ai_core_client():
    cred = load_credentials()
    return get_proxy_client(
        base_url=f"{cred['serviceurls']['AI_API_URL']}/v2",
        auth_url=f"{cred['url']}/oauth/token",
        client_id=cred['clientid'],
        client_secret=cred['clientsecret'],
        resource_group='default'
    )


def _wait_for_ai_core(client, deployment_id):
    sleep_time = 5 # seconds
    timeout = 10

    while timeout > 0:
        deployment = client.deployment.get(deployment_id=deployment_id, resource_group=RESOURCE_GROUP)
        if deployment.status.value == deployment.target_status.value:
            return True
        
        time.sleep(sleep_time)
        timeout -= 1
    return False

def _search_deployment(client: AIAPIV2Client, model_name: str, model_version: str):
    # Check first if deployment is already there
    deployments = client.deployment.query(resource_group=RESOURCE_GROUP).resources

    for deployment in deployments:
        if deployment.status == Status.RUNNING:
            deployment_config = client.configuration.get(
                configuration_id=deployment.configuration_id, resource_group=RESOURCE_GROUP
            )

            if any(p.key == 'modelName' and p.value == model_name for p in deployment_config.parameter_bindings) and \
            any(p.key == 'modelVersion' and p.value == model_version for p in deployment_config.parameter_bindings):
                return deployment
    return None

def deploy_model(client: AIAPIV2Client, model_name: str, model_version: str):
    config = client.configuration.create(
                name=f"Model: {model_name}, version: {model_version}",
                scenario_id="foundation-models",
                executable_id="azure-openai",
                parameter_bindings=[
                    ParameterBinding("modelName", model_name),
                    ParameterBinding("modelVersion", model_version),
                ],
                input_artifact_bindings=[],
                resource_group=RESOURCE_GROUP)
    
    deployment = client.deployment.create(
        configuration_id=config.id, resource_group=RESOURCE_GROUP
    )

    if not _wait_for_ai_core(client, deployment.id):
        raise RuntimeError("LLM deployment failed")
    return deployment.id


def ensure_llm(model_name: str, model_version: str = None):
    gen_ai_client = get_ai_core_client()

    deployment = _search_deployment(gen_ai_client.ai_core_client, model_name, model_version)
    if not deployment:
        deployment_id = deploy_model(gen_ai_client.ai_core_client, model_name, model_version)
        deployment = gen_ai_client.ai_core_client.deployment.get(deployment_id=deployment_id, resource_group=RESOURCE_GROUP)
    return deployment