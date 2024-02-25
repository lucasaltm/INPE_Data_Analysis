# =======================       IMPORTS       ========================== #
#!pip install st-pages

import streamlit as st
from st_pages import Page, show_pages
import pandas as pd
import os
import zipfile
import gdown
# =======================    PAGE  CONFIG    ========================== #

folder_path = 'data'
if os.path.exists(folder_path):
    for item in os.listdir(folder_path):
        st.write(str(item))
else:
    st.write("pasta não existe")


st.set_page_config(
    page_title="INPE Amazon Data Analysis",
    page_icon="🌳",
    layout="centered",
    initial_sidebar_state="expanded"
)

def isDataDownloaded():
    folder = 'data'
    total = 6

    downloaded = False
    
    if os.path.exists(folder):
        num = len([nome for nome in os.listdir(folder)])
        if num == total:
            return True

    return downloaded

def download_data():
    d = isDataDownloaded()

    while not d:
        output = 'data.zip'
        data_link = 'https://drive.google.com/uc?id=1TN-Bi66ulQNoiIvLs963jqmi5E8NUTuD&export=download'
        
        gdown.download(data_link, output, quiet=False)
        
        with zipfile.ZipFile('data.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
        d = isDataDownloaded()
with st.spinner('Downloading data, please wait...'):
    download_data()

show_pages(
    [
        Page("Introduction.py", "Introduction", "📖"),
        Page("pages/DETER.py", "DETER", "⚠️"),
        Page("pages/PRODES.py", "PRODES", "🌳"),
        Page("pages/queimadas.py", "QUEIMADAS\n", "🔥"),
    ]
)
# st.markdown(
#     """
# <style>
#     [data-testid="collapsedControl"] {
#         display: none
#     }
# </style>
# """,
#     unsafe_allow_html=True,
# )

# =======================       TEXTS       ========================== #
df_texts = pd.read_csv('texts/texts_introduction.csv', sep='§', engine='python')
english = {list(df_texts['Key'])[i]: list(df_texts['English'])[i] for i in range(len(list(df_texts['Key'])))}
portuguese = {list(df_texts['Key'])[i]: list(df_texts['Portuguese'])[i] for i in range(len(list(df_texts['Key'])))}

def get_texts(lang):
    if lang == "English":
        return english
    else:
        return portuguese

# ======================= lANGUAGE SETTINGS  ========================== #
languages = {"English": "en", "Portuguese": "pt"}

dict_params = st.query_params.to_dict()

if "lang" not in dict_params.keys():
    st.query_params["lang"] = "en"
    st.rerun()


def set_language() -> None:
    if "selected_language" in st.session_state:
        st.query_params["lang"] = languages.get(st.session_state["selected_language"])

# =======================     SIDE BAR      ========================== #

col1, col2, col3, col4 = st.columns(4)


with st.sidebar:
    sel_lang = st.radio(
        "Language", options=languages,
        horizontal=True, 
        on_change=set_language,
        key="selected_language")
    
    texts = get_texts(sel_lang)

# =======================      HEADER       ========================== #
st.divider()
st.markdown("<h3 style='text-align: center; color: red;'>" + "⚠️  " + texts['construction'] + "  ⚠️" + "</h3>", unsafe_allow_html=True)
st.divider()

st.image('fire3.png')
st.markdown("<h2 style='text-align: center;'>" + texts['title'] + "</h3>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center;'>" + texts['sub_title'] + "</h3></br>", unsafe_allow_html=True)



st.markdown(texts['introduction'])


