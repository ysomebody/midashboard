from ftplib import FTP
from dateutil import parser
from packaging import version

class FileInfo:

    def __init__(self, file_info_text):
        ''' the format returned by the ftp dir command
            -r--r--r-- 1 ftp ftp            538 Jul 26  2016 info.txt
            drwxr-xr-x 1 ftp ftp              0 Sep 30 17:35 Package Manager

        '''
        tokens = file_info_text.split(maxsplit=9)
        self.name = tokens[8]
        self.time = parser.parse(tokens[5] + " " + tokens[6] + " " + tokens[7])
        self.is_dir = (tokens[0][0] == 'd')


class FtpFolder:

    def __init__(self, ftp, path):
        lines = []
        ftp.dir(path, lines.append)
        self.files_info = [FileInfo(line) for line in lines]

    def get_sub_folder_names(self):
        return [file_info.name for file_info in self.files_info if file_info.is_dir]

    def get_latest_folder_info(self):
        latest_time = None
        latest_folder_info = None

        for file_info in self.files_info:
            if not file_info.is_dir:
                continue
            time = file_info.time
            if (latest_time is None) or (time > latest_time):
                latest_folder_info = file_info

        return latest_folder_info


def get_latest_subfolder(ftp, relative_path):
    subfolders = FtpFolder(ftp, relative_path).get_sub_folder_names()
    latest_version = None
    latest_folder = None
    for folder in subfolders:
        try:
            ver = version.parse(folder)
            if ver.release[0] == 255:
                continue
            if (latest_version is None) or (ver > latest_version):
                latest_version = ver
                latest_folder = folder
        except version.InvalidVersion:
            pass
    return latest_folder


def get_master_relative_path(ftp, relative_path):
    folder_name = relative_path.rsplit('/', 1)[-1]
    try:
        v = version.Version(folder_name)
        return relative_path
    except version.InvalidVersion:
        master_folder = get_latest_subfolder(ftp, relative_path)
        return '/'.join([relative_path, master_folder])


def relative_path_to_argo_path(relative_path):
    return '\\\\argo\\' + relative_path.replace('/', '\\')


def argo_path_to_relative_path(argo_path):
    return argo_path.lstrip('\\\\argo\\').rstrip('\\').replace('\\', '/')


def get_latest_master_installer_from_argoftp(ftp, relative_path):
    master_relative_path = get_master_relative_path(ftp, relative_path)
    latest_folder_info = FtpFolder(ftp, master_relative_path).get_latest_folder_info()
    latset_folder_relative_path = '/'.join([master_relative_path, latest_folder_info.name])
    return {
        "installer_timestamp": latest_folder_info.time.strftime("%Y-%m-%d %H:%M:%S"),
        "installer_details"  :
            {
                "version" : latest_folder_info.name,
                "export" : relative_path_to_argo_path(latset_folder_relative_path)
            }

    }


def get_argo_ftp():
    return FTP("argoftp.natinst.com")


def get_installer_info(argo_path):
    with get_argo_ftp() as ftp:
        ftp.login()
        relative_path = argo_path_to_relative_path(argo_path)
        return get_latest_master_installer_from_argoftp(ftp, relative_path)


if __name__ == '__main__':

        installer_path = "\\\\argo\\ni\\nipkg\\feeds\\ni-d\\ni-digital"

        installer = get_installer_info(installer_path)
        print(installer)
