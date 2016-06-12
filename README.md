# Iron
Generate margent link and download scription files from zimuzu.tv website automically.
本工具用于自动检索特定字幕组网站 zimuzu.tv上新发布的字幕压缩包，自动下载解压，并从字幕组网站中抓取字幕文件所对应的电驴或是磁力链接

依赖第三方组件：
beautifulsoup4
rarfile
requests

参数配置
相关参数可在leecher.config中配置：

#你在zimuzu网站的用户名与密码
[user]
id = <id>
password = <password>

#你所订阅的剧集名称，字幕语言以及用于放置取得字幕的目录
[resource]
name = 权力的游戏,绿箭侠
sub_lang = 英文,简体&英文
output_dir = D:\git-workspace\Iron\output\

#你的邮箱信息，用于向订阅邮件发出提醒文件
[email]
subscriber = lala@163.com, vava@163.com
host = smtp.163.com
user = yenancs
postfix = 163.com
password = 8Arrowen

#设定字幕查询起始时间，工具只会获取晚于这个时间所上传的字幕。
#每执行一次工具，这里的时间配置都会被自动更新。
[history]
since = 2016-06-12 15:48

执行：
直接执行 leecher.py
