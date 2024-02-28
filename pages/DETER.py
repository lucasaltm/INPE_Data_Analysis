# =======================       IMPORTS       ========================== #

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import plotly.express as px
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime
from pandas.tseries.offsets import DateOffset
import time
import matplotlib.patches as mpatches
import datetime
import re
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components
import base64
from io import BytesIO
import ast
import zipfile
import gdown
import os

# =======================    PAGE  CONFIG    ========================== #
icon = "⚠️"

st.set_page_config(
    page_title="DETER",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# =======================       TEXTS       ========================== #

df_texts = pd.read_csv('texts/texts_deter.csv', sep='§', engine='python')
english = {list(df_texts['Key'])[i]: list(df_texts['English'])[i] for i in range(len(list(df_texts['Key'])))}
portuguese = {list(df_texts['Key'])[i]: list(df_texts['Portuguese'])[i] for i in range(len(list(df_texts['Key'])))}

classes_deter_en = {'CICATRIZ_DE_QUEIMADA': 'Forest Fire Scar',
          'DESMATAMENTO_CR': 'Deforestation with Exposed Soil',
          'DESMATAMENTO_VEG': 'Deforestation with Vegetation',
          'MINERACAO': 'Mining',
          'DEGRADACAO': 'Degradation',
          'CS_DESORDENADO': 'Selective Logging Type 1 (Disordered)',
          'CS_GEOMETRICO': 'Selective Logging Type 2 (Geometric)',
}

classes_deter_pt = {'CICATRIZ_DE_QUEIMADA': 'Cicatriz de incêndio florestal',
          'DESMATAMENTO_CR': 'Desmatamento com solo exposto',
          'DESMATAMENTO_VEG': 'Desmatamento com Vegetação',
          'MINERACAO': 'Mineração',
          'DEGRADACAO': 'Degradação',
          'CS_DESORDENADO': 'Corte Seletivo Tipo 1 (Desordenado)',
          'CS_GEOMETRICO': 'Corte Seletivo Tipo 2 (Geométrico)',
}

estados = {
    "MT": "Mato Grosso",
    "PA": "Pará",
    "AM": "Amazonas",
    "RO": "Rondônia",
    "MA": "Maranhão",
    "RR": "Roraima",
    "AC": "Acre",
    "TO": "Tocantins",
    "AP": "Amapá"
}

def get_texts(lang):
    if lang == "English":
        return classes_deter_en, english
    else:
        return classes_deter_pt, portuguese

# ======================= lANGUAGE SETTINGS  ========================== #
languages = {"English": "en", "Portuguese": "pt"}

dict_params = st.query_params.to_dict()

if "lang" not in dict_params.keys():
    st.query_params["lang"] = "en"
    st.experimental_rerun()


def set_language() -> None:
    if "selected_language" in st.session_state:
        st.query_params["lang"] = languages.get(st.session_state["selected_language"])

# =======================     SIDE BAR      ========================== #
print('sidebar')
with st.sidebar:
    sel_lang = st.radio(
        "Language", options=languages,
        horizontal=True, 
        on_change=set_language,
        key="selected_language",)
    
    dict_classes, texts = get_texts(sel_lang)

# =======================      HEADER       ========================== #
#LOGO DETER
_, center, _ = st.columns(3)
with center:
    st.image("http://www.obt.inpe.br/OBT/assuntos/programas/amazonia/deter/imagens-deter/deterblogo.jpg")

def center_md(text):
    return "<h3 style='text-align: center;'>" + text + "</h3>"
    
st.markdown(center_md(texts['page_title']), unsafe_allow_html=True)

# =======================        BODY       ========================== #

def divider():
    st.markdown('</br>',unsafe_allow_html=True)
    st.divider()
    st.markdown('</br>',unsafe_allow_html=True)

about, alert_classes, states_statistics, cities_statistics, ucs_statistics, dmg_ty, mapv = st.tabs([texts['about'],
                                                                                                    texts['alert_classes'],
                                                                                                    texts['states_statistics'],
                                                                                                    texts['cities_statistics'],
                                                                                                    texts['ucs_statistics'],
                                                                                                    texts['dmg_ty'], 
                                                                                                    texts['map']])


# About DETER
with about:
    st.write(texts['deter_expander_desc_1'])
    st.write(texts['deter_expander_desc_2'])

# General Vision
with alert_classes:
    divider()
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     st.markdown(center_md(texts['title_deter_graph2']), unsafe_allow_html=True)
    #     #st.markdown(texts['title_deter_graph2'])
    #     fig, ax = deter_graph2()
    #     st.pyplot(fig)
        
    # with col2:
    #     st.markdown(center_md(texts['title_deter_graph1']), unsafe_allow_html=True)
    #     #st.markdown(texts['title_deter_graph1'])
    #     fig, ax = deter_graph1()
    #     st.pyplot(fig)


    # st.markdown(texts['graphs_12_desc'])

with states_statistics:
    # st.markdown(center_md(texts['title_deter_graph3']), unsafe_allow_html=True)
    
    # fig, ax = deter_graph3()
    # st.pyplot(fig)
    # st.markdown(texts['graph3_desc'])
    
    divider()

    # st.markdown(center_md(texts['graph8_title']), unsafe_allow_html=True)
    # fig, ax = deter_graph8()
    # st.pyplot(fig)
    # st.markdown(texts['graph8_desc'])

with cities_statistics:

    # st.markdown(center_md(texts['title_deter_graph4']), unsafe_allow_html=True)
    
    # fig, ax = deter_graph4()
    # st.pyplot(fig)
    # st.markdown(texts['graph4_desc'])
    divider()
    
with ucs_statistics:

    # st.markdown(center_md(texts['graph9_title']), unsafe_allow_html=True)
    
    # fig, ax = deter_graph9()
    # st.pyplot(fig)
    # st.markdown(texts['graph9_desc'])

    divider()

# Damage through years
with dmg_ty:
    # st.markdown(center_md(texts['title_deter_graph5']), unsafe_allow_html=True)
    # fig, ax = deter_graph5()
    # st.pyplot(fig)
    # st.markdown(texts['graph5_desc'])
    
    # divider()

    # fig, ax, y1,y2 = deter_graph6()
    # st.markdown(center_md(texts['title_deter_graph6'].format(y1,y2)), unsafe_allow_html=True)
    # st.pyplot(fig)
    # st.markdown(texts['graph6_desc'])

    divider()

    # st.markdown(center_md(texts['title_deter_graph7']), unsafe_allow_html=True)
    # fig, ax = deter_graph7()
    # st.pyplot(fig)
    # st.markdown(texts['graph7_desc'],unsafe_allow_html=True)

def center_map(html_map):
    html_final = """
    <div style='display:flex; justify-content:center; align-items:center; height:100%;'>
    <div style='width: 80%;'>""" + html_map + """</div>
    </div>
    """
    return html_final


# ---------------- Download maps -------------------- #
def isMapsDownloaded():
    folder = 'Visualizations/DETER/Maps'
    os.makedirs(folder, exist_ok=True)
    total = 25

    downloaded = False
    
    if os.path.exists(folder):
        num = len([nome for nome in os.listdir(folder)])
        if num >= total:
            return True

    return downloaded

def download_maps():
    d = isMapsDownloaded()

    while not d:
        output = 'Visualizations/DETER/Maps/maps.zip'
        data_link = 'https://drive.google.com/uc?id=1FgrolhAqFCTiXgJUPh6qPXcje_vslaZM&export=download'

        gdown.download(data_link, output, quiet=False)
        
        with zipfile.ZipFile('Visualizations/DETER/Maps/maps.zip', 'r') as zip_ref:
            zip_ref.extractall('Visualizations/DETER/Maps')
        d = isMapsDownloaded()

download_maps()

def read_map(map_name):
    html_file_path = f'Visualizations/DETER/Maps/{map_name}.html'
    
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    return html_content


with mapv:


    radio_title = "Escolha o tipo de visualização:"
    options = ["Visão Geral dos Estados", "Visão por Cidades", "Visão por Unidades de Conservação"]

    seL_map = st.radio(radio_title, options=options,
                           horizontal=True, index=0)

    
    
    if seL_map == options[0]:
        map_name = 'States_' + st.query_params["lang"].upper()
        with st.spinner(text="Loading..."):
            components.html(read_map(map_name), height=900)
            
    elif seL_map == options[1]:
        df_estados = pd.DataFrame(list(estados.items()), columns=['UF', 'Nome'])
        df_estados['Nome_UF'] = df_estados['Nome'] + ' (' + df_estados['UF'] + ')'
        

        lst_states = list(df_estados['Nome_UF'])
        lst_states.append('All Cities')
        
        ms_title = 'Escolha o estado que deseja visualizar no gráfico:'
        option = st.selectbox(
            ms_title,
            tuple(lst_states))

        
        if option != 'All Cities':
            uf_sel = df_estados[df_estados['Nome_UF'] == (option)].UF
            uf_sel = uf_sel.values[0]
    
            map_name = 'Cities_' + st.query_params["lang"].upper() + '_' + uf_sel.upper()
            
            with st.spinner('Loading visualization, please wait...'):
                components.html(read_map(map_name), height=900)
        else:
            map_name = 'All_Cities_' + st.query_params["lang"].upper()
            
            with st.spinner('Loading visualization, please wait...'):
                components.html(read_map(map_name), height=900)
        
    elif seL_map == options[2]:
        map_name = 'C_Units_' + st.query_params["lang"].upper()
        with st.spinner(text="Loading..."):
            components.html(read_map(map_name), height=900)