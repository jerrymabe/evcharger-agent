import streamlit as st
import random
import time
from main import main
from sessions import Session
from stats import main as stats
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
from st_copy import copy_button
import json

def positive_feedback_click():
    st.toast('Thanks for the thumbs up!', icon='🎉')
    session.update_feedback(1)

def negative_feedback_click():
    st.toast("Got it, we'll try to improve!", icon='🤔')
    session.update_feedback(0)

@st.cache_data
def address_generator(lat, lon):
    geolocator = Nominatim(user_agent="my-hosted-app")
    location = geolocator.reverse((lat, lon), language="en")
    address = location.address
    return address

@st.cache_data
def response_generator(prompt):
    history = st.session_state.messages
    coordinates = [lat, lon]
    relevancy, response = main(prompt, history, coordinates, selected_user, user_input, id)
    st.session_state.relevancy = relevancy
    return response

@st.cache_data
def stats_generator(table_name):
    response = stats(table_name)
    return response

def response_streamer(prompt):
    response = response_generator(prompt)
    for sentence in response.split("\n"):
        for word in sentence.split():
            yield word + " "
            time.sleep(0.05)
        yield "\n"

st.set_page_config(page_title="EVC Agent", page_icon="")

# Inject custom CSS to reduce top padding
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem; /* Adjust this value as needed */
    }
    ul[data-testid="stSidebarNavItems"] {
        padding-top: 3rem; /* Adjust this value as needed */
    }
    div.stButton > button {
        border-radius: 20px;     /* pill shape */
        padding: 6px 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar stuff
st.sidebar.title("Settings")
checked = []
cb_list = {}
session = Session()

with st.sidebar:
    selected_user = st.selectbox(
        "You are a:",
        ("Customer", "Maintenance Executive")
    )
    user_input = st.text_input("Enter your name:")

    st.header("Past Conversations")
    ph = st.empty()
    with ph:
        st.write("<i>Enter your name to check for any past conversations!</i>", unsafe_allow_html=True)

    if user_input:
        ph.empty()
        session_list = session.get_sessions(user_input)

        if(len(session_list) < 1):
            ph.write("<i>You do not have any past conversations!</i>", unsafe_allow_html=True)

        for i in session_list:
            if i[0] not in st.session_state:
                st.session_state[i[0]] = False

        def checkbox_callback(selected_opt):
            for i in session_list:
                if i[0] != selected_opt:
                    st.session_state[i[0]] = False
        
        for i in session_list:
            cb_list[i[0]] = st.checkbox(i[1], key=i[0], on_change=checkbox_callback, args=(i[0],))

    st.header("Statistics")
    if st.sidebar.button("Charger Details"):
        try:
            response = stats_generator('dp_ast')
            st.write(response)
        except Exception as e:
            print(f"An error occurred: {e}")
            st.error("Error with agent.")

    if st.sidebar.button("Charger Status"):
        try:
            response = stats_generator('evc_dvc_sts')
            st.write(response)
        except Exception as e:
            print(f"An error occurred: {e}")
            st.error("Error with agent.")

    if selected_user != "Customer":
        if st.sidebar.button("Charger Notifications"):
            try:
                response = stats_generator('evc_notifications')
                st.write(response)
            except Exception as e:
                print(f"An error occurred: {e}")
                st.error("Error with agent.")
    
        if st.sidebar.button("Charger Maintenance"):
            try:
                response = stats_generator('evc_maintenance')
                st.write(response)
            except Exception as e:
                print(f"An error occurred: {e}")
                st.error("Error with agent.")
    
        if st.sidebar.button("Charger Faults"):
            try:
                response = stats_generator('evc_flt')
                st.write(response)
            except Exception as e:
                print(f"An error occurred: {e}")
                st.error("Error with agent.")

    st.header("FAQ")
    if selected_user == "Customer":
        text = """
            - Which is the nearest EV charger?
            - What is the average wait time here?
            - Is it operational?
            - Is it occupied right now?
            - Is it fast-charging?
            - Any charger with lower wait time?
            - List of nearest 4 chargers
            - Is it cost-effective?
        """
        st.markdown(text)
    else:
        text = """
            - Which is the nearest EV charger?
            - When is the next maintenance here?
            - Is there any fault with it?
        """
        st.markdown(text)
    copy_button(
        f"{text}",
        copied_label="Copied!",
        icon="st",
    )

# Start of main body
st.title("ChargeGPT")
location = None
id = None

if "relevancy" not in st.session_state:
    st.session_state.relevancy = ""

with st.chat_message("assistant"):
    st.write("Hello there 👋, I am your personal assistant ChargeGPT. I can help you gain any information on Electric \
    Vehicle Chargers! \n To proceed, **please allow access to your location by clicking below!**")
    try:
        location = streamlit_geolocation()
    except:
        with st.chat_message("assistant"):
            st.error("Oops sorry! We are unable to retrieve your location at this moment.")
    
if location and location.get("latitude") is not None:
    lat = location.get("latitude")
    lon = location.get("longitude")

    address = address_generator(lat, lon)
    with st.chat_message("assistant"):
        st.success(f"Thank you! Your location has been identified as **{address}**. How may I be of assistance?")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "opt" not in st.session_state:
        st.session_state.opt = 0

    checked = [opt for opt, val in cb_list.items() if val]
    if checked:
        st.session_state.opt = 1
        id = checked[0]
        session_history = session.get_history(id)
        st.session_state.messages = []

        for i in session_history:
            print(session_history)
            st.session_state.messages.append({"role": "user", "content": i[0]})
            st.session_state.messages.append({"role": "assistant", "content": i[1]})
            
            with st.chat_message("user"):
                st.markdown(i[0])
        
            with st.chat_message("assistant"):
                st.markdown(i[1])
    else:
        id = None

        # If unchecked after checking
        if st.session_state.opt == 1:
            st.session_state.opt = 0
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    if prompt:= st.chat_input("How can I help you today?", key="chat_input"):
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
    
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = st.write_stream(response_streamer(prompt))

        if st.session_state.relevancy and st.session_state.relevancy == "1.0":
            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(10,gap="small")
            st.write("Was this helpful?")
            with col1:
                b1 = st.button("👍", on_click=positive_feedback_click)
            with col2:
                b2 = st.button("👎", on_click=negative_feedback_click)

        # Add  response to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    prompt = st.chat_input("How can I help you today?", key="chat_input", disabled=True)