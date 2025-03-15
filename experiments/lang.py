import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from gen_ai_hub.proxy.langchain.init_models import init_llm

from gen_ai_hub.proxy.core import get_proxy_client

cred = None
with open('key.json') as f:
    cred = json.load(f)

proxy_client = proxy_client=get_proxy_client(
        base_url=f'{cred['serviceurls']['AI_API_URL']}/v2',
        auth_url=f'{cred['url']}/oauth/token',
        client_id=cred['clientid'],
        client_secret=cred['clientsecret'],
        resource_group='default'
    )

template = """Question: {question}
    Answer: Let's think step by step."""
prompt = PromptTemplate(template=template, input_variables=['question'])
question = 'What is a supernova?'

llm = init_llm('gpt-35-turbo', max_tokens=100, proxy_client=proxy_client)
llm_chain = LLMChain(prompt=prompt, llm=llm)
response = llm_chain.invoke(question)
print(response['text'])