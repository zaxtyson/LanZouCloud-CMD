import json
import os
import re
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


class LanZouCloudError(Exception):
    """蓝奏云异常基类"""

    def __init__(self, msg=''):
        self.msg = msg


class GetFileInfoError(LanZouCloudError):
    """获取文件信息失败引发的错误"""
    pass


class ParseError(LanZouCloudError):
    """解析直链时时引发的错误"""
    pass


class PasswdError(LanZouCloudError):
    """密码错误引发的异常"""
    pass


class UploadError(LanZouCloudError):
    """上传文件时引发的异常"""
    pass


class DownloadError(LanZouCloudError):
    """下载过程中引发的异常"""
    pass


class LanZouCloud(object):
    def __init__(self):
        self._file_id_length = 8  # 目前文件id长度
        self._seed_file_suffix = '.seed.txt'  # 种子文件后缀
        self._guise_suffix = '.dll'  # 不支持的文件伪装后缀
        self._session = requests.session()
        self.header_pc = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Referer': 'https://www.lanzous.com',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.header_phone = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Mobile Safari/537.36',
            'Referer': 'https://www.lanzous.com',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def login(self, username, passwd):
        """登录蓝奏云控制台"""
        login_data = {
            "action": "login",
            "task": "login",
            "ref": "https://up.woozooo.com/",
            "formhash": "0af1aa15",
            "username": str(username),
            "password": str(passwd),
        }

        html = self._session.post('https://pc.woozooo.com/account.php', data=login_data,
                                  headers=self.header_pc).text  # 登录
        if '登录成功' not in html:
            raise PasswdError("用户名或登录密码错误")

    def delete(self, id):
        """
        把网盘的文件(夹)放到回收站(不能包含子文件夹)
        :param id: 文件的id或者文件夹id
        :return: True or False
        """
        delete_file = {'task': 6, 'file_id': id}
        delete_folder = {'task': 3, 'folder_id': id}

        # 目前文件夹id为6位，文件id为8位
        if len(str(id)) >= self._file_id_length:
            post_data = delete_file
        else:
            post_data = delete_folder
        try:
            result = self._session.post('https://pc.woozooo.com/doupload.php', data=post_data,
                                        headers=self.header_pc).json()
        except Exception:
            return False

        if result["zt"] != 1:
            return False
        else:
            return True

    def recovery(self, id):
        """
        从回收站恢复文件
        :param id: 文件或文件夹id
        :return: True or False
        """
        post_data = {
            "action": "files",
            "formhash": "efdd6f6f",
            "fl_sel_ids[]": id,
            "task": "restore_recycle"
        }
        result = self._session.post('https://pc.woozooo.com/mydisk.php?item=recycle', data=post_data,
                                    headers=self.header_pc).text
        if '恢复成功' in result:
            return True
        else:
            return False

    def list_dir(self, folder_id=-1) -> dict:
        """
        获取文件列表
        :param folder_id: 文件夹id
        :return: 当前目录下的文件夹列表，文件列表，回溯路径列表
        """
        page = 1
        file_list = {}
        folder_id = int(folder_id)
        while True:
            post_data = dict(task=5, folder_id=folder_id, pg=page, headers=self.header_pc)  # 通过POST拿到分页的文件列表
            r = self._session.post('https://pc.woozooo.com/doupload.php', data=post_data).json()
            if r["info"] == 1:  # 该页有文件
                for file in r["text"]:
                    file_list[file["name_all"]] = file["id"]
            else:
                break
            page += 1
        # 文件夹的id直接从html中提取
        html = self._session.get(
            'https://pc.woozooo.com/mydisk.php?item=files&action=index&folder_id=' + str(folder_id),
            headers=self.header_pc).text
        folder_list = re.findall(r'&nbsp;(.+?)</a>&nbsp;.+folkey\((.+?)\)', html)
        folder_list = dict(folder_list)
        # 获取文件夹完整路径信息及其id
        path = re.findall(r'&raquo;&nbsp;.+folder_id=([0-9]+)">.+&nbsp;(.+?)</a>', html)
        path_list = {'根目录': '-1'}
        for i in path:
            path_list[i[1]] = i[0]
        # 获取当前文件夹名称
        if folder_id != -1:
            current_folder = re.findall(r'&raquo;&nbsp;.+&nbsp;(.+) <font', html)[0]
            path_list[current_folder] = folder_id
        # {'folder_list': {'子文件夹': 'id', ...}, 'file_list': {'文件': 'id', ...},
        #                                       'path_list': {'根目录': '-1', '父文件夹': 'id', ...}}
        return dict(folder_list=folder_list, file_list=file_list, path_list=path_list)

    def mkdir(self, parent_id, folder_name, folder_description=''):
        """
        再网盘上面新建文件夹
        :param parent_id: 父文件夹的id(默认-1，根目录)
        :param folder_name: 文件夹名
        :param folder_description: 文件夹描述
        :return: folder_id
        """
        folder_name = re.sub('[#\$%\^\*<>\+=`\'"/:;,\?]', '', folder_name)  # 去除非法字符
        post_data = {
            "task": 2,
            "parent_id": parent_id or -1,
            "folder_name": folder_name,
            "folder_description": folder_description
        }
        result = self._session.post('https://pc.woozooo.com/doupload.php', data=post_data,
                                    headers=self.header_pc, ).json()
        if result["zt"] != 1:
            return -1
        else:
            html = self._session.get(
                'https://pc.woozooo.com/mydisk.php?item=files&action=index&folder_id=' + str(parent_id),
                headers=self.header_pc, timeout=1000).text
            folder_name = folder_name.replace('.', '\\.')  # 防止正则匹配到错误字符
            folder_name = folder_name.replace('&', '&amp;')  # &符号到html里面转变为&amp;
            try:
                folder_id = re.findall(r'folder_id=([0-9]+)\".+&nbsp;{}</a>'.format(folder_name), html)[0]
            except IndexError:
                return -1
            return int(folder_id)

    def get_file_info(self, share_url) -> dict:
        """
        获取文件名，大小，上传时间
        :param short_url:文件分享链接最后一段
        :return:包含文件名，文件大小，上传时间的dict
        """
        response = requests.get(share_url, headers=self.header_phone)
        try:
            file_name = re.findall(r"<title>(.+) -", response.text)[0]  # 提取文件名，网页标题有
            file_size = re.findall(r"<span class=\".+\">\( (.+) \)</span>", response.text)[0]  # 提取文件大小
            upload_time = re.findall(r'</span>(.*?)\s*<span class="mt2">', response.text)[1]  # 提取文件上传时间
            file_id = re.findall(r'href="/home/\?f=(\d{5,})&report', response.text)[0]  # 提取文件id
            return {'file_name': file_name, 'file_size': file_size, 'upload_time': upload_time,
                    'file_id': file_id, 'share_url': share_url}
        except Exception as e:
            raise GetFileInfoError("获取文件信息错误: {}".format(e))

    def parse(self, url, pwd='') -> dict:
        """
        解析蓝奏云链接返回文件信息和直链
        :param url:蓝奏云分享链接
        :param pwd:文件密码(默认为为空)
        :return dict:文件名，大小，上传时间，直链
        """
        # 链接合法性检查，链接错误则引发UrlInvalidError异常
        if not re.match('https://www\.lanzous\.com/[0-9a-z]{7,}.*', url):
            raise LanZouCloudError("该分享链接有误:{}".format(url))

        short_url = url.split('/')[3]  # 文件ID就是链接最后一段

        if pwd:  # 如果存在访问密码，需要先拿到认证所需的参数

            try:
                response = requests.get('https://www.lanzous.com/tp/' + short_url, headers=self.header_phone)
                para = re.findall(r"data : \'(.*)\'\+pwd", response.text)[0]
                # 参数para是一个整个字符串，形如：action=downprocess&sign=XXXXXXXX&p=
                data = {}
                for item in para.split('&'):  # 先把para先拼凑成字典，方便后面发送POST请求
                    tmp = item.split('=')
                    data[tmp[0]] = tmp[1]
                data['p'] = pwd  # 参数中p设置为访问密码
            except Exception:
                raise ParseError("提取直链参数时错误")

            try:
                # POST带参数请求 https://www.lanzous.com/ajaxm,php 来获取伪链
                resp = requests.post('https://www.lanzous.com/ajaxm.php', headers=self.header_phone, data=data)
                result = json.loads(resp.text)
                temp_url = result['dom'] + '/file/' + result['url']  # 构造文件临时链接，后面需要它来找到直链
                # GET请求临时链接，返回的response中Location字段暴露了文件的直链
                response = requests.get(url=temp_url, headers=self.header_phone, data=data, allow_redirects=False)
                file_info = self.get_file_info(url)  # 获取文件大小等信息
                return {**file_info, 'direct_url': response.headers['Location']}
            except Exception:
                raise PasswdError("文件访问密码错误: {}".format(pwd))

        else:  # 不存在密码时
            # 直接GET请求 https://www.lanzous.com/tp/ID 提取直连，此时需要UA设置为手机，PC版无法提取此链接
            # 手机端返回的html中有一段js暴露了服务器IP和相关参数
            # <script type="text/javascript">
            #     var urlpt = 'http://120.55.32.134/file/';   # 这个是IP
            #     (function(document) {
            #         var submit = document.getElementById('submit');
            #         //var urlpt = 'http://120.55.32.134/file/';
            #         submit.onfocus = submit.onmousedown = function() {
            #         submit.href = urlpt + "XXXXXXXXXXX"  # 这个是参数
            #     }})(document);
            # </script>
            try:
                response = requests.get('https://www.lanzous.com/tp/' + short_url, headers=self.header_phone)
                host = re.findall(r"var urlpt = \'(.+)\'", response.text)[0]
                href = re.findall(r"submit.href = urlpt \+ \"(.+)\"", response.text)[0]

                temp_url = host + href  # 构造临时链接，GET请求返回的response里面暴露直链
                response = requests.get(temp_url, headers=self.header_phone, allow_redirects=False)
                file_info = self.get_file_info(url)
                return {**file_info, 'direct_url': response.headers['Location']}
            except Exception:
                raise ParseError("缺少访问密码或文件不存在")

    def set_passwd(self, id, passwd=-1):
        """
        设置网盘文件的访问密码
        :param id: 蓝奏云文件的id号
        :param passwd: 要设置的访问密码,-1表示关闭密码
        :return: True or false
        """
        if passwd == -1:  # -1则关闭密码
            passwd_status = 0
        else:
            passwd_status = 1

        # 目前文件夹id为位，文件id为8位
        if len(str(id)) >= self._file_id_length:
            post_data = {
                "task": 23,
                "file_id": id,
                "shows": passwd_status,
                "shownames": passwd
            }
        else:
            post_data = {
                "task": 16,
                "folder_id": id,
                "shows": passwd_status,
                "shownames": passwd
            }

        try:
            result = self._session.post('https://pc.woozooo.com/doupload.php', data=post_data,
                                        headers=self.header_pc).json()
        except Exception:
            return False
        # 返回结果 {'zt': 1, 'info': '设置成功', 'text': 1}
        # zt=1表示成功，但是顺便填一个不存在的file_id也不会出现错误提示，蓝奏云的bug
        if result['zt'] != 1:
            return False
        else:
            return True

    def get_share_url(self, id):
        """
        通过id获取分享链接
        :param file_id: 文件id
        :return: 分享链接
        """
        if len(str(id)) >= self._file_id_length:  # 返回文件的分享链接
            post_data = {
                "task": 22,
                "file_id": id
            }
            try:
                result = self._session.post('https://pc.woozooo.com/doupload.php', data=post_data,
                                            headers=self.header_pc).json()
            except Exception:
                return ''

            if result['zt'] == 1:
                return 'https://www.lanzous.com/' + result['info']['f_id']
            else:
                return ''
        else:  # 返回文件夹分享链接
            return 'https://www.lanzous.com/b{}/'.format(id)

    def upload(self, file_path, folder_id=-1) -> dict:
        """
        上传文件到蓝奏云上指定的文件夹(默认根目录)
        :param file_path: 本地文件地址
        :param folder_id: 蓝奏云目标文件夹的ID
        :return: 包含文件名、文件ID、分享链接的dict
        """
        file_name = os.path.basename(file_path)  # 从文件路径截取文件名
        suffix = file_name.split(".")[-1]
        vaild_suffix_list = ['doc', 'docx', 'zip', 'rar', 'apk', 'ipa', 'txt', 'exe', '7z', 'e', 'z', 'ct',
                             'ke', 'cetrainer', 'db', 'tar', 'pdf', 'w3x', 'epub', 'mobi', 'azw', 'azw3',
                             'osk', 'osz', 'xpa', 'cpk', 'lua', 'jar', 'dmg', 'ppt', 'pptx', 'xls', 'xlsx',
                             'mp3', 'ipa', 'iso', 'img', 'gho', 'ttf', 'ttc', 'txf', 'dwg', 'bat', 'dll']
        if suffix not in vaild_suffix_list:
            # 不支持的文件修改后缀蒙混过关
            file_name = file_name + self._guise_suffix

        post_data = {
            "task": "1",
            "folder_id": str(folder_id),
            "id": "WU_FILE_0",
            "name": file_name,
            "type": "application/octet-stream",
            "upload_file": (file_name, open(file_path, 'rb'), 'application/octet-stream')
        }
        post_data = MultipartEncoder(post_data)
        upfile_header = self.header_pc.copy()  # 天坑！！复制不能直接赋值，结果导致全局headers异常,这里浅拷贝即可
        upfile_header['Content-Type'] = post_data.content_type
        result = self._session.post('http://pc.woozooo.com/fileup.php', data=post_data, headers=upfile_header).json()
        # 处理上传返回的结果
        if result["zt"] == 0:
            raise UploadError('上传文件"{}"时发生错误: {}'.format(file_path, result["info"]))
        file_id = result["text"][0]["id"]
        short_url = result["text"][0]["f_id"]
        file_name = result["text"][0]["name_all"]
        share_url = 'https://www.lanzous.com/' + short_url
        return {'file_name': file_name, 'file_id': file_id, 'share_url': share_url}

    def _split_file(self, file_path, block_size):
        """
        拆分大文件为若干个小文件
        :param file_path: 文件路径
        :param block_size: 单个小文件的大小(字节)
        :return: 保存拆分文件的文件夹的完整路径 或者 原文件路径(不超过block_size时)
        """
        file_size = os.path.getsize(file_path)  # 文件字节数
        real_path, file_name = os.path.split(file_path)  # 除去文件名以外的path，文件名
        suffix = file_name.split('.')[-1]  # 文件后缀名
        if file_size < block_size:
            return file_path
        else:
            fp = open(file_path, 'rb')
            count = file_size // block_size + 1
            temp_dir = real_path + os.sep + file_name + '_split'
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)

            for i in range(1, count + 1):
                name = temp_dir + os.sep + file_name.replace('.' + str(suffix), '[{}].{}'.format(i, suffix))
                f = open(name, 'wb')
                f.write(fp.read(block_size))
            fp.close()
            return temp_dir

    def _merge_file(self, split_dir):
        """
        把若干个小文件合并为一个文件
        :param split_dir: 存放被拆分文件的文件夹完整路径
        :return:
        """
        # split_dir以_split结尾，删除即得到正式保存文件的路径
        file_path = split_dir.replace('_split', '')  # 正式文件的完整路径
        real_path, file_name = os.path.split(file_path)  # 除去文件名以外的path，文件名
        fp = open(file_path, 'ab+')
        for file in sorted(os.listdir(split_dir)):
            f = open(split_dir + os.sep + file, 'rb')
            fp.write(f.read())
            f.close()
        fp.close()
        from shutil import rmtree
        rmtree(split_dir)

    def upload2(self, file_path, folder_id=-1) -> dict:
        """
        强化版upload，大文件自动拆分上传
        :param file_path: 本地文件完整路径
        :param folder_id: 蓝奏云目标文件夹的ID
        :return: dict 单个文件的信息(小文件)，或者种子文件的信息(大文件)
        """
        max_size = 104857600  # 蓝奏云100MB限制
        temp_dir = self._split_file(file_path, max_size)
        if os.path.isfile(temp_dir):
            return self.upload(temp_dir, folder_id)
        elif os.path.isdir(temp_dir):
            result_list = []
            temp_folder_id = self.mkdir(folder_id, os.path.basename(file_path), '分段文件，请勿直接下载')
            for file in sorted(os.listdir(temp_dir)):
                up_file = temp_dir + os.sep + file
                r = self.upload(up_file, temp_folder_id)
                result_list.append(r)
            from shutil import rmtree
            rmtree(temp_dir)
            # 把所有分段文件的信息写入txt文本，然后上传，之后返回的是这个txt的信息
            # 通过下载这个txt文件（相当于一个种子文件），可以得到所有文件的信息，然后分别下载再合并，得到完整文件
            save_name = os.path.basename(temp_dir).replace('_split', '.seed.txt')
            f = open(save_name, 'w')
            json.dump(result_list, f, ensure_ascii=False, indent=4)
            f.close()
            result = self.upload(save_name, folder_id)
            os.remove(save_name)
            return result

    def clean_recycle(self):
        """清空回收站"""
        post_data = dict(action='delete_all', task='delete_all', formhash='efdd6f6f')
        result = self._session.post('https://pc.woozooo.com/mydisk.php?item=recycle', headers=self.header_pc,
                                    data=post_data)
        if '清空回收站成功' in result.text:
            return True
        else:
            return False

    def download(self, share_url, save_path='.', pwd=''):
        """
        下载文件到指定路径
        :param share_url: 蓝奏云分享链接
        :param pwd: 访问密码(默认空)
        :param save_path: 本地文件保存路径(默认当前目录)
        :return: None
        """
        info = self.parse(share_url, pwd)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        try:
            if info["file_name"].endswith(self._seed_file_suffix):  # 如果是种子文件
                all_file_info = json.loads(requests.get(info["direct_url"]).text, encoding='utf-8')
                save_path = save_path + os.sep + info["file_name"].replace(self._seed_file_suffix, '')
                for file_info in all_file_info:
                    direct_url = self.parse(file_info['share_url'])["direct_url"]
                    part_file = requests.get(direct_url).content
                    f = open(save_path, 'ab')
                    f.write(part_file)
                    f.close()
            else:  # 如果是普通文件
                save_name = info["file_name"].replace(self._guise_suffix, '')  # 去除伪装后缀名
                f = open(save_path + os.sep + save_name, 'wb')
                data = requests.get(info["direct_url"]).content
                f.write(data)
                f.close()
        except Exception:
            raise DownloadError("下载时发生错误")
