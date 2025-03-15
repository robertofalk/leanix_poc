import json
import time

from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
from ai_api_client_sdk.models.status import Status
from ai_api_client_sdk.models.parameter_binding import ParameterBinding

from gen_ai_hub.proxy.core import get_proxy_client
from gen_ai_hub.proxy import set_proxy_version

set_proxy_version("gen-ai-hub")
from gen_ai_hub.proxy.native.openai.clients import OpenAI

RESOURCE_GROUP = "default"
MODEL_NAME = "gpt-35-turbo"
MODEL_VERSION = "0613"

SINGLE = {}


def load_credentials():
    cred = None
    with open('key.json') as f:
        cred = json.load(f)
    
    return cred

def create_ai_api_client():

    cred = load_credentials()

    base_url = f'{cred['serviceurls']['AI_API_URL']}/v2/lm'
    auth_url = f'{cred['url']}/oauth/token'
    client_id = cred['clientid']
    client_secret = cred['clientsecret']

    aicore_client = AIAPIV2Client(
        base_url=base_url,
        auth_url=auth_url,
        client_id=client_id,
        client_secret=client_secret,
        resource_group=RESOURCE_GROUP
    )

    return aicore_client

def deploy_model(client: AIAPIV2Client):
    config = client.configuration.create(
                name=f"Model: {MODEL_NAME}, version: {MODEL_VERSION}",
                scenario_id="foundation-models",
                executable_id="azure-openai",
                parameter_bindings=[
                    ParameterBinding("modelName", MODEL_NAME),
                    ParameterBinding("modelVersion", MODEL_VERSION),
                ],
                input_artifact_bindings=[],
                resource_group=RESOURCE_GROUP)
    
    deployment_id = client.deployment.create(
        configuration_id=config.id, resource_group=RESOURCE_GROUP
    )
    return deployment_id

def wait_for_deployment(client, deployment_id):
    sleep_time = 6 #seconds
    i = 10

    deployment = client.deployment.get(deployment_id=deployment_id, resource_group=RESOURCE_GROUP)
    while deployment.status.value != deployment.target_status.value:
        
        if i == 0:
            break

        time.sleep(sleep_time)
        i -= 1
        deployment = client.deployment.get(deployment_id=deployment_id, resource_group=RESOURCE_GROUP)

    if deployment.status.value != deployment.target_status.value:
        raise RuntimeError(f"The model didn't reach state {deployment.target_status.value} after 1 minute")
    return deployment

def delete_all_deployments(client):
    deployments = client.deployment.query(resource_group=RESOURCE_GROUP).resources
    for deployment in deployments:
        if deployment.status == Status.RUNNING:
            client.deployment.modify(deployment_id=deployment.id, resource_group=RESOURCE_GROUP, target_status=Status.STOPPED)
    
    time.sleep(10)
    deployments = client.deployment.query(resource_group=RESOURCE_GROUP).resources
    for deployment in deployments:
        client.deployment.delete(deployment_id=deployment.id, resource_group=RESOURCE_GROUP)

def search_deployment(client):
    # Check first if deployment is already there
    deployments = client.deployment.query(resource_group=RESOURCE_GROUP).resources

    for deployment in deployments:
        if deployment.status == Status.RUNNING:
            deployment_config = client.configuration.get(
                configuration_id=deployment.configuration_id, resource_group=RESOURCE_GROUP
            )

            if any(p.key == 'modelName' and p.value == MODEL_NAME for p in deployment_config.parameter_bindings) and \
            any(p.key == 'modelVersion' and p.value == MODEL_VERSION for p in deployment_config.parameter_bindings):
                return deployment
    return None


def map_deployments(client):
    # Check first if deployment is already there
    deployments = client.deployment.query(resource_group=RESOURCE_GROUP).resources

    for deployment in deployments:
        if deployment.status == Status.RUNNING:
            deployment_config = client.configuration.get(
                configuration_id=deployment.configuration_id, resource_group=RESOURCE_GROUP
            )

            if (deployment_config.parameter_bindings[0].value, deployment_config.parameter_bindings[1].value) not in SINGLE:
                SINGLE[(deployment_config.parameter_bindings[0].value, deployment_config.parameter_bindings[1].value)] = deployment
            else:
                client.deployment.modify(deployment_id=deployment.id, resource_group=RESOURCE_GROUP, target_status=Status.STOPPED)
        
        elif deployment.status in [Status.UNKNOWN, Status.STOPPED]:
            client.deployment.delete(deployment_id=deployment.id, resource_group=RESOURCE_GROUP)
        else:
            client.deployment.modify(deployment_id=deployment.id, resource_group=RESOURCE_GROUP, target_status=Status.STOPPED)

    return SINGLE

def get_deployment(client):
    # Try do find existing deployment for the expected model
    deployment = search_deployment(client)

    if not deployment:
        deployment_id = deploy_model(client)
        deployment = wait_for_deployment(client, deployment_id)

    return deployment

def list_scenarios(client):
    scenarios = client.executable.query(resource_group=RESOURCE_GROUP, scenario_id="foundation-models")
    print(scenarios)

def run(text: str):
    # ensure model is deployed
    aicore_client = create_ai_api_client()
    list_scenarios(aicore_client)
    # delete_all_deployments(aicore_client)
    map_deployments(aicore_client)
    deployment = get_deployment(aicore_client)
    
    # now the fun part
    cred = load_credentials()
    open_ai =  OpenAI(proxy_client=get_proxy_client(
        base_url=f'{cred['serviceurls']['AI_API_URL']}/v2',
        auth_url=f'{cred['url']}/oauth/token',
        client_id=cred['clientid'],
        client_secret=cred['clientsecret'],
        resource_group=RESOURCE_GROUP
    ))

    message = {
        'role': 'user',
        'content': text
    }

    response = open_ai.chat.completions.create(messages=[message], deployment_id=deployment.id)
    print(response.choices[0].message.content)

run('Is Darth Maul the best sith of all times?')
