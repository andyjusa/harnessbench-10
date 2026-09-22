def base(url):
    return url.rstrip()

def jobs(url):
    return base(url) + "/jobs"

def runs(url):
    return base(url) + "/runs"
