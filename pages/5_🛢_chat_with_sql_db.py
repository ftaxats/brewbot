import utils
import sqlite3
import streamlit as st
from pathlib import Path
from sqlalchemy import create_engine

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities.sql_database import SQLDatabase

st.set_page_config(page_title="Brewbot", page_icon="🛢")
st.header('BrewThat')
st.write('Enable the Brewbot to interact with your company data through simple, conversations.')


class SqlChatbot:

    def __init__(self):
        self.openai_model = utils.configure_openai()
    
    def setup_db(_self, db_uri):
        if db_uri == 'USE_SAMPLE_DB':
            db_filepath = (Path(__file__).parent.parent / "assets/Chinook.db").absolute()
            db_uri = f"sqlite:////{db_filepath}"
            creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=rw", uri=True)
            db = SQLDatabase(create_engine("sqlite:///", creator=creator))
        else:
            db = SQLDatabase.from_uri(database_uri=db_uri)
        
        with st.sidebar.expander('Database tables', expanded=True):
            st.info('\n- '+'\n- '.join(db.get_usable_table_names()))
        return db
    
    def setup_sql_agent(_self, db):
        llm = ChatOpenAI(model_name=_self.openai_model, temperature=0, streaming=True)

        agent = create_sql_agent(
            llm=llm,
            db=db,
            top_k=10,
            verbose=True,
            agent_type="openai-tools",
            handle_parsing_errors=True,
            handle_sql_errors=True
        )
        return agent

    @utils.enable_chat_history
    def main(self):

        # User inputs
        radio_opt = ['Use sample db - Chinook.db','Connect to your SQL db']
        selected_opt = st.sidebar.radio(
            label='Choose suitable option',
            options=radio_opt
        )
        if radio_opt.index(selected_opt) == 1:
            with st.sidebar.popover(':orange[⚠️ Security note]', use_container_width=True):
                warning = "Building Q&A systems of SQL databases requires executing model-generated SQL queries. There are inherent risks in doing this. Make sure that your database connection permissions are always scoped as narrowly as possible for your chain/agent's needs.\n\nFor more on general security best practices - [read this](https://python.langchain.com/docs/security)."
                st.warning(warning)
            db_uri = st.sidebar.text_input(
                label='Database URI',
                placeholder='mysql://user:pass@hostname:port/db'
            )
        else:
            db_uri = 'USE_SAMPLE_DB'
        
        if not db_uri:
            st.error("Please enter database URI to continue!")
            st.stop()
        
        db = self.setup_db(db_uri)
        agent = self.setup_sql_agent(db)

        user_query = st.chat_input(placeholder="Ask me anything!")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container())
                result = agent.invoke(
                    {"input": user_query},
                    {"callbacks": [st_cb]}
                )
                response = result["output"]
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)

if __name__ == "__main__":
    obj = SqlChatbot()
    obj.main()
