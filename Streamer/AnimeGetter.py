from PIL import Image
import requests
import urllib
import json
import time
import bs4
import os
url="https://gogoanime.ai"
seriesFolder = os.path.join("static","series")
thumbnailFolder=os.path.join("static","thumbnails")
headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"}

folders=["static/series","static/subtitles","static/thumbnails","static/archive","static/searchtemplates"]
for i in folders:
    try:
        os.mkdir(i)
    except Exception:
        continue
messages = []
notWorkingURLs=[]
breakDuration=60

import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
engine = db.create_engine('sqlite:///data.db')
Base = declarative_base()

class titleUrls(Base):
    __tablename__="title_urls"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)

def wait(breakDuration):
    print("Timeout!!!\nStarting in {breakDuration} minutes again!!!".format(
        breakDuration=breakDuration / 60))
    time.sleep(breakDuration)
    print("Starting again")

def searchForAnime(searchTerm):
    ajax="https://ajax.gogo-load.com/site/loadAjaxSearch?keyword={}&id=-1&link_web=https%3A%2F%2Fgogoanime.ai%2F".format(searchTerm)
    req=requests.get(ajax,headers=headers)
    content = json.loads(req.text)["content"]
    soup=bs4.BeautifulSoup(content, 'html.parser')
    animeUrls=[]
    for i in soup.find_all("a"):
        animeUrls.append(i.get("href"))
    return animeUrls

def getEpisodeBox(animeUrl,thumbnailOnly=False):
        animeName=animeUrl.split("/")[-1]
        try:
            if animeName+".thumbnail".replace(" ","%20") not in os.listdir(thumbnailFolder):
                animeName=animeUrl.split("/")[-1]
                site=requests.get(animeUrl,headers=headers)
                soup=bs4.BeautifulSoup(site.text,'html.parser')
                id=soup.find(id="movie_id").get("value")
                print(f"Downloading thumbnail for {animeName}")
                req=urllib.request.Request(
                            soup.find(class_="anime_info_body_bg").find("img").get("src").replace(" ","%20"),
                            headers=headers
                )

                webpage = urllib.request.urlopen(req).read()

                with open(os.path.join(os.getcwd(),thumbnailFolder,animeName), 'wb') as handler:
                    handler.write(webpage)

                im = Image.open(os.path.join(os.getcwd(),thumbnailFolder,animeName))
                rgb_im = im.convert('RGB')
                rgb_im=rgb_im.resize((250,330))
                rgb_im.save(os.path.join(os.getcwd(),thumbnailFolder,animeName+".thumbnail"),"JPEG")
                os.remove(os.path.join(os.getcwd(),thumbnailFolder,animeName))
        except Exception as ex:
            print("Error while downloading thumbnail:",ex)

        if ~thumbnailOnly:
            site=requests.get(animeUrl,headers=headers)
            soup=bs4.BeautifulSoup(site.text,'html.parser')
            id=soup.find(id="movie_id").get("value")
            Session = sessionmaker(bind=engine)
            session=Session()
            if session.query(titleUrls).filter_by(title=animeName).first()==None:
                session.add(titleUrls(title=animeName,url=animeUrl))
                session.commit()
            session.close()
            ajax="https://ajax.gogo-load.com/ajax/load-list-episode?ep_start=0&ep_end=1000&id={}&default_ep=0&alias={}".format(id,animeName)
            req=requests.get(ajax,headers=headers)
            soup=bs4.BeautifulSoup(req.text, 'html.parser')
            episodeUrls=[]



            for i in soup.find_all("a"):
                episodeUrls.append(url+i.get("href").replace(" ",""))
            return episodeUrls

def getDownloadUrl(episodeUrl,ignoreURLs=[]):
    req=requests.get(episodeUrl,headers=headers)
    soup=bs4.BeautifulSoup(req.text, 'html.parser')
    downloadSiteUrl=soup.find(class_="dowloads").find("a").get("href")
    req=requests.get(downloadSiteUrl,headers=headers)
    soup=bs4.BeautifulSoup(req.text, 'html.parser')
    downloadUrls=[]
    for i in soup.find_all(class_="dowload"):
        text=i.find("a").text[i.find("a").text.find("(")+1:i.find("a").text.find(")")]
        downloadUrls.append({"url":i.find("a").get("href"),"text":text})

    prefeared=["HD","1080","720","480","360"]

    downloadUrl=downloadUrls[0]["url"]
    for i in prefeared[::-1]:
        for j in downloadUrls:
            if j["url"] in ignoreURLs:
                    break
            if i in j["text"]:
                downloadUrl=j["url"]
                break

    return downloadUrl


def downloadUrl(url, folderName, fileName):
    print("Downloading {url}".format(url=url))
    try:
        request_=urllib.request.Request(url,None,headers)
        response = urllib.request.urlopen(request_)
        data = response.read()
        f = open( os.path.join(os.getcwd(),folderName, fileName),'wb')
        f.write(data)
        f.close()
        numOfEpisode=fileName.replace(".mp4","")

        messages.append("Download of episode {episode} completed".format(episode=numOfEpisode))
        print("Download of {url} completed".format(url=url))

    except Exception as e:
        messages.append("Error:" + str(e))
        print(f"Error while downloading {url}", e, "\n")
        list(set(notWorkingURLs.append(url)))
        print(f"Added {url} to not working URLs")



def downloadAnime(animeUrl):
    global seriesFolder
    epi = getEpisodeBox(animeUrl)
    folderName = animeUrl.split("/")[-1].replace("/", "")
    Session = sessionmaker(bind=engine)
    session=Session()
    t=session.query(titleUrls).filter_by(title=seriesFolder).first()
    if session.query(titleUrls).filter_by(title=seriesFolder).first()==None:
        session.add(titleUrls(title=seriesFolder,url=animeUrl))
        session.commit()
    session.close()
    try:
        fileList = os.listdir(os.path.join(os.getcwd(),seriesFolder,folderName))
    except Exception as e:
        os.mkdir(os.path.join(os.getcwd(),seriesFolder, folderName))
        fileList = os.listdir(os.path.join(os.getcwd(),seriesFolder, folderName))
    errors=[]
    downloaded = (int(x.replace(".mp4", "")) for x in fileList)
    download = set(range(1, len(epi) + 1)) - set(downloaded)
    while len(download)!=len(list(downloaded)):
        fileList = os.listdir(os.path.join(os.getcwd(),seriesFolder, folderName))
        downloaded = (int(x.replace(".mp4", "")) for x in fileList)
        download = set(range(1, len(epi) + 1)) - set(downloaded)
        for j in download:
            print("Downoloading {downloading} of {numOfEpisodes}".format(
                downloading=j, numOfEpisodes=len(epi)))
            try:
                print("\n")
                print(notWorkingURLs)
                url = getDownloadUrl(epi[len(epi) - j],ignoreURLs=notWorkingURLs)
                fileName = str(j) + ".mp4"
                downloadUrl(url, os.path.join(os.getcwd(),seriesFolder, folderName), fileName)
                print("\n")
            except Exception as e:
                print(f"Error while downloading episode {os.path.join(os.getcwd(),seriesFolder, folderName)}\n")

                wait(60)
                continue


def popularOngoing():
    global url
    ajax="https://ajax.gogo-load.com/ajax/page-recent-release-ongoing.html?page={}"
    retTitles=[]

    for i in range(1,6):
        req=requests.get(ajax.format(i))
        soup=bs4.BeautifulSoup(req.text,"html.parser")
        box=soup.find(class_="added_series_body popular")
        titles=box.find_all("li")
        for j in titles:
            url_=j.find("a").get("href")
            title=j.find("a").get("href").split("/")[-1]
            getEpisodeBox(url+"/"+url_,thumbnailOnly=True)
            try:
                latest=j.find_all("p")[1].find("a").get("title").split("-")[-1]
            except Exception as e:
                print("Error while handling title:",e,title)
                latest=""
            retTitles.append({"title":title,"url":url_,"latest":latest})

    return retTitles

def newReleases():
    global url
    ajax="https://ajax.gogo-load.com/ajax/page-recent-release.html?page=1&type=1"
    retTitles=[]
    req=requests.get(ajax)
    soup=bs4.BeautifulSoup(req.text,"html.parser")
    box=soup.find(class_="items")
    titles=box.find_all("li")
    for i in titles:
        anker=i.find("p").find("a")
        title=anker.get("href").split("-episode-")[0]
        try:
            latest=anker.get("href").split("-episode-")[1]
        except Exception as e:
            print(e,"while handling title:",title)
            latest=""
        url_=f"{url}/category{title}"
        try:
            getEpisodeBox(url_,thumbnailOnly=True)
        except Exception as e:
            print("Error while handling title:",e,title)
            continue
        retTitles.append({"title":title.replace("/",""),"url":url_,"latest":latest})

    return retTitles

if __name__== "__main__":
    anime = []
    while True:
        searchTerm = input("Search for anime:")
        anime = list(set(searchForAnime(searchTerm)))
        if anime != []:
            break
    print("The results are:")
    for i in range(len(anime)):
        print("     ", i + 1, ".", anime[i])
    selected = str(input(
        "Select what you want(seperate indexes with ',' for more options):")).split(",")
    for i in range(len(selected)):
        selected[i] = int(selected[i]) - 1
    for i in selected:
        downloadAnime(anime[i])