import streamlit as st
from llm_graph import run_langraph

import time
def get_llm_response(query):
    if query is None:
        answer = "How can I help you today?"
    else:
        answer = run_langraph(query)
    for word in answer.split(" "):
        yield word + " "
        time.sleep(0.05)


st.set_page_config(
    page_title="CKN Chat Bot",
    page_icon="🤖",
    layout="wide")

st.header("CKN Analytics Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display assistant response in chat message container
with st.chat_message("assistant"):
    # response = st.write_stream(get_llm_response(prompt))
    response = st.write_stream(get_llm_response(prompt))

# Add assistant response to chat history
st.session_state.messages.append({"role": "assistant", "content": response})