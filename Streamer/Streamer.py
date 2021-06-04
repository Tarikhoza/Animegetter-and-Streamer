from AnimeGetter import seriesFolder, downloadAnime, searchForAnime, messages, getEpisodeBox, getDownloadUrl,popularOngoing,newReleases
from flask import Flask, jsonify, render_template, url_for, request, redirect, json, send_from_directory
from timeStamp import generateTimeStamps
from flask_sqlalchemy import SQLAlchemy
from integrityCheck import check
from detectImage import detect
from waitress import serve
import webbrowser
import threading
import datetime
import archiver
import logging
import shutil
import psutil
import time
import os


port = 80
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


archiveFolder = os.path.join("static","archive")
UPLOAD_FOLDER = seriesFolder

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

downloading = []
packing = []
unpacking = []
timestampScanning = []

#logging.getLogger('werkzeug').setLevel(logging.ERROR)


def updateTitleTime(title):
    t=titleTime.query.filter_by(title=title).first()
    if(t):
        if(datetime.datetime.now().day-t.dateCreated.day>2):
            t.weakDayRelease=datetime.datetime.now().strftime("%A")
            t.dateCreated=datetime.datetime.now()
            db.session.commit()
    else:
        t=titleTime(title=title,weekDayRelease=str(datetime.datetime.now().strftime("%A")),dateCreated=datetime.datetime.now())
        db.session.add(t)
        db.session.commit()


class titleTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    weekDayRelease = db.Column(db.String(15), nullable=False)
    dateCreated = db.Column(db.DateTime, nullable=False,default=datetime.datetime.now())

class titleUrls(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)

class titleIntegrity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    integrity = db.Column(db.Boolean,nullable=False)

class templateSkip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    series = db.Column(db.String(80), nullable=False)
    episode = db.Column(db.Integer)
    jumpTime = db.Column(db.Float)


class Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global unpacking
        global packing
        global downloading
        global timestampScanning
        while True:
            time.sleep(10)
            for series_name in timestampScanning:
                timestampScanning.pop(timestampScanning.index(series_name))
                break
            for series_name in unpacking:
                messages.append("Unpacking " + series_name)
                archiver.unpack(series_name,  archiveFolder, UPLOAD_FOLDER)
                messages.append("Unpacking of " + series_name + " finished")
                unpacking.pop(packing.index(series_name))
                break
            for series_name in packing:
                messages.append("Packing " + series_name)
                archiver.pack(series_name, UPLOAD_FOLDER, archiveFolder)
                messages.append("Packing of " + series_name + " finished")
                packing.pop(packing.index(series_name))
                break
            for url in downloading:
                messages.append("Downloading " + url.split("/")[-1])
                downloadAnime(url)
                messages.append("Download of " + url.split("/")[-1] + " finished")
                downloading.pop(downloading.index(url))
                break
ongoinglist=[]
newList=[]
class ongoingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global ongoinglist
        global newList
        while True:
            try:
                print("Getting titles")
                newL=newReleases()
                for title in newList:
                    updateTitleTime(title["title"])
                ongoingL=popularOngoing()
                print("Getting titles finished")
                newList=newL
                ongoinglist=ongoingL
            except Exception as e:

                print("Error while getting titles",e)
                time.sleep(60)
                continue
            time.sleep(60*15)

def scanForTimeStamps(seriesName,kind):
    lines=generateTimeStamps(seriesName,name=kind)
    with open(os.path.join("static","timestamps",seriesName+".txt"),"w") as file:
        for i in lines:
            video=i["video"].split("\\")[-1].replace(".mp4","")
            timestamp=i["timestamp"]
            file.write(f"{video}:{kind}:{timestamp}\n")

def getTimeStamp(seriesName,episode):
    ret=[]
    with open(os.path.join("static","timestamps",seriesName+".txt"),"r") as file:
        lines=file.readlines()
        for i in lines:
            seriesEpisode,kind,time=i.replace("\n","").split(":")
            if seriesEpisode==str(episode):
                ret.append({kind:time})
    return ret
def get_folders():
    dir_list = os.listdir(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']))
    return sorted(dir_list)


def get_archived():
    global archiveFolder
    dir_list = os.listdir(os.path.join(os.getcwd(), archiveFolder))
    return sorted(dir_list)


@app.route("/")
def home():
    global packing
    global unpacking
    global downloading

    downloadingNames=[]
    for i in downloading:
        downloadingNames.append(i.split("/")[-1])

    folders = get_folders()
    num_of_episodes = {}

    for i in folders:
        num_of_episodes[i] = len(os.listdir(os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'], i)))

    archived = get_archived()

    for i in archived:
        folders.append(i.replace(".7z", ""))

    folders = list(set(folders))
    folders = sorted(folders)
#   print(archiver.errors, sep="\n")
    status = {}

    for i in folders:
        if i in packing:
            status[i] = "packing"
        elif i in unpacking:
            status[i] = "unpacking"
        elif i + ".7z" in archived:
            status[i] = "archived"
        elif i in downloadingNames:
            status[i] = "downloading"
        else:
            status[i] = "watchable"

    driveStats ={
        "total":str(round(shutil.disk_usage("/").total / 1000000000)),
        "used":str(round(shutil.disk_usage("/").used / 1000000000)),
        "free":str(round(shutil.disk_usage("/").free / 1000000000)),
    }
    return render_template(
        "home.html",
        folders=folders,
        status=status,
        path=os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']),
        numOfEpisodes=num_of_episodes,
        numOfTitles=len(folders),
        numOfArchived=len(archived),
        driveStats=driveStats
    )



@app.route("/pack/<string:series_name>")
def pack(series_name):
    global packing
    global unpacking
    global downloading
    downloadingNames=[]
    for i in downloading:
        downloadingNames.append(i.split("/")[-1])


    packing.append(series_name)
    return redirect(url_for("home"))

@app.route("/unpack/<string:series_name>")
def unpack(series_name):
    global unpacking
    unpacking.append(series_name)
    return redirect(url_for("home"))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico')


@app.route("/series/<string:name>")
def series(name):
    if name in get_folders():
        return render_template(
            "episodes.html",
            name=name,
            numOfEpisodes=len(os.listdir(os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'], name)))
        )
    else:
        return "File not found"


@app.route("/series/<string:name>/<string:episode>")
def watch_episode(name, episode):
    filename = "/" + name + "/" + episode + ".mp4"

    if name in os.listdir(os.path.join(os.getcwd(),seriesFolder)):
        if  episode + ".mp4" in  os.listdir(os.path.join(os.getcwd(),seriesFolder,name)):
            return render_template(
                "episode.html",
                name=name,
                numOfEpisodes=len(os.listdir(os.path.join(os.getcwd(),seriesFolder,name))) + 1,
                episode=episode,
                thEpisode=int(episode.replace(".mp4", "")),
                filename="/series/" + filename,
                path="/" + name + "/"
            )
    return redirect(url_for("live_episode", name=name, episode=episode))

@app.route("/new/series/<string:name>/<string:episode>")
def watch_episode_new(name, episode):
    filename = "/" + name + "/" + episode + ".mp4"

    if name in os.listdir(os.path.join(os.getcwd(),seriesFolder)):
        if  episode + ".mp4" in  os.listdir(os.path.join(os.getcwd(),seriesFolder,name)):
            return render_template(
                "newEpisode.html",
                name=name,
                numOfEpisodes=len(os.listdir(os.path.join(os.getcwd(),seriesFolder,name))) + 1,
                episode=episode,
                thEpisode=int(episode.replace(".mp4", "")),
                filename="/series/" + filename,
                path="/" + name + "/"
            )
    return redirect(url_for("live_episode", name=name, episode=episode))



def che():
    for i in os.listdir(seriesFolder):
        for j in range(1,len(os.listdir(os.path.join(seriesFolder,i)))+1):
            t=titleIntegrity.query.filter_by(title=f"{i}-{j}").first()
            c=check(seriesFolder, i, f"{j}.mp4")
            db.session.add(titleIntegrity(title=f"{i}-{j}",integrity=c))
            db.session.commit()

@app.route("/check/<string:name>/<string:episode>")
def check_episode(name, episode):
    t=titleIntegrity.query.filter_by(title=f"{name}-{episode}").first()
    onError="""
                <div class="container border d-flex justify-content-center bg-danger text-light">
                    <b>There may be some errors in this video</b>
                </div>"
            """
    if t:
        if t.integrity:
            return onError
        return ""
    else:
        c=check(seriesFolder, name, episode + ".mp4")
        db.session.add(titleIntegrity(title=f"{name}-{episode}",integrity=c))
        db.session.commit()
        if(c):
            return onError
        return ""

@app.route("/skip/<string:name>/<string:episode>")
def video_jumps(name,episode):
    timestamps=getTimeStamp(name,episode)
    if timestamps!=[]:
        return jsonify({"success":True,"timestamps":timestamps})

    return jsonify({"success":False,"timestamps":[]})

@app.route('/upload/', methods=['GET', 'POST'])
def upload_file():
    '''
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        upload_episode = request.form.get('episode')
        upload_series = request.form.get('series')

        if file.filename == '':
            return redirect(request.url)

        if file:
            if upload_series in os.listdir(os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'])):
                if len(os.listdir(seriesFolder + "\\" + upload_series)) <= int(upload_episode) or \
                        int(upload_episode) < 0:
                    if len(os.listdir(os.path.join(os.getcwd(),seriesFolder,upload_series))) == int(upload_episode):
                        os.remove(
                        os.path.join(
                            os.getcwd(),
                            app.config['UPLOAD_FOLDER'],
                            upload_series,
                            str(upload_episode) + ".mp4"
                            )
                        )
                    file.save(
                        os.path.join(
                            os.getcwd(),
                            app.config['UPLOAD_FOLDER'],
                            upload_series,
                            str(upload_episode) + ".mp4"
                        )
                    )
    '''
    return redirect(url_for("home"))

@app.route("/messages")
def message():
    global messages
    if len(messages)==0:
        return render_template("messages.html", messages=["No messages"])
    return render_template("messages.html", messages=messages)

# Anime getter section
# If you don't want to download anime than remove the code below


@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    return render_template(
        "search.html",
        results=results,
    )


@app.route("/search/<string:term>")
def search_results(term):
    names = []
    url_list = list(set(searchForAnime(term)))
    for i in url_list:
        names.append(i.split("/")[-1])
    return render_template("results.html", urlList=url_list, names=names)


@app.route("/update", methods=["GET", "POST"])
def update():
    if request.method == "POST":
        name = request.form["name"]
        url=titleUrls.query.filter_by(title=name).first()
        if url:
            downloading.append(url.url)

        return redirect(url_for("home"))
    else:
        new_name = ""
        for i in name.split("-"):
            new_name += i + " "

        results = searchForAnime(new_name)
        return render_template(
            "search.html",
            results=results,
            searchTerm=new_name
        )


@app.route("/download", methods=["GET", "POST"])
def download():
    global messages
    if request.method == "POST":
        url = request.form["url"]
        downloading.append(url)
        name = url.split("/")[-1]
        messages.append("Added " + name + " to downloading queue")
        return render_template("search.html", close=True)


@app.route("/series/live/<string:name>/<int:episode>")
def live_episode(name, episode):
    title_name=name

    url=titleUrls.query.filter_by(title=name).first()

    episode = int(episode)

    if url != None:
        url=url.url
        episode_list = getEpisodeBox(url)[::-1]
        if episode_list != "":
            return render_template(
                "liveEpisode.html",
                name=title_name,
                numOfEpisodes=len(episode_list),
                thEpisode=episode,
                filename=getDownloadUrl(episode_list[episode - 1])
            )
    return redirect(url_for("home"))


@app.route("/get/live/<string:name>/<int:episode>")
def get_live_episode(name, episode):

    url=titleUrls.query.filter_by(title=name).first()
    if url:
        url=url.url
    else:
        return redirect(url_for("home"))
    episode = int(episode)
    episode_list = getEpisodeBox(url)[::-1]

    return getDownloadUrl(episode_list[episode - 1])


@app.route("/watch/live/", methods=["POST", "GET"])
def watch_live():
    if request.method == "POST":
        anime_url = request.form["url"]
        name = request.form["name"]
        db.session.add(titleUrls(title=name,url=anime_url))
        db.session.commit()
        return redirect(url_for("live_episode", name=name, episode=1))
    else:
        return redirect(url_for("home"))

@app.route("/ongoing")
def ongoing():
    global ongoinglist
    titleDays={}
    if ongoinglist!=[]:
        for i in ongoinglist:
            t=titleTime.query.filter_by(title=i["title"]).first()
            if t:
                titleDays[i["title"]]=t.weekDayRelease
        return render_template("ongoing.html",ongoing=ongoinglist,titleDays=titleDays)
    else:
        return render_template("ongoing.html",ongoing=ongoinglist),404

@app.route("/new")
def new():
    global newList
    if newList!=[]:
        return render_template("ongoing.html",ongoing=newList)
    else:
        return render_template("ongoing.html",ongoing=newList),404



if __name__=="__main__":
	#db.create_all()
	ongoingT=ongoingThread()
	ongoingT.start()
	t = Thread()
	t.start()

	webbrowser.open("http://127.0.0.1:" + str(port))
	serve(app,host="0.0.0.0", port=port)

#	app.run(host="0.0.0.0", port=port, threaded=True,debug=1)
