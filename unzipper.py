import zipfile
import rarfile
import os
import os.path
import re

temp_dir = ".iron/"

def extract(arch_name, output_loc, lang_list = None):

    result = set()

    if not os.path.exists(output_loc):
        os.makedirs(output_loc)

    def filter(filename):
        if not lang_list: #no filter for subtitle language
            return True
        else:
            target = '|'.join(['\.' + lang for lang in lang_list])
            pattern = re.compile(target)
            return pattern.search(filename)
    
    path = os.path.join(temp_dir, arch_name)    
    z = None
    if path.endswith('.zip'):
        z = zipfile.ZipFile(path,'r')
    #elif path.endswith('.rar'):
    #    z = rarfile.RarFile(path,'r')

    if z:
        for info in z.infolist():
            name = info.filename
            if name.endswith('.srt') or name.endswith('.ass'):
                #zipfile use cp437 to decode file name, so we have to encode it as cp437 first and then decode it with GBK
                #otherwise, Chinese will be gibberish

                try:
                    newName = name.encode('cp437').decode('gbk')
                except UnicodeEncodeError as e:
                    newName = name
                newName = newName.split('/').pop()

                if filter(newName):
                    z.extract(info,temp_dir)

                    resource_name = '.'.join(newName.split('.')[:-2])

                    print(newName)
                    result.add(resource_name)
                    
                    old = os.path.join(temp_dir,name)
                    new = os.path.join(output_loc,newName)
                    if old != new and os.path.exists(new):
                        os.remove(new)
                    os.rename(old,new)
            elif name.endswith('.zip') or name.endswith('.rar'):
                print("find child zip/rar file")
                z.extract(info,temp_dir)
                result = result.union(extract(name, output_loc))
    print(result)           
    return result

if __name__ == '__main__':
    

    sub_dir = "D:/git-workspace/Iron/sub/"
    zip1 = "6.zip"

    output_dir = "D:/git-workspace/Iron/sub/result/"

    extract(sub_dir+zip1, output_dir,['简体&英文','英文'])
            


