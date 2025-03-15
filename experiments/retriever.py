import json

from langchain_community.retrievers import WikipediaRetriever
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from gen_ai_hub.proxy.langchain import ChatOpenAI
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

llm = ChatOpenAI(proxy_model_name="gpt-35-turbo", temperature=0, verbose=True, proxy_client=proxy_client)


retriever = WikipediaRetriever(load_all_available_meta=True, top_k_results=1)
docs = retriever.invoke("Outlook")

# print(len(docs[0].page_content))  # content of the Document
# print(docs[0].metadata)  # meta-information of the Document)

prompt_template = PromptTemplate.from_template(
    '''You are helping to make a software or hardware inventory, and its name is your input.
       Your task is to return a short description of the input, the name of the company that provides it,
       and its status (for example, supported, end of life).
       Return the information in a json format with the following keys: description, provider, status.
       The json format should be: {{"description": xxx, "provider": xxx, "status": xxx}}. 
       Use the below article to search for details on the input.

       Article: {article}
       Input: {input}
    ''')


# prompt = prompt_template.format(article=docs[0], input="Windows XP")
llm_chain = LLMChain(prompt=prompt_template, llm=llm)
response = llm_chain.invoke({
        "input": "Jenkins",
        "article": docs[0].page_content
    })
print(response['text'])
