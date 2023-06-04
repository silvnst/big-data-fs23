#### Overall setup 
#########################################################

import streamlit as st  # import streamlit library
import pandas as pd # import pandas library
import seaborn as sns   # import seaborn library
from datetime import date, datetime, time # import datetime library
import pickle # import pickle library
import xgboost as xgb # import xgboost library
import numpy as np # import numpy library
from helper.connect import create_weather # import function from connect.py
from helper.get_connection import get_connection # import function from get_connection.py
import pytz # import pytz library
import isodate # import isodate library
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score # import metrics from sklearn
from sklearn.model_selection import train_test_split # import train_test_split from sklearn
import helper.config as config # import config.py
from helper.functions import get_twitter_data, process_twitter_data, add_twitter_info # import functions.py
import snscrape.modules.twitter as sntwitter
import os # import os library


# Set page config
st.set_page_config(
    page_title= "Zugverspätung.ch",
    page_icon = "🚄",
    layout="wide"
    )

# Change directory to App
cwd = os.getcwd()
if not cwd.endswith('App'):
    os.chdir(os.getcwd() + '/App')

# set system timezone to swiss timezone
os.environ['TZ'] = 'Europe/Zurich'

# Load model
st.cache_data()
def load_model(station):
    model = pickle.load(open(f'./Modell/Orte/{station}_XGBRegressor.pkl', "rb"))
    # model = pickle.load(open("./Modell/model.pkl", "rb"))
    # model = pickle.load(open("./Modell/model_twitter.pkl", "rb"))
    return model

# Load data
st.cache_data()
def load_data():
    # df = pd.read_csv('./Daten/data_expanded/data_with_features.csv')
    # df = pd.read_csv('./Daten/data_expanded/data_with_features_twitter.csv')
    df1 = pd.read_csv('./Daten/data_new/detail1.csv')
    df2 = pd.read_csv('./Daten/data_new/detail2.csv')
    df = pd.concat([df1, df2], axis=0)
    df.drop(columns=['BETRIEBSTAG'], inplace=True)
    # Assuming your dataframe is called 'df' and the dummy columns start with 'departure_'
    df['haltestelle_ab'] = df.filter(like='haltestelle_ab_').idxmax(axis=1)
    df['haltestelle_ab'] = df['haltestelle_ab'].str.replace('haltestelle_ab_', '')
    df = df.drop(df.filter(like='haltestelle_ab_').columns, axis=1)
    df_cols = df.columns
    feiertage_data = pd.read_excel('./Daten/Feiertage_Haltestellen_roh.xlsx', sheet_name='data')
    haltestellen_data = pd.read_excel('./Daten/koordinaten.xlsx')
    return df, df_cols, feiertage_data, haltestellen_data

# Get twitter data
st.cache_data()
def get_twitter():
    today = date.today()
    query = 'from:railinfo_sbb since:' + today.strftime('%Y-%m-%d') + ' until:' + today.strftime('%Y-%m-%d') # Define twitter query
    tweets_raw = get_twitter_data(query=query, max_tweets=15, haltestellen=[x.lower() for x in config.HALTESTELLEN])
    if len(tweets_raw) > 0:
        tweets = process_twitter_data(tweets_raw, haltestellen=[x.lower() for x in config.HALTESTELLEN], linien=[x.lower() for x in config.LINIEN])
        return tweets
    return None    

#### Define general functions
#########################################################
def header():
    # add logo
    st.image('./img/logo_w.png', width=200)
    # set header
    header_html = "<div style='background-color: #eb0000; padding: 10px;'>"
    header_html += "<h1 style='color: #ffffff;'>SBB - Verspätungsvorhersage</h1></div>"
    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown("🚄 NEU – Berechne die vorhergesagte Verspätung deines Zuges!")
    # hide menu
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
            content:'Created by: Deniz, Felix, Jeff, Loris & Silvan'; 
            visibility: visible;
            display: block;
            color: #000000;
            }
            </style>
            """ 
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def user_input(df):
    # Define layout
    row1_col1, row1_col2= st.columns([1,1])
    
    # Define user inputs
    abfahrt = row1_col1.selectbox('Abfahrt', config.HALTESTELLEN, index=0)
    ankunft = row1_col1.selectbox('Ankunft', config.HALTESTELLEN, index=1)
    datum = row1_col2.date_input("Bitte wähle das Datum deiner Zugreise", value=date.today())
    selected_departure_time = row1_col2.time_input("Bitte wähle die Abfahrtszeit deines Zuges", value=datetime.now(pytz.timezone(os.environ['TZ'])).time())
    return abfahrt, ankunft, datum, selected_departure_time

def format_data(feiertage_data, haltestellen_data, abfahrt, ankunft, datum, selected_departure_time):
    weekday = datum.weekday()
    week = datum.isocalendar().week
    input_time = str(selected_departure_time).split(':')
    hour = int(input_time[0])
    minute = int(input_time[1])
    datetime_value = datetime.combine(datum, selected_departure_time)
    datetime_connection = datetime_value.strftime('%Y-%m-%dT%H:%M:%S')
    haltestelle_ab_info = int(haltestellen_data.loc[haltestellen_data['Bahnhof'] == abfahrt, 'info'].values[0])
    haltestelle_an_info = int(haltestellen_data.loc[haltestellen_data['Bahnhof'] == ankunft, 'info'].values[0])
    feiertage_data['datum'] = pd.to_datetime(feiertage_data['datum'], format='%d.%m.%Y').dt.date
    return weekday, week, hour, minute, datetime_value, datetime_connection, haltestelle_ab_info, haltestelle_an_info, feiertage_data

def get_feiertag(feiertage_data, datum):
    # Check if date is a holiday
    if datum in feiertage_data['datum'].values:
        feiertag = 1
    else:
        feiertag = 0
    return feiertag

def create_df(ankunft, week, weekday, hour, minute, feiertag, Temperatur, Niederschlag, Luftfeuchtigkeit, Wind, line_text, df_cols):
    # Get column names
    linien_cols = [col for col in df_cols if col.startswith('LINIEN_TEXT')]
    haltestellen_an_cols = [col for col in df_cols if col.startswith('haltestelle_an')]
    einschr_cols = [col for col in df_cols if col.startswith('Einschr_type')]
    dist_overlap = [col for col in df_cols if col.startswith('disturbance_overlap')]
    # Define column names and set values to 0
    column_names = ['weekday', 'ab_hour', 'ab_minute'] + dist_overlap + ['feiertag', 'Temperatur', 'Niederschlag',
            'Luftfeuchtigkeit', 'Wind', 'week'] + haltestellen_an_cols + linien_cols + einschr_cols
    column_values = {col: 0 for col in column_names}
    # Create dataframe
    df_models = pd.DataFrame(column_values, index=[0])
    # Fill dataframe
    df_models['weekday'] = weekday
    df_models['week'] = week
    df_models['ab_hour'] = hour
    df_models['ab_minute'] = minute
    df_models['feiertag'] = feiertag
    df_models['Temperatur'] = Temperatur
    df_models['Niederschlag'] = Niederschlag
    df_models['Luftfeuchtigkeit'] = Luftfeuchtigkeit
    df_models['Wind'] = Wind
    if dist_overlap != []:
        df_models['disturbance_overlap'] = False

    # Get col with ankunft in name and set value to 1
    for i in haltestellen_an_cols:
        if i.split('_')[2] == ankunft:
            df_models[i] = 1

    # select add linien info       
    for i in linien_cols:
        if i.split('_')[2] == line_text:
            df_models[i] = 1

    return df_models


#### Define main app function
#########################################################
def connection_app():

    # Load data
    df, df_cols, feiertage_data, haltestellen_data = load_data()
    # Define general header of section
    header()
    # Define header of section
    st.header("Verbindung suchen")

    # get user input
    abfahrt, ankunft, datum, selected_departure_time = user_input(df)

    # Format Data for further processing
    weekday, week, hour, minute, datetime_value, datetime_connection, haltestelle_ab_info, haltestelle_an_info, feiertage_data = format_data(feiertage_data, haltestellen_data, abfahrt, ankunft, datum, selected_departure_time)

    # get feiertag
    feiertag = get_feiertag(feiertage_data, datum)

    # filter data
    df = df[df['haltestelle_ab'] == abfahrt]

    # get relevant connections
    relevant_connections = df.loc[df[f'haltestelle_an_{ankunft}'] == 1] # get relevant connections

    # get column names starting with LINIEN_TEXT
    linien_list = [col.split('_')[2] for col in relevant_connections.columns if col.startswith('LINIEN_TEXT')] # get linien from column names of relevant connections

    #### Access API information
    #########################################################

    # Check for errors and get weather data
    if datetime_value <= datetime.now() - pd.Timedelta(minutes=5):
        st.error('Bitte wähle ein Datum in der Zukunft')
    elif datetime_value > datetime.now() + pd.Timedelta(days=5):
        st.error('Bitte wähle ein Datum in den nächsten 5 Tagen, damit wir dir eine Vorhersage machen können mit Wetterdaten')
    else:
        Temperatur, Niederschlag, Luftfeuchtigkeit, Schnee, Wind = create_weather(abfahrt, datetime_value)
    
    # Get data form SBB API, if abfahrt and ankunft are not the same
    if abfahrt == ankunft:
        st.error('Bitte wähle eine andere Ankunftsstation. Ankunft und Abfahrt dürfen nicht identisch sein.')
    else:
        departure, arrival, duration, line_id, prediction_available, line_text = get_connection(haltestelle_ab_info, abfahrt, haltestelle_an_info, ankunft, datetime_connection, linien_list)
    
    # Get twitter data
    # twitter = get_twitter()

    # predict delay
    if st.button('Verbindungen anzeigen'):
        for i in range(len(departure)):
            # convert utc time to local time
            utc_time_dep = datetime.strptime(departure[i], "%Y-%m-%dT%H:%M:%SZ")
            local_timezone = pytz.timezone('Europe/Zurich')
            local_time_dep = utc_time_dep.astimezone(local_timezone).strftime("%Y-%m-%d %H:%M")
            utc_time_arr = datetime.strptime(arrival[i], "%Y-%m-%dT%H:%M:%SZ")
            local_time_arr = utc_time_arr.astimezone(local_timezone).strftime("%Y-%m-%d %H:%M")
            
            local_time_dep = (datetime.strptime(departure[i], "%Y-%m-%dT%H:%M:%SZ") + pd.Timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            local_time_arr = (datetime.strptime(arrival[i], "%Y-%m-%dT%H:%M:%SZ") + pd.Timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            
            duration_time = isodate.parse_duration(duration[i])
            duration_str = str(duration_time)

            # Extract hours, minutes, and seconds from the duration string
            hours = int(duration_str.split(':')[0])
            minutes = int(duration_str.split(':')[1])
            seconds = int(duration_str.split(':')[2])

            # function to create df
            df_models = create_df(ankunft, weekday, week, hours, minutes, feiertag, Temperatur, Niederschlag, Luftfeuchtigkeit, Wind, line_text, df_cols)

            # Format the time as "hh:mm:ss"
            formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            st.markdown(
                f"""
                <div class="connection">
                    <table>
                        <tr>
                            <td><div class="departure">Abfahrt: <br><b>{local_time_dep.split(' ')[1]} - {abfahrt}</b></div></td>
                            <td><div class="departure">Ankunft: <br><b>{local_time_arr.split(' ')[1]} - {ankunft}</b></div></td>
                            <td><div class="departure">Dauer: <br><b>{formatted_time}</b></div></td>
                            <td><div class="departure">Datum: <br><b>{local_time_dep.split(' ')[0]}</b></div></td>
                        </tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
            """
            <style>
            .connection {
                background-color: #eb0000;
                margin-bottom: 10px;
                padding: 10px;
                color: #ffffff;
            }
            table {
                border-collapse: collapse;
            }
            table tr td {
                border: none;
            }
            div [data-testid="stHorizontalBlock"] {
                padding-bottom: 1rem;
            }
            div [data-testid="stHorizontalBlock"] p {
                margin: 0;
            }
            </style>
            """,
            unsafe_allow_html=True
            )
            st.subheader('Vorhersage für Ihre Zugverbindung')

            row2_col1, row2_col2 = st.columns([1, 1])
            row2_col1.markdown('**Abfahrtszeit:** {}'.format(local_time_dep))
            row2_col1.markdown('**Ankunftszeit:** {}'.format(local_time_arr))
            row2_col1.markdown('**Dauer:** {}'.format(formatted_time))
            row2_col1.markdown(f"**Wochentag:** {datum.strftime('%A')} {'(Feiertag)' if feiertag == 1 else ''}")
            row2_col1.markdown('**Linie:** {}'.format(line_text[i]))
            row2_col2.markdown('**Temperatur:** {:.2f} °C'.format(Temperatur))
            row2_col2.markdown('**Niederschlag:** {}'.format(Niederschlag))
            row2_col2.markdown('**Luftfeuchtigkeit:** {}'.format(Luftfeuchtigkeit))
            row2_col2.markdown('**Wind:** {}'.format(Wind))

            # Predict delay
            if prediction_available[i] == 1:
                model = load_model(abfahrt)
                # if twitter != None:
                #     X = add_twitter_info(df_models, twitter)
                #     pd.get_dummies(X, columns=['Einschr_Type'])
                # else:
                X = df_models
                delay_prediction = model.predict(X)[0]
                row2_col2.markdown('**Vorhersage: :red[{:.4f}]** Minuten Verspätung'.format(delay_prediction))
                metrics = pd.read_csv('./Modell/Orte/metrics.csv')
                m = metrics[(metrics['modelname'] == 'XGBRegressor') & (metrics['station'] == abfahrt)]
                row2_col2.markdown('**Vorhersagegenauigkeit: R2 von :red[{:.4f}]** und **RMSE von :red[{:.4f}]**'.format(m['R2'].values[0], m['RMSE'].values[0]))
            else:
                row2_col2.markdown('**Vorhersage:** :red[für diese Linie nicht verfügbar]')
connection_app()
