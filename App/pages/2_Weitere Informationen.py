import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import plot_importance
import seaborn as sns
import pydeck as pdk
import os

# Change directory to App
cwd = os.getcwd()
if not cwd.endswith('App'):
    os.chdir(os.getcwd() + '/App')

# Load model
st.cache_data()
def load_model(twittermodel=False):
    if twittermodel:
        model = pickle.load(open("./Modell/model_twitter.pkl", "rb"))
    else:
        model = pickle.load(open("./Modell/model.pkl", "rb"))
    return model

# Load Data
st.cache_data()
def load_data(twitterdata=False):
    if twitterdata:
        df = pd.read_csv('./Daten/data_expanded/data_with_features_twitter.csv')
    else:
        df = pd.read_csv('./Daten/data_expanded/data_with_features.csv')
    return df

st.cache_data()
def create_long_df(df):
    df_long = df.copy()
    haltestellen_cols = [col for col in df.columns if col.startswith('haltestelle_an_')]
    linien_cols = [col for col in df.columns if col.startswith('LINIEN_TEXT')]
    df_long['haltestelle_an'] = df_long[haltestellen_cols].idxmax(axis=1).str.replace('haltestelle_an_', '')
    df_long['linie'] = df_long[linien_cols].idxmax(axis=1).str.replace('LINIEN_TEXT_', '')
    return df_long, haltestellen_cols, linien_cols

def create_locations(df):
     #Prepare coordinates and labels
    locations = {
    'haltestelle_an_Basel SBB': ['Basel SBB', 47.547589, 7.589662],
    'haltestelle_an_Bern': ['Bern', 46.94753, 7.43976],
    'haltestelle_an_Lugano': ['Lugano', 46.00536, 8.94646],
    'haltestelle_an_Olten': ['Olten', 47.35196, 7.90692],
    'haltestelle_an_Zürich HB': ['Zürich', 47.3784, 8.54024],
    'haltestelle_an_Luzern': ['Luzern', 47.05018, 8.31018],
    'haltestelle_an_St. Gallen': ['St. Gallen', 47.42318, 9.3699],
    }
    location_data = []
    # Prepare data for each location
    for location in locations:
        loc_data = df[df[location] == 1]
        average_delay = round(loc_data['AN_diff'].mean(), 3)  # Rounding to 2 decimal places
        location_data.append({'city': locations[location][0],
                            'lon': locations[location][2],
                            'lat': locations[location][1],
                            'delay': f"{average_delay} Min",  # Adding 'Min' to the delay
                            'delay_num': average_delay*3000})  # Adding the delay as a number
    location_df = pd.DataFrame(location_data)
    return location_df

def create_map(location_df):
    # Create map
    view_state = pdk.ViewState(
        latitude=46.8182,
        longitude=8.2275,
        zoom=6.8,
        min_zoom=5,
        max_zoom=15,
        pitch=0,    # set pitch to 0 for a 2D view
        bearing=0   # set bearing to 0 to align north to top
    )
    # Create the layer for the map
    layer = pdk.Layer(
        "ScatterplotLayer",
        location_df,
        get_position=["lon", "lat"],
        get_radius=["delay_num"],
        get_fill_color=[200, 30, 0, 255],
        pickable=True,  
    )
    tooltip = {
        "html": "<b>{city}:</b> {delay}",
        "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
    }
    map_ = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    )
    return map_
    
def create_dichteplot(df_long):

    # SNS kdeplot
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.kdeplot(data=df_long, x='AN_diff', hue='haltestelle_an', ax=ax, palette='husl')
    ax.set_xlabel('Verspätung [min]')
    ax.set_ylabel('Häufigkeit')
    ax.set_xlim(-10, 25)
    # make plot background transparent
    ax.patch.set_alpha(0)
    ax.set_facecolor('b')
    fig.patch.set_alpha(0)
    fig.set_facecolor('b')

    # make x and y axis white
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')
    ax.tick_params(axis='x', colors='w')
    ax.tick_params(axis='y', colors='w')
    ax.yaxis.label.set_color('w')
    ax.xaxis.label.set_color('w')
    ax.title.set_color('w')
    ax.set_title('Verteilung der Ankunftsverspätung pro Haltestelle', color='w')

    return fig

def create_linienplot(df_long):
    # Plot Number of entries per Linie
    # Select linen to plot
    linien = df_long['linie'].unique()
    selected_linien = st.multiselect("Wählen Sie die Linien aus, die Sie anschauen möchten.", linien, default=linien[0:5])
    # Filter df_long for selected_linien
    df_long = df_long[df_long['linie'].isin(selected_linien)]
    # Plot
    fig, ax = plt.subplots(figsize=(10, 5*(len(selected_linien)/len(linien))))
    sns.countplot(y='linie', data=df_long, ax=ax, palette='tab10', order=df_long['linie'].value_counts(ascending=True).index)
    ax.set_ylabel('Linie')
    ax.set_xlabel('Anzahl Einträge')

    # make plot background transparent
    ax.patch.set_alpha(0)
    ax.set_facecolor('b')
    fig.patch.set_alpha(0)
    fig.set_facecolor('b')

    # make x and y axis white
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')
    ax.tick_params(axis='x', colors='w')
    ax.tick_params(axis='y', colors='w')
    ax.yaxis.label.set_color('w')
    ax.xaxis.label.set_color('w')
    ax.title.set_color('w')
    ax.set_title('Anzahl Einträge pro Linie', color='w')
    return df_long, fig


def create_weekly_delay(df_long):
    df_long['woche'] = pd.to_datetime(df_long['BETRIEBSTAG']).dt.isocalendar().week
    df_long['woche'] = df_long['woche'].astype(int)
    avg_delay = df_long.groupby(['linie', 'woche'])['AN_diff'].mean().reset_index()
    # Lineplot delays per Linie and day
    fig, ax = plt.subplots()
    sns.lineplot(x='woche', y='AN_diff', hue='linie', style='linie', data=avg_delay, ax=ax, palette='husl')
    ax.set_ylabel('Durschnittliche Verspätung [min]')
    ax.set_xlabel('Kalenderwoche')
    ax.legend(title='Linie')

    # make plot background transparent
    ax.patch.set_alpha(0)
    ax.set_facecolor('b')
    fig.patch.set_alpha(0)
    fig.set_facecolor('b')

    # make x and y axis white
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')
    ax.tick_params(axis='x', colors='w')
    ax.tick_params(axis='y', colors='w')
    ax.yaxis.label.set_color('w')
    ax.xaxis.label.set_color('w')
    ax.title.set_color('w')
    ax.set_title('Durschnittliche Verspätung pro Linie und Kalenderwoche', color='w')
    return fig

def create_model(df, model, haltestellen_cols, linien_cols):

    # Defne X and y
    X = df.drop(['AN_diff', 'BETRIEBSTAG'], axis=1)
    y = df['AN_diff']

    # Split data into train and test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=4153)

    # Predict y
    y_pred = model.predict(X_test)

    # Create dataframe with y_test, y_pred, X_test and haltestellen_cols
    df_pred = pd.DataFrame({'y_test': y_test, 'y_pred': y_pred})
    df_pred = pd.concat([df_pred, X_test], axis=1)
    df_pred['haltestelle'] = df_pred[haltestellen_cols].idxmax(axis=1).str.replace('haltestelle_an_', '')
    df_pred['linie'] = df_pred[linien_cols].idxmax(axis=1).str.replace('LINIEN_TEXT_', '')

    # Evaluate model
    r2 = r2_score(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    return df_pred, r2, rmse

def create_scatterplot(df_plot, selector=True):
    # Drop y_pred and y_test > 400
    df_plot = df_plot[(df_plot['y_test'] < 400) & (df_plot['y_pred'] < 400)]
    df_plot['linie_type'] = df_plot['linie'].str.replace(r'\d+', '', regex=True)

    if selector:
        selected_linien = st.multiselect("Wählen Sie die Linien aus, die Sie anschauen möchten.", df_plot['linie_type'].unique(), default=df_plot['linie_type'].unique()[0:5])
        df_plot = df_plot[df_plot['linie_type'].isin(selected_linien)]

    # Create the plot
    fig, ax = plt.subplots()
    sns.scatterplot(data=df_plot, x='y_test', y='y_pred', alpha=0.1, hue='linie_type', ax=ax)
    ax.set_xlabel('y_test (in Min)')
    ax.set_ylabel('y_pred (in Min)')

    # Calculate y_min and y_max
    y_min = min(df_plot['y_test'].min(), df_plot['y_pred'].min())
    y_max = max(df_plot['y_test'].max(), df_plot['y_pred'].max())

    # Add line with x=y with y_min and y_max
    ax.plot([y_min, y_max], [y_min, y_max], color='w')

    # make plot background transparent
    ax.legend(title='Linien Typ')
    ax.patch.set_alpha(0)
    ax.set_facecolor('b')
    fig.patch.set_alpha(0)
    fig.set_facecolor('b')
    
    # make x and y axis white
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')
    ax.tick_params(axis='x', colors='w')
    ax.tick_params(axis='y', colors='w')
    ax.yaxis.label.set_color('w')
    ax.xaxis.label.set_color('w')
    ax.title.set_color('w')
    ax.set_title('Vergleich y_test und y_pred', color='w')
    
    return fig

def create_importanceplot(model):
    # Plot feature importance
    fig, ax = plt.subplots()
    plot_importance(model, ax=ax, max_num_features=15)

    # make plot background transparent
    ax.patch.set_alpha(0)
    ax.set_facecolor('b')
    fig.patch.set_alpha(0)
    fig.set_facecolor('b')

    # make x and y axis white
    ax.spines['bottom'].set_color('w')
    ax.spines['left'].set_color('w')
    ax.tick_params(axis='x', colors='w')
    ax.tick_params(axis='y', colors='w')
    ax.yaxis.label.set_color('w')
    ax.xaxis.label.set_color('w')
    ax.title.set_color('w')
    ax.set_title('Feature Importance', color='w')

    #make information white
    for text in ax.texts:
        text.set_color('w')

    # make bars white
    for patch in ax.patches:
        patch.set_facecolor('red')

    return fig

def run_details():
    # hide menu
    hide_menu_style = """
            <style>
            #MainMenu {visibility: visible;}
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
    #load model
    model = load_model(True)
    #load data
    df = load_data(True)
    df_long, haltestellen_cols, linien_cols = create_long_df(df)
    #create locations for train stations
    location_df = create_locations(df_long)
    st.title("Weitere Informationen")
    st.write("Hier finden Sie vertiefte Informationen zu unseren Daten, unseren Vorhersagen und unserem Modell!")
    st.subheader("Informationen zu Verspätungen der SBB und dem Datensatz")
    st.write("**Erfahren Sie mehr über die durchschnittliche Verspätung an den verschiedenen SBB-Bahnhöfen in der Karte.**")
    # Create map from train station locations
    map_ = create_map(location_df)
    # Render the map
    st.pydeck_chart(map_)
    st.write("---")
    st.write("**Vergleichen Sie die Verspätungen an den verschiedenen Standorten.**")
    fig = create_dichteplot(df_long)
    # create dichteplot
    st.pyplot(fig)
    st.write("---")
    st.write("**Anzahl Einträge pro Haltestelle und Verspätung im Zeitverlauf:**")
    df_long, fig2 = create_linienplot(df_long)
    # create linienplot
    st.pyplot(fig2)
    # create weekly delay
    fig3 = create_weekly_delay(df_long)
    st.pyplot(fig3)
    if st.checkbox('Datensatz anzeigen'):
    # Schieberegler zur Auswahl der Zeilenanzahl
        rows = st.slider('Wähle die Anzahl der Zeilen:', 1, 100, 10)
        st.table(df_long.head(rows))
    ####### Explore the model #######
    st.write("---")
    st.subheader("Erfahren Sie mehr über unser Modell")
    res_df, r2, rmse = create_model(df, model, haltestellen_cols, linien_cols)
    col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 1, 4])
    col1.image("./img/r2.png", width=40)
    col2.markdown("Unser aktuelles Modell haben einen R2-Wert von \n:red[{}]".format(r2))
    col4.image("./img/rmse.png", width = 20)
    col5.markdown("Unser aktuelles Modell haben einen RMSE von \n:red[{}]".format(rmse))
    st.write("---")
    st.write("**Vergleichen der Vorhersage mit den tatsächlichen Werten.**")
    # Create scatterplot von pred und test
    fig4 = create_scatterplot(res_df)
    st.pyplot(fig4)
    st.write("---")
    # Plot feature importance
    st.write("**Wichtigkeit der Features:**")
    fig5 = create_importanceplot(model)
    st.pyplot(fig5)
    st.write("---")
    st.write("**Modell ohne die Twitterdaten.**")
    # Look at model with twitter data
    df_ohne_twitter = load_data(False)
    #create locations for train stations
    model_ohne_twitter = load_model(False)
    res_df_t, r2_t, rmse_t = create_model(df_ohne_twitter, model_ohne_twitter, haltestellen_cols, linien_cols)
    col6, col7, col8, col9, col10 = st.columns([1, 4, 2, 1, 4])
    col6.image("./img/r2.png", width=40)
    col7.markdown("Unser aktuelles Modell haben einen R2-Wert von :red[{}]".format(r2_t))
    col9.image("./img/rmse.png", width = 20)
    col10.markdown("Unser aktuelles Modell haben einen RMSE von :red[{}]".format(rmse_t))
    st.write("---")
    # Create scatterplot von pred und test
    fig6 = create_scatterplot(res_df_t, False)
    st.pyplot(fig6)
    st.write("---")
    st.write("**Wichtigkeit der Features:**")
    fig7 = create_importanceplot(model_ohne_twitter)
    st.pyplot(fig7)

run_details()




    








