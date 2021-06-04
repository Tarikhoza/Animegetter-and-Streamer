var jump={
    inter:null,
    stop:function(){
      clearInterval(this.inter);
    },
    start:function(jump,jumpTime){
      this.inter=setInterval(function(){
          var time=document.getElementById("video_html5_api").currentTime;
          if(time>jumpTime && time<(jumpTime+jump) ){
              document.getElementById("video_html5_api").currentTime=jumpTime+jump;
            }
          },1
      );
    }
}
