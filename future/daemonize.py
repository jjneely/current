Here's the daemonize function I use; I think Greg Ward originally
gave it to me.

    def daemonize (self):
        # Fork once
        if os.fork() != 0:
            os._exit(0)
        os.setsid()                     # Create new session
        if os.fork() != 0:      
            os._exit(0)         
        os.chdir("/")         
        os.umask(0)

        os.close(sys.__stdin__.fileno())
        os.close(sys.__stdout__.fileno())
        os.close(sys.__stderr__.fileno())
        
--amk


