
import json

from gen_ai_hub.proxy.langchain import ChatOpenAI

from llm.ai_core import get_ai_core_client, ensure_llm

from langchain_community.retrievers import WikipediaRetriever
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.exceptions import OutputParserException

from persistence.inventory_item import InventoryItem



class NotFoundError(RuntimeError):
    pass

class NoNewRevision(RuntimeError):
    pass

class Inventory(BaseModel):
    description: str = Field(description="Short description of the software or hardware provided as input")
    provider: str = Field(description="Name of the company that provides the software or hardware provided as input")
    status: str = Field(description="Status of the software or hardware provided as input")
    new_name: str = Field(description="New name of the software or hardware provided as input, if any", default=None)


class LLMRetriever:

    # The list of models can be found here:
    # https://help.sap.com/docs/sap-ai-core/sap-ai-core-service-guide/models-and-scenarios-in-generative-ai-hub?locale=en-US#models
    MODEL_NAME = "gpt-35-turbo"
    MODEL_VERSION = "0613"

    PROMPT = '''You are assisting in creating a software or hardware inventory. Given the name of a product as input, 
                your task is to return a very brief description of the input, the name of the company that provides it,
                its status (e.g., supported, renamed or end of life) and if there were any name changes 
                (indicating the product continued under a different name). Only consider it a new name if the product 
                continued with a different name, not just a version change.
                Return the information in a json format with the following keys: description, provider, status and new_name.
                The json format should be: {{"description": xxx, "provider": xxx, "status": xxx, "new_name": xxx}}. 
                Use the below article to search for details on the input.

                Article: {article}
                Input: {input}
            '''

    def __init__(self):
        proxy_client = get_ai_core_client()
        _ = ensure_llm(LLMRetriever.MODEL_NAME, LLMRetriever.MODEL_VERSION)
        llm = ChatOpenAI(proxy_model_name=LLMRetriever.MODEL_NAME,
                         temperature=0,
                         verbose=True,
                         proxy_client=proxy_client)
        parser = PydanticOutputParser(pydantic_object=Inventory)
        prompt_template = PromptTemplate.from_template(LLMRetriever.PROMPT,
                                                       partial_variables={"format_instructions": parser.get_format_instructions()})
        self.llm_chain = prompt_template | llm | parser
        self.retriever = WikipediaRetriever(load_all_available_meta=True, top_k_results=1, doc_content_chars_max=0)
        
    
    def search(self, data: InventoryItem, skip_if_same_revision: bool=True):
        docs = self.retriever.invoke(data.name)

        if not docs:
            raise NotFoundError(f"Could not find any information for {data.name}")

        # we are limiting to one result, so it's safe to access the first element
        doc = docs[0]
        
        # The defaul value for WikipediaRetriever doc_content_chars_max is 4000,
        # which fits the context window of 4K tokens of the gpt3.5 model.
        # A more robust approach would be to read the complete page and then use a
        # Retrieval Augmented Generation (RAG) pipeline, where we would embedd the 
        # document and use a similarity search to retrieve the most relevant chunks.

        if skip_if_same_revision and data.revision == doc.metadata['revision_id']:
            raise NoNewRevision("The data is already up to date.")

        try: 
            llm_details = self.llm_chain.invoke({
                "input": data.name,
                "article": doc.metadata['summary']
                # "article": doc.page_content
            })
        except OutputParserException as e:
            raise RuntimeError(f"Could not parse the output: {str(e)}")

        retrieved_data = InventoryItem(name=data.name,
                              description=llm_details.description,
                              provider=llm_details.provider,
                              lifeciycle_status=llm_details.status,
                              revision=doc.metadata["revision_id"],
                              source=doc.metadata["source"],
                              new_name=llm_details.new_name,
                              ref_text=doc.metadata["summary"])
        return retrieved_data