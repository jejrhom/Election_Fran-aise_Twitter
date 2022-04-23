import tweepy
import pandas as pd
import requests
from bs4 import BeautifulSoup
from credentials import *
from datetime import datetime, timedelta
from nltk.corpus import stopwords
import re
from textblob import TextBlob
from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import sys
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64



consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
api_twitter = tweepy.API(auth, wait_on_rate_limit=True)
auth_api = API(auth)

def Election_France(name_candidat) :

    def generate_urlCandidat(name_candidat):
        url = "https://news.search.yahoo.com/search?q={}".format(name_candidat)
        return url

    def generate_urlPicture(name_candidat):
        url_pic = "https://images.search.yahoo.com/search/images?q={}".format(name_candidat)
        return url_pic

    def scrap_img(url_pic):
        list_links = []
        response = requests.get(url_pic)
        soup = BeautifulSoup(response.text, 'html.parser')
        i = 0
        for item in soup.find_all('img', class_="process"):
            if i < 1 and len(list_links) < 1 :
                list_links.append(item["data-src"])
                i =+1
            else : 
                break
        return list_links[0]

    url_pic = generate_urlPicture(name_candidat)
    pic_candidat = scrap_img(url_pic)
    url_candidat = generate_urlCandidat(name_candidat)



    def scrap_news(url_candidat) :
        news = {"titles":[],"sources":[],"times":[], "times_hours":[],"links":[]}
        links_list = []
        time_hours = 0
        response = requests.get(url_candidat)
        soup = BeautifulSoup(response.text, 'html.parser')
        for news_item in soup.find_all('div', class_='NewsArticle'):
            title = news_item.find(['h4']).text
            time = news_item.find('span', class_='fc-2nd').text
            source = news_item.find("span", class_ ="s-source mr-5 cite-co").text
            link = news_item.find('a')["href"]
            # Clean time text and generate hours from publication to order the news in a timely manner
            time = time.replace('·', '').strip()
            if 'days' in time or 'day' in time :
                time_hours = int(time.split(" ")[0])*24
            else : 
                time_hours = int(time.split(" ")[0])
            news["titles"].append(title)
            news["sources"].append(source)
            news["times"].append(time)
            news["times_hours"].append(time_hours)
            news["links"].append(link)
        return news

    newsmetadata = pd.DataFrame(scrap_news(url_candidat)).sort_values("times_hours")
    newsmetadata['title_source']=newsmetadata['titles']+' - '+newsmetadata['sources']

    articles_dic = dict(zip(newsmetadata.title_source, newsmetadata.links))

    #Twitter Data


    DictDesCandidats = {"Candidat1" : {"Id": 1976143068, "Nom":"Emmanuel Macron"},
         "Candidat2" : {"Id": 80820758, "Nom":"Jean-Luc Mélenchon"}, "Candidat3" : {"Id":1183418538285027329, "Nom":"Eric Zemmour"}, "Candidat4" : {"Id":217749896 ,"Nom":"Marine Le Pen"}
    }

    def metadataduCandidat(DictDesCandidats, name_candidat) : 
        IdTwitter = [v for v in DictDesCandidats.values() if name_candidat in v.values()][0]["Id"]
        NomCandidat = [v for v in DictDesCandidats.values() if name_candidat in v.values()][0]["Nom"]
        data = auth_api.get_user(user_id= int(IdTwitter))
        PseudoTwitter = "@"+str(data.screen_name)
        Description = data.description
        NombreTweets = str(data.statuses_count)
        NombreAmis = str(data.friends_count)
        NombreFollowers = str(data.followers_count)
        NbrdeFavoris = str(data.favourites_count)
        PhotoProfil = data.profile_image_url_https
        URL_Twitter = "https://twitter.com/" + str(data.screen_name)
        return {"IdTwitter": IdTwitter, "Nom":NomCandidat, "PseudoTwitter" : PseudoTwitter, "Description" : Description, "NombreTweets" : NombreTweets, "NombreAmis": NombreAmis, "NombreFollowers": NombreFollowers, "NombreFavoris":NbrdeFavoris,"PhotoProfil":PhotoProfil,"URLTwitter":URL_Twitter}
    metadataduCandidat = metadataduCandidat(DictDesCandidats, name_candidat)

    import datetime
    import pytz

    utc=pytz.UTC

    def TweetsCandidatsnDays(IdTwitter, days = 30 ):
        tweet_count = 0
        DatedeFin = datetime.datetime.utcnow() - timedelta(days)
        DictTweets = {"Tweets" :[],"DateDeCreation":[]}
        for status in Cursor(auth_api.user_timeline, id = IdTwitter).items() :
            tweet_count +=1
            DictTweets["Tweets"].append(status.text)
            DictTweets["DateDeCreation"].append(status.created_at)
            if status.created_at < utc.localize(DatedeFin) :
                break
        TweetsCandidatsnDays = pd.DataFrame(list(zip(DictTweets["Tweets"], DictTweets["DateDeCreation"])),
                   columns =['Tweet', 'DateDeCreation'])
        return TweetsCandidatsnDays

    TweetsCandidatsnDays = TweetsCandidatsnDays(IdTwitter=metadataduCandidat["IdTwitter"])

    my_file = open("C:/Users/Jad/Desktop/stopwords French.txt", "r", encoding='utf-8')
    stopWordsFrench = my_file.read().split(",")
    def clean_tweet(TweetsCandidatsnDays):
        tweet_clean = []
        tweet_noStopWords = []
        stopWords = stopwords.words('english') + stopwords.words('french') + stopWordsFrench
        for tweet in TweetsCandidatsnDays["Tweet"] :
            tweet_clean.append(' '.join(re.sub('(@[A-Za-z0-9]+)|(\w+:\/\/\S+)|[^A-zÀ-ú]+|([RT])', ' ', tweet.lower()).split()))
        for t in tweet_clean :
            tweet_noStopWords.append(' '.join([word for word in t.split() if word not in stopWords]))
        TweetsCandidatsnDays["Tweet_clean"] = tweet_noStopWords
        return TweetsCandidatsnDays

    TweetsCandidats = clean_tweet(TweetsCandidatsnDays)
    Top50 = pd.DataFrame(pd.DataFrame(' '.join(TweetsCandidats['Tweet_clean']).lower().split()).value_counts()[:50]).rename_axis('Mot').reset_index()
    #Keep only words with length > 4
    img = BytesIO()
    MotsTweets = Top50[Top50['Mot'].str.len() > 4]
    wordcloud = WordCloud(background_color = "white", stopwords = stopWordsFrench, max_words = 50).generate(' '.join(MotsTweets['Mot']))    
    plt.figure(figsize=(5,3))
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')


    results = [pic_candidat, metadataduCandidat["Nom"], articles_dic, metadataduCandidat["Description"], metadataduCandidat["PseudoTwitter"], metadataduCandidat["NombreTweets"], metadataduCandidat["NombreAmis"], metadataduCandidat["NombreFollowers"], plot_url, metadataduCandidat["NombreFavoris"], metadataduCandidat["URLTwitter"]]
    return results