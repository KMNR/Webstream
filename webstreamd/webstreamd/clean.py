import subprocess
import settings

def clean():
    def do_directory(p):
        contents = os.listdir(p)
        for f in contents:
            if os.path.isfile(os.path.join(p,f)):
                do_file(p,f)
            elif os.path.isdir(os.path.join(p,f)):
                do_directory(os.path.join(p,f))
        if len(contents) == 0:
            subprocess.Popen(['rm','-r',p]).wait()
    def do_file(p,f):
        l = f.split('-')
        if len(l) >= 3:
            d = datetime(int(l[2]),int(l[0]),int(l[1]))
            now = datetime.today()
            if now-d > timedelta(days=120):
                util.lnp("Removing {}/{}".fomat(p,f))
                subprocess.Popen(['rm',f],cwd=p).wait()
    do_directory(settings.RECORDER_FOLDER)

if __name__ == "__main__":
    clean()        
