from langchain.prompts import ChatPromptTemplate
from langchain.utilities import SQLDatabase
from langserve import add_routes
from fastapi import FastAPI

app = FastAPI(
   title="LangChain Server",
   version="1.0",
   description="A simple api server using Langchain's Runnable interfaces",
)

template = """Based on the table schema below, write a SQL query that would answer the user's question: {schema}

Question: {question}
SQL Query:"""
prompt = ChatPromptTemplate.from_template(template)

db = SQLDatabase.from_uri(f"mysql+pymysql://{user}:{password}@{ip}/{db}")

def get_schema(_):
   return db.get_table_info()

def run_query(query):
   return db.run(query)

from langchain.chat_models import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

model = ChatOpenAI()

sql_response = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | model.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)

template="""Based on the table schema below, question, sql query, and sql response, write a natural language {schema2}

Question: {question}
SQL Query: {query}
SQL Respinse: {response}"""
prompt_response = ChatPromptTemplate.from_template(template)


full_chain = (
   RunnablePassthrough.assign(query=sql_response)
   | RunnablePassthrough.assign(schema2=get_schema, response=lambda x: db.run(x["query"]),
   )
   | prompt_response
   | model
)

add_routes(
   app,
   full_chain,
   path="/answer",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
