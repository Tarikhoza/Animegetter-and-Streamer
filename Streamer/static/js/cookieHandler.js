function getWatchingCookie() {
  var watchingCookie = document.cookie.split('; ').find(row => row.startsWith('watching')).split('=')[1];
  return watchingCookie.replaceAll("'", "");
}
function getWatchingTitles() {
  var watchingCookie = getWatchingCookie();
  var titles = watchingCookie.split("|");
  titles.pop();
  return titles;
}

function addWatchingTitleToCookie(name, episode) {
  var watchingCookie = getWatchingCookie().replaceAll("'", "");
  var cookie = watchingCookie + name + ">" + episode + "|";
  var date = new Date();
  var days = 30;
  date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `watching='${cookie}';path=/;expires=${date.toUTCString()}`;
}




function addWatchingTitle(titleName, titleEpisode) {

  var mainCard=document.createElement("div")
  var imgCard=document.createElement("img")
  var bodyCard=document.createElement("div")
  var titleCard=document.createElement("h5")
  var buttonCard=document.createElement("a")
  var close=document.createElement("button")
  var buttonCon=document.createElement("div")

  var url="/series/" + titleName.toLowerCase() + "/" + titleEpisode

  close.className="close mb-2"
  close.innerText="x"
  close.style="z-index:100"
  close.title=titleName
  close.addEventListener("click",function(){eraseTitleByTitleName(this.title)},false );

  buttonCon.className="d-flex flex-row-reverse"
  buttonCon.appendChild(close)

  mainCard.className="watchingTitle card bg-dark col-auto"
  mainCard.style="width: 15rem; padding:10px; margin:10px;margin-right:20px"

  imgCard.className="card-img-top";
  imgCard.src="/static/thumbnails/"+titleName+".thumbnail";
  imgCard.onerror="this.onerror=null;this.src='/static/thumbnails/alt.thumbnail';"

  titleCard.className="card-title text-light text-nowrap text-truncate "
  titleCard.innerText=titleName.charAt(0).toUpperCase() + titleName.slice(1).replaceAll("-"," ")

  buttonCard.innerText="Watch episode "+titleEpisode
  buttonCard.className="btn btn-success text-nowrap stretched-link"

  buttonCard.href=url

  bodyCard.className="card-body"

  mainCard.appendChild(buttonCon)
  mainCard.appendChild(imgCard)

  bodyCard.appendChild(titleCard)

  mainCard.appendChild(bodyCard)
  mainCard.appendChild(buttonCard)

  document.getElementById("watchingList").appendChild(mainCard);

}

function setWatchingTitles() {
  try { getWatchingCookie() }
  catch (error) { document.cookie = "watching='';path=/" }

  watchingList = document.getElementById("watchingList");
  nextEpisodesBar=document.getElementById("next-episodes")
  watchingTitles = getWatchingTitles();

  if (watchingTitles.length!=0){
    for (var i in watchingTitles) {
      title = watchingTitles[i];
      var info = title.split(">");
      addWatchingTitle(info[0], info[1])
    }
  }
  else{
    nextEpisodesBar.style.display="none"
  }
}
function eraseTitle(nth) {
  watchingList = document.getElementById("watchingList");
  watchingTitles = getWatchingTitles();
  watchingTitles.splice(nth,1);
  document.cookie = "watching='';path=/";
  for (var i in watchingTitles) {
    var title = watchingTitles[i].split(">");
    addWatchingTitleToCookie(title[0], title[1]);
  }
}

function eraseTitleByTitleName(titleName) {
  try{
    nextEpisodesBar=document.getElementById("next-episodes")
    watchingList = document.getElementById("watchingList");
    watchingElements = watchingList.getElementsByClassName("watchingTitle")
    index=1
  }
  catch(err){index=0}
  watchingTitles = getWatchingTitles();
  nth=-1
  for(var i in watchingTitles){
    if(watchingTitles[i].split(">")[0]==titleName){
        nth=i
        break
      }
  }

  if(nth!=-1){
    if(index){
      watchingElements[nth].remove()

    }
    eraseTitle(nth)
    if (getWatchingTitles().length==0){
      nextEpisodesBar.style.display="none";
    }
  }
}

function updateWatchingCookie() {
  var watchingTitles = getWatchingTitles();


  if (numOfEpisodes >= thEpisode + 1){
    eraseTitleByTitleName(String(videoFolder).replaceAll("/",""));
    addWatchingTitleToCookie(String(videoFolder).replaceAll("/", ""), thEpisode + 1);
  }
  else
    eraseTitleByTitleName(String(videoFolder).replaceAll("/",""));
}

function addToWatchList(videoFolder){
  var watchingTitles = getWatchingTitles();
  var inside=0;
  try{
    nextEpisodesBar=document.getElementById("next-episodes")
    watchingList = document.getElementById("watchingList");
    watchingElements = watchingList.getElementsByClassName("watchingTitle")
    index=1
  }
  catch(err){index=0}

  for(var i=0;i<watchingTitles.length;i++){
    if(videoFolder==watchingTitles[i].split(">")[0]){
      inside=1
      break
    }
  }

  if (!inside){
    addWatchingTitleToCookie(String(videoFolder).replaceAll("/", ""), 1);
    addWatchingTitle(String(videoFolder).replaceAll("/", ""), 1);
    nextEpisodesBar.style.display="block"

  }


}
