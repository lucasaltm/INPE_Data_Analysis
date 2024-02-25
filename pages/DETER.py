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


# =======================   READING DATA    ========================== #
@st.cache_data(show_spinner=False)
def load_data():
    alerts = gpd.read_file('data/deter-amz-public-2024fev02/deter-amz-deter-public.shp', encoding='utf-8')
    #gdf_deter['VIEW_DATE'] = pd.to_datetime(gdf_deter['VIEW_DATE'])

    alerts.loc[alerts['CLASSNAME'] == 'DEGRDACAO', 'CLASSNAME'] = 'DEGRADACAO'
    alerts = alerts[~(alerts['CLASSNAME'] == 'CORTE_SELETIVO')]
    alerts['VIEW_DATE'] = pd.to_datetime(alerts['VIEW_DATE'])
    alerts['ANO'] = alerts['VIEW_DATE'].dt.year
    alerts['MES'] = alerts['VIEW_DATE'].dt.month
    alerts['MES/ANO'] = alerts['VIEW_DATE'].dt.strftime('%Y-%m')

    df_deter = pd.DataFrame(alerts)
    df_deter = df_deter.drop(columns=['FID', 'QUADRANT', 'PATH_ROW', 'SENSOR', 'SATELLITE', 'geometry'])
    # df_deter['NOME_ESTADO'] = df_deter['UF'].map(estados)
    # df_deter['STATE'] = df_deter['NOME_ESTADO'] + ' (' + df_deter['UF'] + ')   '

    legal_amazon = gpd.read_file('data/brazilian_legal_amazon/brazilian_legal_amazon.shp',encoding='utf-8')
    states = gpd.read_file('data/states_legal_amazon/states_legal_amazon.shp',encoding='utf-8')
    
    return alerts, df_deter, legal_amazon, states

with st.spinner('Loading Project, please wait...'):
    alerts, df_deter, legal_amazon, states = load_data()

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



# =======================       GRAPHS      ========================== #
# Pallete Generation Function
def palette_gen(n_colors=9, rgb1=[0, 100, 0], rgb2=[0, 200, 0]):
    green1 = np.array(rgb1) / 255.0
    green2 = np.array(rgb2) / 255.0
    
    grad = [green1 * (1 - i / (n_colors - 1)) + green2 * (i / (n_colors - 1)) for i in range(n_colors)]
    return [mcolors.to_hex(c) for c in grad]

gray = '#4b4d4b'

# def fig_to_html (fig):
#     buf = BytesIO()
#     fig.savefig(buf, format='png')
#     data = base64.b64encode(buf.getbuffer()).decode("ascii")
#     html_str = f'<img src="data:image/png;base64,{data}" style="display:block; margin:auto;"/>'

#     return html_str


# DETER GRAPH 1: TOP DETECTED CLASSES
def deter_graph1():
    df_class = df_deter.groupby('CLASSNAME')['AREAMUNKM'].sum().sort_values(ascending=False)
    df_class = pd.DataFrame(df_class)
    df_class['DESC'] = df_class.index.map(dict_classes)
    
    fig, ax = plt.subplots(figsize=(16,18))
    sns.set_theme(style="white")
    ax = sns.barplot(data=df_class, x=df_class.AREAMUNKM, y = df_class.DESC, palette=palette_gen())
    #ax.set_title(texts['title_deter_graph1'], fontsize=75, color=gray, fontweight='bold');
    #fig.suptitle(texts['title_deter_graph1'], fontsize=75, color=gray, fontweight='bold')
    ax.set_xlabel('');
    ax.set_ylabel('');
    ax.set_xticklabels([]);
    ax.yaxis.set_tick_params(labelsize=45, labelcolor = gray)
    sns.despine(left = True, bottom = True)
    
    for i, valor in enumerate(df_class.AREAMUNKM):
        p = (valor * 100) / df_class['AREAMUNKM'].sum()
        qtd = f'{valor:,.0f} km² ({p:,.2f} %)'.replace(',','.')  
        #offset = 1e3  # offset de 1.000
        ax.text(valor + 47500, i, qtd, color= gray, fontsize=45, fontweight='bold', ha='right', va='center')

    return fig, ax

def deter_graph2():
    class_count = pd.DataFrame(df_deter['CLASSNAME'].value_counts())
    class_count['DESC'] = class_count.index.map(dict_classes)
    class_count.reset_index()

    fig, ax = plt.subplots(figsize=(16,18))
    sns.set_theme(style="white")
    ax = sns.barplot(data=class_count, x=class_count['count'], y = class_count['DESC'], palette=palette_gen())
    #ax.set_title(texts['title_deter_graph2'], fontsize=65, color=gray, fontweight='bold');
    #fig.suptitle(texts['title_deter_graph2'], fontsize=65, color=gray, fontweight='bold')
    ax.set_xlabel('');
    ax.set_ylabel('');
    ax.set_xticklabels([]);
    ax.yaxis.set_tick_params(labelsize=45, labelcolor = gray)
    sns.despine(left = True, bottom = True)
    
    for i, valor in enumerate(class_count['count']):
        p = (valor * 100) / class_count['count'].sum()
        qtd = f'{valor:,.0f} ({p:,.2f} %)'.replace(',','.')  
        #offset = 1e3  # offset de 1.000
        ax.text(valor + 105000, i, qtd, color= gray, fontsize=45, fontweight='bold', ha='right', va='center')

    return fig, ax

def deter_graph3():
    gb_uf = df_deter.groupby('UF')['AREAMUNKM'].sum().sort_values(ascending=False)
    gb_uf = pd.DataFrame(gb_uf)

    gb_uf['NOME_ESTADO'] = gb_uf.index.map(estados)
    gb_uf['NOME E SIGLA'] = gb_uf['NOME_ESTADO'] + ' (' + gb_uf.index + ')   '
    
    
    #print(gb_uf)
    
    fig, ax = plt.subplots(figsize=(12,5))
    sns.set_theme(style="white")
    ax = sns.barplot(data=gb_uf, x=gb_uf.AREAMUNKM, y = gb_uf['NOME E SIGLA'], palette=palette_gen())
    #fig.suptitle(texts['title_deter_graph3'], fontsize=25, color=gray, fontweight='bold')
    #ax.set_title(texts['title_deter_graph3'], fontsize=50, color=gray, fontweight='bold');
    ax.set_xlabel('');
    ax.set_ylabel('');
    ax.set_xticklabels([]);
    ax.tick_params(axis='both', which='both', length=0)
    ax.yaxis.set_tick_params(labelsize=12, labelcolor = gray)
    sns.despine(left = True, bottom = True)

    for i, valor in enumerate(gb_uf.AREAMUNKM):
        p = (valor * 100) / gb_uf['AREAMUNKM'].sum()
        qtd = f'{valor:,.0f} km² ({p:,.2f} %)'.replace(',','.')  
        offset = 12e3  # offset de 1.000


        if valor>2000:
            offset = 13e3
        if valor>10000:
            offset = 138e2
        if valor>50000:
            offset = 145e2
        ax.text(valor + offset, i, qtd, color= gray, fontsize=12, fontweight='bold', ha='right', va='center')

    return fig, ax

def deter_graph4(qtd = 25,fs=(8,7)):
    sum_areamunkm = df_deter.groupby('MUNICIPALI')['AREAMUNKM'].sum().reset_index()
    info_uf = df_deter.drop_duplicates(subset='MUNICIPALI')[['UF', 'MUNICIPALI']]
    res = pd.merge(sum_areamunkm, info_uf, on='MUNICIPALI', how='left')
    
    top_cities = res.sort_values(by='AREAMUNKM', ascending=False).head(qtd)
    top_cities['MUN/UF'] = top_cities['MUNICIPALI'] + ' (' + top_cities['UF'].str.upper() + ') '

    fig, ax = plt.subplots(figsize=fs)
    sns.set_theme(style="white")
    ax = sns.barplot(data=top_cities, x=top_cities.AREAMUNKM, y = top_cities['MUN/UF'], palette=palette_gen(n_colors=top_cities.shape[0]))
    #ax.set_title(texts['title_deter_graph4'], fontsize=50, color=gray, fontweight='bold');
    #fig.suptitle(texts['title_deter_graph4'], fontsize=23, color=gray, fontweight='bold', horizontalalignment='center',x=0.375,y=0.935)
    ax.set_xlabel('');
    ax.set_ylabel('');
    ax.set_xticklabels([]);
    ax.yaxis.set_tick_params(labelsize=14, labelcolor = gray)
    sns.despine(left = True, bottom = True)
    
    for i, valor in enumerate(top_cities.AREAMUNKM):
        qtd = f'{valor:,.0f} km²'.replace(',','.')  
        #offset = 1e3  # offset de 1.000
        ax.text(valor + 1300, i, qtd, color= gray, fontsize=12, fontweight='bold', ha='right', va='center')
    
    return fig, ax


def deter_graph5():
    gb_ym = pd.DataFrame(df_deter.groupby('MES/ANO')['AREAMUNKM'].sum().sort_index()).reset_index()
    
    #Dropando mês incompleto
    most_recent_date = df_deter['VIEW_DATE'].max()
    last_day = pd.to_datetime(f'{most_recent_date.year}-{most_recent_date.month + 1}-01') - pd.Timedelta(days=1)
    
    if most_recent_date < last_day:
        # Se sim, excluir os dados desse mês
        gb_ym = gb_ym[gb_ym['MES/ANO'] < last_day.strftime('%Y-%m')]
    
    #maior valor de impacto mensal no ano
    gb_ym['ANO'] = pd.to_datetime(gb_ym['MES/ANO']).dt.year
    gb_ym['MES'] = pd.to_datetime(gb_ym['MES/ANO']).dt.month
    #max_year = pd.DataFrame(gb_ym.groupby('ANO').max()['AREAMUNKM']).rename(columns={'AREAMUNKM': 'MAX_DMG_YEAR'})
    max_year = gb_ym.groupby('ANO')['AREAMUNKM'].max().rename('MAX_DMG_YEAR').reset_index()
    gb_ym = pd.merge(gb_ym, max_year, on='ANO', how='left')
    
    #Meses que serão plotados
    dots = [True if row['AREAMUNKM'] == row['MAX_DMG_YEAR'] else False for index, row in gb_ym.iterrows()]


    
    fig, ax = plt.subplots(figsize=(27,6))
    gb_ym['MES/ANO'] = pd.to_datetime(gb_ym['MES/ANO'])
    
    ax.plot(gb_ym["MES/ANO"].values, gb_ym["AREAMUNKM"].values, lw=3, color = '#00c800', marker ="o", 
              markersize = 10, markerfacecolor = '#006400', markevery = dots)
    #ax.set_title(texts['title_deter_graph5'], fontsize = 45, color = gray, loc='center', pad=17)
    ax.set_frame_on(False)
    ax.xaxis.set_tick_params(labelsize=14, labelcolor = gray)
    ax.grid(which='both', linestyle='--', linewidth=0.5, color='gray', axis='both')
    
    meses = gb_ym['MES/ANO'].dt.month
    first_month = gb_ym["MES/ANO"].min()
    last_month = gb_ym["MES/ANO"].max()
    ticks = pd.date_range(start=first_month, end=last_month, freq='4MS')
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(texts['date_format2']))
    ax.set_xlim(first_month - DateOffset(months=1), last_month)
    
    for i in range(0, gb_ym.shape[0]):
    
        if gb_ym['AREAMUNKM'][i] == gb_ym['MAX_DMG_YEAR'][i]:
            ax.annotate(f"{gb_ym['AREAMUNKM'][i]:.2f} km²\n  ({gb_ym['MES/ANO'][i].strftime(texts['date_format2'])})", 
                        xy=(gb_ym["MES/ANO"][i], gb_ym['AREAMUNKM'][i]), 
                        xytext=(15, -20), textcoords='offset points',
                        color='#006400', weight="bold", fontsize=13,
                        arrowprops=dict(arrowstyle="->", color='#006400'))
    
    plt.xticks(rotation=0);
    
    return fig, ax

def deter_graph6():
    complete_years = df_deter.groupby('ANO')['MES'].nunique().reset_index()
    complete_years = complete_years[complete_years['MES'] == 12]['ANO']

    y1 = complete_years.min()
    y2 = complete_years.max()
    
    df_month = df_deter[df_deter['ANO'].isin(complete_years)]['AREAMUNKM'].groupby(df_deter['MES']).sum().sort_index()
    df_month = pd.DataFrame(df_month)

    fig, ax = plt.subplots(figsize=(17,5))
    
    norm = plt.Normalize(df_month.values.min()-50000, df_month.values.max()+20000);
    colors = plt.cm.Greens(norm(df_month));
    
    ax = sns.barplot(data=df_month, x=df_month.index, y=df_month['AREAMUNKM'], palette=colors)
    #ax.set_title(texts['title_deter_graph6'].format(y1,y2), fontsize = 23, color = gray, loc='center', pad=20)
    ax.set_xlabel('')
    ax.set_ylabel('')
    lbs = ast.literal_eval(texts['labels_deter_graph6'])
    plt.xticks(ticks=range(0, 12), labels=lbs);
    ax.set_frame_on(False)
    plt.gca().set_yticks([])
    
    for i, area in enumerate(df_month['AREAMUNKM']):
        qtd = f'{area:,.0f} km²'.replace(',', '.')
        offset = 750
        ax.text(i, area + offset, qtd, color= gray, fontsize=12, ha='center', va='center')

    return fig, ax, y1, y2

def deter_graph7():
    complete_years = df_deter.groupby('ANO')['MES'].nunique().reset_index()
    complete_years = complete_years[complete_years['MES'] == 12]['ANO']
    # df_month = df_deter[df_deter['ANO'].isin(complete_years)]['AREAMUNKM'].groupby(df_deter['MES']).sum().sort_index()
    # df_month = pd.DataFrame(df_month)
    complete_years_df = df_deter[df_deter['ANO'].isin(complete_years)]
    complete_years_df = pd.DataFrame(complete_years_df['AREAMUNKM'].groupby(df_deter['ANO']).sum().sort_index())
    complete_years_df = complete_years_df.reset_index(drop=False)
    # complete_years_df['VARIACAO_AREA'] = complete_years_df["AREAMUNKM"].diff().fillna(complete_years_df["AREAMUNKM"]).astype("float64")
    # complete_years_df["Medidas"] = ["absolute"] + ["relative"] * 6

    fig, ax = plt.subplots(figsize=(20,7))
    ax = sns.barplot(data=complete_years_df, x=complete_years_df['ANO'], y=complete_years_df['AREAMUNKM'],color='#009600')
    #ax.set_title(texts['title_deter_graph7'], fontsize = 23, color = gray, loc='center', pad=20)
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_frame_on(False)
    plt.gca().set_yticks([])
    
    for i, area in enumerate(complete_years_df['AREAMUNKM']):
        qtd = f'{area:,.0f} km²'.replace(',', '.')
        offset = -1500
        
        ax.text(i, area + offset, qtd, color= "#ffffff", fontsize=18, ha='center', va='center', fontweight='bold')
        
        if (i != complete_years_df.shape[0]-1):
            
            dif = complete_years_df['AREAMUNKM'].iloc[i+1] - complete_years_df['AREAMUNKM'].iloc[i]
            
            if dif < 0:
                fcolor = '#00c800'
                ecolor = '#00c800'
                offs = 0.74
                prefix = ''
            else:
                fcolor = '#ff0000'
                ecolor = '#ff0000'
                offs = 0.26
                prefix = '+'
            
            arrow = mpatches.FancyArrowPatch((i + 0.5, complete_years_df['AREAMUNKM'].iloc[i]), (i+0.5, complete_years_df['AREAMUNKM'].iloc[i+1]),
                                         mutation_scale=45, facecolor=fcolor,edgecolor=ecolor)
            ax.add_patch(arrow)
    
            pct = (dif*100) / complete_years_df['AREAMUNKM'].iloc[i]
            textarea = complete_years_df['AREAMUNKM'].iloc[i] +  (dif/2)
            qtd = f'{prefix}{dif:.0f}\n{prefix}{pct:.2f}%'
            ax.text(i + offs, textarea, qtd, color= fcolor, fontsize=15, ha='center', va='center')
    
    return fig, ax

def deter_graph8():
    fig, axs = plt.subplots(3, 3, figsize=(20,20), sharey=True)
    #fig.suptitle(texts['graph8_title'], fontsize = 40, color = gray, fontweight='bold')
    plt.subplots_adjust(wspace=0.05, hspace=0.3)  
    sns.set_theme(style="white")
    
    lst_states = list(estados.keys())
    all_classes = sorted(df_deter['CLASSNAME'].unique())
    
    k=0
    
    for i in range(3):
        for j in range(3):
            
            df_state = df_deter[df_deter['UF'] == lst_states[k]]
            df_state_summed = df_state.groupby('CLASSNAME')['AREAMUNKM'].sum().reset_index()
            df_state_complete = pd.DataFrame({'CLASSNAME': all_classes})
            df_state_complete = df_state_complete.merge(df_state_summed, on='CLASSNAME', how='left').fillna(0)
            df_state_complete['DESC'] = df_state_complete['CLASSNAME'].map(dict_classes)
    
            sns.barplot(data=df_state_complete, x='AREAMUNKM', y = 'DESC', palette=palette_gen(), ax=axs[i, j])
            axs[i, j].set_xlabel('');
            axs[i, j].set_ylabel('');
            axs[i, j].yaxis.set_tick_params(labelsize=15, labelcolor = gray)
            sns.despine(left = True, bottom = True)
            axs[i, j].grid(color='gray', linestyle='--', linewidth=0.5)
            axs[i, j].set_title(estados[lst_states[k]] + ' (' + lst_states[k] + ')', fontsize=25, color=gray, fontweight='bold')

            
            k+=1
    return fig, axs

def deter_graph9():
    sum_areamunkm = df_deter.groupby('UC')['AREAMUNKM'].sum().reset_index()
    info_uc = df_deter.drop_duplicates(subset='UC')[['UC', 'UF', 'MUNICIPALI']]
    res = pd.merge(sum_areamunkm, info_uc, on='UC', how='left')
    top_ucs = res.sort_values(by='AREAMUNKM', ascending=False).head(25)
    top_ucs['UC/LOC'] = top_ucs['UC'] + ' (' + top_ucs['MUNICIPALI'].str.upper() + '/' + top_ucs['UF'].str.upper() + ')'

    fig, ax = plt.subplots(figsize=(8,14))
    sns.set_theme(style="white")
    ax = sns.barplot(data=top_ucs, x=top_ucs.AREAMUNKM, y = top_ucs['UC/LOC'],
                     palette=palette_gen(n_colors=top_ucs.shape[0]))
    #ax.set_title(texts['graph9_title'], fontsize=20, color=gray, fontweight='bold');
    #fig.suptitle(texts['graph9_title'], fontsize=23, color=gray, fontweight='bold', horizontalalignment='center',x=0.28,y=0.92)
    ax.set_xlabel('');
    ax.set_ylabel('');
    ax.set_xticklabels([]);
    ax.yaxis.set_tick_params(labelsize=10, labelcolor = gray)
    sns.despine(left = True, bottom = True)

    for i, valor in enumerate(top_ucs.AREAMUNKM):
        qtd = f'{valor:,.0f} km²'.replace(',','.')  

        offset = 110

        if valor>100:
            offset = 125

        if valor>200:
            offset = 130
        
        if valor>1000:
            offset = 150
        
        
        ax.text(valor + offset, i, qtd, color= gray, fontsize=12, fontweight='bold', ha='right', va='center')

    return fig, ax

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
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(center_md(texts['title_deter_graph2']), unsafe_allow_html=True)
        #st.markdown(texts['title_deter_graph2'])
        fig, ax = deter_graph2()
        st.pyplot(fig)
        
    with col2:
        st.markdown(center_md(texts['title_deter_graph1']), unsafe_allow_html=True)
        #st.markdown(texts['title_deter_graph1'])
        fig, ax = deter_graph1()
        st.pyplot(fig)


    st.markdown(texts['graphs_12_desc'])

with states_statistics:
    st.markdown(center_md(texts['title_deter_graph3']), unsafe_allow_html=True)
    
    fig, ax = deter_graph3()
    st.pyplot(fig)
    st.markdown(texts['graph3_desc'])
    
    divider()

    st.markdown(center_md(texts['graph8_title']), unsafe_allow_html=True)
    fig, ax = deter_graph8()
    st.pyplot(fig)
    st.markdown(texts['graph8_desc'])

with cities_statistics:

    st.markdown(center_md(texts['title_deter_graph4']), unsafe_allow_html=True)
    
    fig, ax = deter_graph4()
    st.pyplot(fig)
    st.markdown(texts['graph4_desc'])
    
with ucs_statistics:

    st.markdown(center_md(texts['graph9_title']), unsafe_allow_html=True)
    
    fig, ax = deter_graph9()
    st.pyplot(fig)
    st.markdown(texts['graph9_desc'])

# Damage through years
with dmg_ty:
    st.markdown(center_md(texts['title_deter_graph5']), unsafe_allow_html=True)
    fig, ax = deter_graph5()
    st.pyplot(fig)
    st.markdown(texts['graph5_desc'])
    
    divider()

    fig, ax, y1,y2 = deter_graph6()
    st.markdown(center_md(texts['title_deter_graph6'].format(y1,y2)), unsafe_allow_html=True)
    st.pyplot(fig)
    st.markdown(texts['graph6_desc'])

    divider()

    st.markdown(center_md(texts['title_deter_graph7']), unsafe_allow_html=True)
    fig, ax = deter_graph7()
    st.pyplot(fig)
    st.markdown(texts['graph7_desc'],unsafe_allow_html=True)

# FOLIUM MAPS
def get_centroids(geo_df, mode=2, crs='EPSG:31982'):

    if mode==0:
        centroids = geo_df.copy()
        centroids["centroid"] = centroids.geometry.centroid
        centroids["latitude"] = centroids.centroid.y
        centroids["longitude"] = centroids.centroid.x
        return centroids

    if mode==1:
        geo_df_proj = geo_df.copy()
        geo_df_proj.to_crs(crs)
        
        geo_df_proj['centroid'] = geo_df_proj.geometry.centroid
        geo_df_proj['latitude'] = geo_df_proj.centroid.y
        geo_df_proj['longitude'] = geo_df_proj.centroid.x
        
        centroids = gpd.GeoDataFrame(geo_df_proj, geometry='centroid', crs=crs)
    
        centroids = centroids.to_crs(geo_df.crs)
        return centroids

    if mode==2:
        df = geo_df.copy()
        df['representative_point'] = df.geometry.representative_point()
        df['latitude'] = df['representative_point'].apply(lambda p: p.y)
        df['longitude'] = df['representative_point'].apply(lambda p: p.x)
        return df

def folium_map_init():
    map = folium.Map(location=[-7.25, -60], zoom_start=4)

    folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', 
        attr='&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name='Stamen Terrain'
    ).add_to(map)

    return map

def folium_add_markers(container, df_data, geo_df, get_centroid_mode, df_deter, key, popup_title_column, popup_total_area_text='Área Total Afetada:',total_area_column='AREAMUNKM'):

    all_classes = sorted(df_deter['CLASSNAME'].unique())
    df_centroids = get_centroids(geo_df,get_centroid_mode)
    
    for idx, row in df_data.iterrows():

        # Get Centroids for marker location
        coords = df_centroids.loc[df_centroids[key] == row[key]].iloc[0]

        # Variable of statistics
        info = ''
        
        # Get classes statistics from the deter dataframe
        if row['AREAMUNKM']>0:
            df_stats = df_deter[df_deter[key] == row[key]]
            df_stats_summed = df_stats.groupby('CLASSNAME')['AREAMUNKM'].sum().reset_index()
            df_stats_complete = pd.DataFrame({'CLASSNAME': all_classes})
            df_stats_complete = df_stats_complete.merge(df_stats_summed, on='CLASSNAME', how='left').fillna(0)
            df_stats_complete['DESC'] = df_stats_complete['CLASSNAME'].map(dict_classes)
            df_stats_complete = df_stats_complete.sort_values(by='AREAMUNKM', ascending=False)
    
            total = df_stats_complete['AREAMUNKM'].sum()
            
            # Calculates percentage of every class
            for ind, lin in df_stats_complete.iterrows():
                perc = (lin['AREAMUNKM'] * 100) / total
                info += f"{lin['DESC']}: {lin['AREAMUNKM']:.0f} km² ({perc:.2f}%)<br>"
        
        popup_text = f"""
        <div style='white-space: nowrap;'>
        <span style='font-size: 16px; font-weight: bold;'>{row[popup_title_column]}</span><br><br> {popup_total_area_text} {row[total_area_column]:.0f} km²<br><br> {info}
        </div>
        """

        # Add marker on Map or MarkerCluster (container)
        folium.Marker(
            location=[coords['latitude'], coords['longitude']],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='triangle-exclamation', prefix='fa')
        ).add_to(container)
    
    return container

@st.cache_data(show_spinner=False)
def states_map():
    
    ############# Data Preparation #############
    legal_amazon = gpd.read_file('data/brazilian_legal_amazon/brazilian_legal_amazon.shp',encoding='utf-8')
    states = gpd.read_file('data/states_legal_amazon/states_legal_amazon.shp',encoding='utf-8')
    
    df_deter = alerts.copy()
    gb_uf = df_deter.groupby('UF')['AREAMUNKM'].sum().sort_values(ascending=False)
    gb_uf = pd.DataFrame(gb_uf)
    
    gb_uf['NOME_ESTADO'] = gb_uf.index.map(estados)
    gb_uf['NOME_SIGLA'] = gb_uf['NOME_ESTADO'] + ' (' + gb_uf.index + ')' 
    gb_uf = gb_uf.reset_index()
    
    states = states.rename(columns={'sigla':'UF'})



    #############       Folium       #############
    
    map = folium_map_init()
    
    style_states = {'fillOpacity':0 ,'color' : '#117306', 'weight': 2}
    folium.GeoJson(states, name = 'States', style_function= lambda x: style_states).add_to(map)
    
    style_legal_amazon = {'fillOpacity':0 ,'color' : '#117306', 'weight': 3}
    folium.GeoJson(legal_amazon, name = 'Legal Amazon', style_function= lambda x: style_legal_amazon).add_to(map)
    
    folium.Choropleth(geo_data=states,
                      data=gb_uf,
                      columns=['UF', 'AREAMUNKM'],
                      key_on = 'feature.properties.UF',
                      fill_color = 'YlOrRd',
                      nan_fill_color = 'white',
                      bins=10,
                      highlight = True,
                      legend_name='Affected Area in km²',
                      name='Most Affected States').add_to(map)

    map = folium_add_markers(map, gb_uf, states, 1, df_deter, 'UF', 'NOME_SIGLA', 'Total Damaged Area:', 'AREAMUNKM')
    
    folium.LayerControl().add_to(map)

    return map._repr_html_()

@st.cache_data(show_spinner=False)
def cities_map(filter=[]):
    
    ############# Data Preparation #############
    ac = gpd.read_file('data/malhas_regionais_ibge/AC_Municipios_2022/AC_Municipios_2022.shp', encoding='utf-8')
    am = gpd.read_file('data/malhas_regionais_ibge/AM_Municipios_2022/AM_Municipios_2022.shp', encoding='utf-8')
    ap = gpd.read_file('data/malhas_regionais_ibge/AP_Municipios_2022/AP_Municipios_2022.shp', encoding='utf-8')
    ma = gpd.read_file('data/malhas_regionais_ibge/MA_Municipios_2022/MA_Municipios_2022.shp', encoding='utf-8')
    mt = gpd.read_file('data/malhas_regionais_ibge/MT_Municipios_2022/MT_Municipios_2022.shp', encoding='utf-8')
    pa = gpd.read_file('data/malhas_regionais_ibge/PA_Municipios_2022/PA_Municipios_2022.shp', encoding='utf-8')
    ro = gpd.read_file('data/malhas_regionais_ibge/RO_Municipios_2022/RO_Municipios_2022.shp', encoding='utf-8')
    rr = gpd.read_file('data/malhas_regionais_ibge/RR_Municipios_2022/RR_Municipios_2022.shp', encoding='utf-8')
    to = gpd.read_file('data/malhas_regionais_ibge/TO_Municipios_2022/TO_Municipios_2022.shp', encoding='utf-8')

    df_cities = pd.concat([ac, am, ap, ma, mt, pa, ro, rr, to])
    df_cities.rename(columns={'CD_MUN':'GEOCODIBGE'}, inplace=True)

    geocodibge = alerts.drop_duplicates(subset='MUNICIPALI').set_index('MUNICIPALI')['GEOCODIBGE']
    sum_areamunkm = alerts.groupby('MUNICIPALI')['AREAMUNKM'].sum().reset_index()
    sum_areamunkm['GEOCODIBGE'] = sum_areamunkm['MUNICIPALI'].map(geocodibge)

    merge = pd.merge(df_cities, sum_areamunkm, on='GEOCODIBGE', how='left')

    if len(filter)>0:
        merge = merge[merge['SIGLA_UF'].isin(filter)]
    
    # merge[merge['AREAMUNKM'].isna()]
    # 226 cidades não contém avisos. Esses valores ausentes serão preenchidos com 0.
    merge['AREAMUNKM'].fillna(0, inplace=True)

    #############       Folium       #############
    map = folium_map_init()

    style_cities = {'fillOpacity':0 ,'color' : '#117306', 'weight': 1}
    folium.GeoJson(merge, name = 'Cities', style_function= lambda x: style_cities).add_to(map)

    style_states = {'fillOpacity':0 ,'color' : '#117306', 'weight': 2}
    folium.GeoJson(states, name = 'States', style_function= lambda x: style_states).add_to(map)
    
    style_legal_amazon = {'fillOpacity':0 ,'color' : '#117306', 'weight': 3}
    folium.GeoJson(legal_amazon, name = 'Legal Amazon', style_function= lambda x: style_legal_amazon).add_to(map)
    
    folium.Choropleth(geo_data=merge.to_json(),
                  name='Choropleth',
                  data=merge,
                  columns=['GEOCODIBGE', 'AREAMUNKM'],
                  key_on = 'feature.properties.GEOCODIBGE',
                  fill_color = 'YlOrRd',
                  nan_fill_color = 'white',
                  highlight = True,
                  legend_name='Affected Area in km²').add_to(map)

    marker_cluster = MarkerCluster().add_to(map)
    marker_cluster = folium_add_markers(marker_cluster, merge, merge, 2, alerts, 'GEOCODIBGE', 'NM_MUN', 'Total Damaged Area:', 'AREAMUNKM')
    folium.LayerControl().add_to(map)

    return map._repr_html_()


def normalize_string(s):
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[^\w\s]', '', s)
    s = s.upper()
    return s

@st.cache_data(show_spinner=False)
def c_units_map():

    ############# Data Preparation #############
    c_units = gpd.read_file('data/conservation_units_legal_amazon/conservation_units_legal_amazon.shp',encoding='utf-8')
    c_units.rename(columns={'nome':'UC'},inplace=True)
    c_units['UC'] = c_units['UC'].apply(normalize_string)
    
    alerts_uc = alerts[alerts['UC'].notna()].copy()
    dic_correcao = {'FLORESTA NACIONAL DE ALTAMIRA': 'FLORESTA NACIONAL ALTAMIRA', 
                    'FLORESTA NACIONAL DE CAXIUANÂ': 'FLORESTA NACIONAL DE CAXIUANÃ', 
                    'FLORESTA NACIONAL DO AMANA': 'FLORESTA NACIONAL DO AMANÁ',
                    'FLORESTA NACIONAL DO BOM FUTURO': 'FLORESTA NACIONAL DE BOM FUTURO',
                    'FLORESTA NACIONAL DO ITACAIUNAS': 'FLORESTA NACIONAL DE ITACAIUNAS',
                    'FLORESTA NACIONAL DO JATUARANA': 'FLORESTA NACIONAL DE JATUARANA',
                    'FLORESTA NACIONAL DO PURUS': 'RESERVA EXTRATIVISTA DO MÉDIO PURÚS',
                    'FLORESTA NACIONAL DO TAPAJÓS': 'FLORESTA NACIONAL DE TAPAJÓS',
                    'FLORESTA NACIONAL DO TAPIRAPÉAQUIRI': 'FLORESTA NACIONAL DE TAPIRAPÉAQUIRI',
                    'FLORESTA NACIONAL MAPIÁ  INAUINI': 'FLORESTA NACIONAL DE MAPIÁINAUINÍ',
                    'PARQUE NACIONAL SERRA DA CUTIA': 'PARQUE NACIONAL DA SERRA DA CUTIA',
                    'RESERVA BIOLÓGICA NASCENTES DA SERRA DO CACHIMBO': 'RESERVA BIOLÓGICA NASCENTES SERRA DO CACHIMBO',
                    'RESERVA EXTRATIVISTA DO ALTO JURUÁ': 'RESERVA EXTRATIVISTA ALTO JURUÁ',
                    'RESERVA EXTRATIVISTA DO ALTO TARAUACÁ': 'RESERVA EXTRATIVISTA ALTO TARAUACÁ',
                    'RESERVA EXTRATIVISTA DO BAIXO JURUÁ': 'RESERVA EXTRATIVISTA BAIXO JURUÁ',
                    'RESERVA EXTRATIVISTA DO CIRIACO': 'RESERVA EXTRATIVISTA DO CIRIÁCO',
                    'RESERVA EXTRATIVISTA DO LAGO DO CUNIÃ': 'RESERVA EXTRATIVISTA LAGO DO CUNIÃ',
                    'RESERVA EXTRATIVISTA DO MÉDIO JURUÁ': 'RESERVA EXTRATIVISTA MÉDIO JURUÁ',
                    'RESERVA EXTRATIVISTA DO RIO CAJARI': 'RESERVA EXTRATIVISTA RIO CAJARI',
                    'RESERVA EXTRATIVISTA DO RIO DO CAUTÁRIO': 'RESERVA EXTRATIVISTA RIO CAUTÁRIO',
                    'RESERVA EXTRATIVISTA DO RIO OURO PRETO': 'RESERVA EXTRATIVISTA RIO OURO PRETO',
                    'RESERVA EXTRATIVISTA RIO UNINI': 'RESERVA EXTRATIVISTA DO RIO UNINI',
                    'RESERVA EXTRATIVISTA TAPAJÓSARAPIUNS': 'RESERVA EXTRATIVISTA TAPAJÓS ARAPIUNS',
                    'RESERVA EXTRATIVISTA TAPAJÓS-ARAPIUNS': 'RESERVA EXTRATIVISTA TAPAJÓS ARAPIUNS',
                    'RESERVA EXTRATIVISTA TERRA GRANDE  PRACUÚBA': 'RESERVA EXTRATIVISTA TERRA GRANDE PRACUUBA',
                    'RESERVA EXTRATIVISTA TERRA GRANDE - PRACUÚBA': 'RESERVA EXTRATIVISTA TERRA GRANDE PRACUUBA',
                    'ÁREA DE PROTEÇÃO AMBIENTAL DOS MEANDROS DO RIO ARAGUAIA': 'ÁREA DE PROTEÇÃO AMBIENTAL MEANDROS DO ARAGUAIA',
                    'ÁREA DE RELEVANTE INTERESSE ECOLÓGICO SERINGAL NOVA ESPERANÇA': 'ÁREA DE RELEVANTE INTERESSE ECOLÓGICA SERINGAL NOVA ESPERANÇA',
                    'ESTAÇÃO ECOLÓGICA JUAMI-JAPURÁ': 'ESTAÇÃO ECOLÓGICA JUAMIJAPURÁ',
                    'FLORESTA NACIONAL DE BALATA-TUFARI': 'FLORESTA NACIONAL DE BALATATUFARI',
                    'FLORESTA NACIONAL DE SARACÁ-TAQUERA': 'FLORESTA NACIONAL DE SARACÁTAQUERA',
                    'FLORESTA NACIONAL MAPIÁ - INAUINI': 'FLORESTA NACIONAL DE MAPIÁINAUINÍ',
                    'RESERVA EXTRATIVISTA AUATÍ-PARANÁ': 'RESERVA EXTRATIVISTA AUATÍPARANÁ',
                    'RESERVA EXTRATIVISTA DO CAZUMBÁ-IRACEMA': 'RESERVA EXTRATIVISTA DO CAZUMBÁIRACEMA',
                    'RESERVA EXTRATIVISTA GURUPÁ-MELGAÇO': 'RESERVA EXTRATIVISTA GURUPÁMELGAÇO',
                    'RESERVA EXTRATIVISTA IPAÚ-ANILZINHO': 'RESERVA EXTRATIVISTA IPAÚANILZINHO'}
    alerts_uc['UC'] = alerts_uc['UC'].replace(dic_correcao)
    gc_uc = alerts_uc.groupby('UC')['AREAMUNKM'].sum().reset_index()
    gc_uc['UC'] = gc_uc['UC'].replace(dic_correcao)
    
    # Not found conservation units in c_units dataframe
    # lst_dif=[]
    # for item in list(gc_uc['UC']):
    #     if item not in list(c_units['UC']):
    #         lst_dif.append(item)
    # lst_dif # ['ESTAÇÃO ECOLÓGICA DE CARACARAÍ', 'ESTAÇÃO ECOLÓGICA DE IQUÊ']
    
    # Inserindo unidades de conservação que faltam no geodataframe "c_units" nas coordenadas do primeiro alerta encontrado nos dados do DETER
    def uc_geodf(estacao):
        primeiro_alerta = alerts[alerts['UC'] == estacao]['geometry'].iloc[0]
        ponto_representativo = primeiro_alerta
        novo_registro = {
            'UC': estacao,
            'geometry': ponto_representativo
        }
        return gpd.GeoDataFrame([novo_registro], crs=c_units.crs)
    
    c_units = pd.concat([c_units, uc_geodf('ESTAÇÃO ECOLÓGICA DE CARACARAÍ')], ignore_index=True)
    c_units = pd.concat([c_units, uc_geodf('ESTAÇÃO ECOLÓGICA DE IQUÊ')], ignore_index=True)
    
    merge_ucs = pd.merge(c_units, gc_uc, on='UC', how='left').fillna(0)


    
    #############       Folium       #############

    map = folium_map_init()

    style_legal_amazon = {'fillOpacity':0 ,'color' : '#117306', 'weight': 3}
    folium.GeoJson(legal_amazon, name = 'Legal Amazon', style_function= lambda x: style_legal_amazon).add_to(map)

    style_states = {'fillOpacity':0 ,'color' : '#117306', 'weight': 2}
    folium.GeoJson(states, name = 'States', style_function= lambda x: style_states).add_to(map)

    style_ucs = {'fillOpacity':0 ,'color' : '#3d1601', 'weight': 1}
    folium.GeoJson(c_units, name = 'Conservation Units', style_function= lambda x: style_ucs).add_to(map)


    folium.Choropleth(geo_data=merge_ucs.to_json(),
                  name='Choropleth',
                  data=merge_ucs,
                  columns=['UC', 'AREAMUNKM'],
                  key_on = 'feature.properties.UC',
                  fill_color = 'YlOrRd',
                  nan_fill_color = 'white',
                  highlight = True,
                  legend_name='Affected Area in km²').add_to(map)
    
    marker_cluster = MarkerCluster().add_to(map)

    marker_cluster = folium_add_markers(marker_cluster,merge_ucs,merge_ucs, 2, alerts_uc, 'UC', 'UC', 'Total Damaged Area:', 'AREAMUNKM')

    folium.LayerControl().add_to(map)
    return map._repr_html_()

def center_map(html_map):
    html_final = """
    <div style='display:flex; justify-content:center; align-items:center; height:100%;'>
    <div style='width: 80%;'>""" + html_map + """</div>
    </div>
    """
    return html_final

with mapv:
    radio_title = "Escolha o tipo de visualização:"
    options = ["Visão Geral dos Estados", "Visão por Cidades", "Visão por Unidades de Conservação"]

    seL_map = st.radio(radio_title, options=options,
                           horizontal=True, index=0)
        

    
    if seL_map == options[0]:
        html_states = states_map()
        components.html(center_map(html_states), height=900)
    
    elif seL_map == options[1]:
        df_estados = pd.DataFrame(list(estados.items()), columns=['UF', 'Nome'])
        df_estados['Nome_UF'] = df_estados['Nome'] + ' (' + df_estados['UF'] + ')'
        
        ms_title = 'Escolha os estados que deseja visualizar no gráfico:'
        options = st.multiselect(ms_title,
                                 list(df_estados['Nome_UF']),
                                 [])


        if len(options) != 0:
            if list(df_estados['Nome_UF']) == options:
                filter = []
            else:
                filter = list(df_estados[df_estados['Nome_UF'].isin(options)].UF)
        else:
            filter = ['']

        with st.spinner('Loading visualization, please wait...'):
            html_cities = cities_map(filter)
            components.html(center_map(html_cities), height=900)
        
    elif seL_map == options[2]:
        html_c_units = c_units_map()
        components.html(center_map(html_c_units), height=900)