import streamlit as st
from conn import MySQLDatabase
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

st.set_page_config(page_title="AI assistant", page_icon=":speech_balloon:")

st.title("All Leases")

# Initialize database connection
db = MySQLDatabase()

# Fetch all leases as a DataFrame
df = db.fetch_all_leases()

if not df.empty:
    # Display the data as a table
    st.dataframe(df, use_container_width=True, hide_index=True)

    
else:
    st.error("No leases found or failed to fetch data.")
    
    


def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def generate_schema_summary(schema_raw_text):
    summarization_prompt = f"""
    Here is a database schema. Summarize it with table names, purposes, and a brief description of each column's purpose.

    Schema:
    {schema_raw_text}

    Summary:
    """
    
    summary_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # Wrap the prompt in a HumanMessage for compatibility
    summary = summary_llm([HumanMessage(content=summarization_prompt)]).content
    print(summary)
    return summary

def get_schema(db):
    raw_schema = db.get_table_info()
    print("This is the raw schema: ")
    print(raw_schema)
    return generate_schema_summary(raw_schema)

def get_sql_chain(db):  
    # Use the top-level get_schema function to retrieve the schema summary
    schema_summary = get_schema(db)
    
    template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
        
        <SCHEMA>{schema}</SCHEMA>
        
        Conversation History: {chat_history}
        
        Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
        Ensure that your response is a valid SQL query that can be executed by MySQL.
      
        ENSURE that there are no backticks in the query!
        ENSURE that there are no backslashes in the query!
    
        
        For example:
        Question: when is the next lease set to end?
        SQL Query: SELECT * FROM lease_tracking WHERE end_date = (SELECT MIN(end_date) FROM lease_tracking WHERE end_date > CURRENT_DATE) LIMIT 1;
        
        Question: Find all leases with a rental value greater than Ksh 100,000
        SQL Query: SELECT * FROM lease_tracking WHERE rental_amount > 100000;
        
        Your turn:
        
        Question: {question}
        SQL Query:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    #llm = ChatOpenAI(model="gpt-4-0125-preview")
    #llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def clean_sql_output(output):
        # Remove backticks from the query
        output = output.replace("`", "").strip()
        output = output.replace(r"\\", "").strip()
        return output
    
    return (
        RunnablePassthrough.assign(schema=lambda _: schema_summary)
        | prompt
        | llm
        | StrOutputParser()
        | (lambda output: clean_sql_output(output))  # Clean up the output
    )
    
    
def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    # Convert `chat_history` to simple text format for compatibility
    chat_history_text = "\n".join(
        f"Human: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}"
        for msg in chat_history
    )
  
    sql_chain = get_sql_chain(db)
  
    template = """
        You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
        Based on the table schema below, question, sql query, and sql response, write a natural language response. 
        Give all the monetary values in Ksh.
        
        
        <SCHEMA>{schema}</SCHEMA>
        ENSURE that there are no backticks in the query!
        ENSURE that there are no backslashes in the query!

        Conversation History: {chat_history}
        SQL Query: <SQL>{query}</SQL>
        User question: {question}
        SQL Response: {response}
    """
  
    prompt = ChatPromptTemplate.from_template(template)
  
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def clean_query(query: str) -> str:
        """
        Removes backslashes and any unwanted characters from the SQL query.
        """
        return query.replace("\\", "").strip()

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response=lambda vars: db.run(clean_query(vars["query"])),  # Clean the query
        )
        | prompt
        | llm
        | StrOutputParser()
    )
  
    return chain.invoke({
        "question": user_query,
        "chat_history": chat_history_text,  # Pass as joined text
    })

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm an AI assistant. Ask me anything about the leases."),
    ]

load_dotenv()



st.title("🤖 AI assistant")

db = init_database("root","pass","localhost","3306","apricot")

st.session_state.db = db
    
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    # Add the user query to chat history as HumanMessage
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    
    with st.chat_message("Human"):
        st.markdown(user_query)
        
    # Convert chat history to text format before passing to get_response
    with st.chat_message("AI"):
        response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
        st.markdown(response)
        
    # Add the AI response to chat history as AIMessage
    st.session_state.chat_history.append(AIMessage(content=response))
