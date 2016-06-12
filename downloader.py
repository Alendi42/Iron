
import os.path
from urllib.request import urlretrieve
from datetime import datetime
import shutil

temp_dir = ".iron/"
def download(url):
    print("downloading from %s" % url)
    ext = url.split('.')[-1]
    name = datetime.now().strftime('%Y%m%d-%H%M%S%f') + '.' + ext
    target_location = os.path.join(temp_dir,name)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    local_filename, headers = urlretrieve(url, target_location)
    return os.path.basename(local_filename)

def clean():
    """
    delete all files under temp directory
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    
    print("downloading with urllib" )
    url = 'http://tu.rrsub.com/ftp/2016/0427/6aab634bbf78e5838b29c65baea720cb.zip'  
    download(url)


