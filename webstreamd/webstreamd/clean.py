import subprocess
import settings

settings = Settings()

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
    do_directory(settings.RECORDINGDIR)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        conf_file = sys.argv[1]
    elif len(sys.argv) == 1:
        print "Using default config {}".format(Settings.DEFAULTCONFIG)
        conf_file = Settings.DEFAULTCONFIG
    else:
        print "Format: {} [CONFIG_FILE]".format(sys.argv[0])
        exit(1)
    settings.load_config(conf_file)
    clean()        
