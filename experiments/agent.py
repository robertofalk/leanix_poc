import json

from gen_ai_hub.proxy.langchain import ChatOpenAI
from gen_ai_hub.proxy.core import get_proxy_client

from langchain.agents import Tool
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain.agents import create_openai_tools_agent

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

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

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper)


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", '''You are helping to make a software and hardware inventary. 
                      Use the tool to search for details on the input. Then based on the information returned,
                      create a short description of the input, the name of the company that provides the hardware or software,
                      and the status of it (for example, supported, end of life).
                      Return the information in a json format with the following keys: description, provider, status.
                      The return format should be like this: {{"description": xxx, "provider": xxx, "status": xxx}}. 
                   '''
         ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

tools = [Tool(  
     name=wiki.name,  
     func=wiki.run,  
     description=wiki.description  
 )]  

# agent = create_tool_calling_agent(llm, [tool], prompt)
agent = create_openai_tools_agent(llm, tools, prompt) 

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
reply = agent_executor.invoke(
    {
        "input": "Windows XP"
    })
print(reply['output'])