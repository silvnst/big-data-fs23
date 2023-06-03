import snscrape.modules.twitter as sntwitter
import pandas as pd

def get_twitter_data(query, max_tweets, haltestellen):

    # function takes a query, the maximum number of tweets to be scraped and 
    # a list of stations as input and returns a dataframe with the tweets and their attributes.
    
    # Created a list to append all tweet attributes(data)
    attributes_container = []

    # Using TwitterSearchScraper to scrape data and append tweets to list
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i>max_tweets:
            break
        # Check if tweet.content has one of the keywords
        if any(keyword in tweet.content.lower() for keyword in haltestellen):
            attributes_container.append([tweet.date, tweet.likeCount, tweet.sourceLabel, tweet.content])
        
        if i % 500 == 0:
            print(i)
        
    # Creating a dataframe from the tweets list above 
    tweets_df = pd.DataFrame(attributes_container, columns=["Date Created", "Number of Likes", "Source of Tweet", "Tweets"])
    
    # Drop unnecessary columns
    tweets_df = tweets_df.drop(["Number of Likes", "Source of Tweet"], axis=1)
    
    return tweets_df

def process_twitter_data(tweets, haltestellen, linien):

    # function takes a dataframe with tweets and a list of stations as input and returns a dataframe with the tweets and their attributes.

    # Import libraries
    import pandas as pd
    import numpy as np
    import datetime as dt

    # Find first words of all tweets which represent Einschränkungstyp
    tweets['Einschr_type'] = tweets['Tweets'].str.split().str[0]

    # delete links from tweets
    tweets['Tweets'] = tweets['Tweets'].str.replace('http\S+|www.\S+', '', case=False, regex=True)

    # tweets to lower case
    tweets['Tweets'] = tweets['Tweets'].str.lower()

    # extract all stations from tweets in a list
    tweets['haltestellen'] = tweets['Tweets'].str.findall('|'.join(haltestellen))

    # replace all 'ic ' with 'ic' in tweets and 'ir ' with 'ir'
    tweets['Tweets'] = tweets['Tweets'].str.replace('ic ', 'ic', case=False, regex=True)
    tweets['Tweets'] = tweets['Tweets'].str.replace('ir ', 'ir', case=False, regex=True)    

    # extract all stations from tweets in a list
    tweets['linien'] = tweets['Tweets'].str.findall('|'.join(linien))

    # filter rows with empty lists
    tweets = tweets.loc[tweets['linien'].str.len() != 0]

    tweets['zeiten'] = tweets['Tweets'].str.findall('\d{2}\:\d{2}\s-\s\d{2}\:\d{2}')

    # Zeiten mehrtägig
    tweets['zeiten_multiple'] = tweets['Tweets'].str.findall('\d{2}\.\d{2}\.\d{4}\s\d{2}\:\d{2}\s-\s\d{2}\.\d{2}\.\d{4}\s\d{2}\:\d{2}')

    # Recode empty lists in zeiten and zeiten_multiple with NaN
    tweets['zeiten'] = tweets['zeiten'].apply(lambda x: np.nan if len(x)==0 else x)
    tweets['zeiten_multiple'] = tweets['zeiten_multiple'].apply(lambda x: np.nan if len(x)==0 else x)

    # Split Datum_ab, Zeit_ab, Zeit_bis and Datum_bis
    tweets['Datum_ab'], tweets['Zeit_ab'], x, tweets['Datum_bis'], tweets['Zeit_bis'] = zip(*tweets['zeiten_multiple'].apply(lambda x: x[0].split(' ') if pd.notna(x) else [np.nan, np.nan, np.nan, np.nan, np.nan]))
    tweets['Zeit_ab_m'], x, tweets['Zeit_bis_m'] = zip(*tweets['zeiten'].apply(lambda x: x[0].split(' ') if pd.notna(x) else [np.nan, np.nan, np.nan]))
    # Set Datum_bis and Datum_ab to 'Date Created' if it's 0
    tweets['Datum_bis'] = np.where(tweets['Datum_bis'].isna(), tweets['Date Created'].dt.strftime("%d.%m.%Y"), tweets['Datum_bis'])
    tweets['Datum_ab'] = np.where(tweets['Datum_ab'].isna(), tweets['Date Created'].dt.strftime("%d.%m.%Y"), tweets['Datum_ab'])

    # Fill NaN in Zeit_ab and Zeit_bis with Zeit_ab_m and Zeit_bis_m
    tweets['Zeit_ab'] = np.where(tweets['Zeit_ab'].isna(), tweets['Zeit_ab_m'], tweets['Zeit_ab'])
    tweets['Zeit_bis'] = np.where(tweets['Zeit_bis'].isna(), tweets['Zeit_bis_m'], tweets['Zeit_bis'])

    # Create a new column 'von' by combining date and time information from 'Datum_ab' and 'Zeit_ab'
    tweets['von'] = pd.to_datetime(tweets['Datum_ab'] + ' ' + tweets['Zeit_ab'], dayfirst=True, errors='coerce')
    # Create a new column 'bis' by combining date and time information from 'Datum_bis' and 'Zeit_bis'
    tweets['bis'] = pd.to_datetime(tweets['Datum_bis'] + ' ' + tweets['Zeit_bis'], dayfirst=True, errors='coerce')

    # Explode lists in haltestellen and linien
    tweets = tweets.explode('haltestellen')
    tweets = tweets.explode('linien')

    # Drop duplicates
    tweets.drop_duplicates(subset=['linien', 'haltestellen', 'Datum_ab', 'Datum_bis',], inplace=True)

    # Drop unnecessary columns
    tweets = tweets.drop(columns=['zeiten', 'zeiten_multiple', 'Zeit_ab_m', 'Zeit_bis_m', 'Datum_ab', 'Datum_bis', 'Zeit_ab', 'Zeit_bis'])

    # All linien to upper
    tweets['linien'] = tweets['linien'].str.upper()

    return tweets

def check_overlap(row, disturbances):
    
    # HELPERFUNCTION for add_twitter_info()
    # This function checks if a row from data_disturbances overlaps with a row from twitter_clean.
    # It returns a boolean and the type of the disturbance.
    
    same_place = (disturbances['haltestellen'] == row['haltestelle_ab']) | (disturbances['haltestellen'] == row['haltestelle_an'])
    start_before_arrival = disturbances['von'] <= row['AB_soll']
    end_after_departure = disturbances['bis'] >= row['AN_soll']
    overlap = same_place & start_before_arrival & end_after_departure
    if overlap.any():
        return pd.Series([True, disturbances.loc[overlap, 'Einschr_type'].values[0]])
    return pd.Series([False, ''])

def add_twitter_info(input_df, twitter):

    #function adds information from twitter to the input_df.

    input_df['haltestelle_ab'] = input_df['haltestelle_ab'].str.lower()
    input_df['haltestelle_an'] = input_df['haltestelle_an'].str.lower()

    result = input_df.apply(check_overlap, axis=1, disturbances=twitter)
    result.columns = ['disturbance_overlap', 'Einschr_type']
    new_df = pd.concat([input_df, result], axis=1)

    return new_df

def station_upper(x):
    #This function converts all stations to their correct format.
    s = x.split(' ')
    if len(s) == 1:
        return s[0].title()
    elif len(s) == 2:
        if len(s[1]) <= 3:
            return s[0].title() + ' ' + s[1].upper()
        else:
            return s[0].title() + ' ' + s[1].title()
    else:
        out = ''
        for t in s:
            out += t.title() + ' '
        return out