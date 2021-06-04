import os

def check(seriesFolder,seriesName,episode):
	if((os.name == 'nt' and "ffmpeg.exe" in os.listdir()) or (os.name !="nt" and "ffmpeg" in os.listdir())):
		commandTemplate="{} -v error -i {} -map 0:1 -f null - 2>integrity.temp"
		windowsCommand=commandTemplate.format("ffmpeg.exe",os.path.join(seriesFolder,seriesName,episode))
		linuxCommand=commandTemplate.format("./ffmpeg",os.path.join(seriesFolder,seriesName,episode))
		command=windowsCommand+" || "+linuxCommand
		os.system(command)
		with open("integrity.temp","r") as file:
		    out=file.readlines()
		    if len(out)>0:

		        print(seriesName+"-"+episode+" -- file damaged")
		        with open("integrityLogs"+"\\"+seriesName+"-"+episode+".log","w") as log:
		            for i in out:
		                log.write(i)
		        return 1
		print(seriesName+"-"+episode+" OK")

	else:
		print("Download FFMPEG to add integrity checking to the app")
		print("Just add the executable to the root of the project")
	return 0
def checkAll(seriesFolder):
    report={
        "errors":[],
        "working":[]
    }

    for series in os.listdir(seriesFolder):
        for episode in os.listdir(seriesFolder+"\\"+series):
            r={
                "episode":episode,
                "series":series
            }
            if(check(seriesFolder,series,episode)):
                report["errors"].append(r)
            else:
                report["working"].append(r)
    return report
