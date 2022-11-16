from pathlib import Path
import pathlib
import subprocess as sp
import re


local_root = pathlib.PosixPath.home() / 'BioSci-McGrath'
cloud_root = pathlib.PosixPath('cichlidVideo:/BioSci-McGrath')


class SmartPath(pathlib.PosixPath):

    def __init__(self, path):
        path = pathlib.PosixPath(path)
        if path.is_relative_to(local_root):
            self.local_path = path
            self.rel_path = self.local_to_rel(path)
            self.cloud_path = self.local_to_cloud(path)
        elif path.is_relative_to(cloud_root):
            self.cloud_path = path
            self.rel_path = self.cloud_to_rel(path)
            self.local_path = self.cloud_to_local(path)
        else:
            self.rel_path = path
            self.cloud_path = cloud_root / path
            self.local_path = local_root / path
        super().__init__(self.local_path)
        self.name = self.local_path.name
        self.stem = self.local_path.stem
        self.suffix = self.local_path.suffix
        self.suffixes = self.local_path.suffixes

    @staticmethod
    def rel_to_cloud(rel_path):
        return cloud_root / pathlib.PosixPath(rel_path)

    @staticmethod
    def rel_to_local(rel_path):
        return cloud_root / pathlib.PosixPath(rel_path)

    @staticmethod
    def local_to_rel(local_path):
        return pathlib.PosixPath(local_path).relative_to(local_root)

    @staticmethod
    def cloud_to_rel(cloud_path):
        return pathlib.PosixPath(cloud_path).relative_to(cloud_root)

    @staticmethod
    def cloud_to_local(cloud_path):
        return local_root / pathlib.PosixPath(cloud_path).relative_to(cloud_root)

    @staticmethod
    def local_to_cloud(local_path):
        return cloud_root / pathlib.PosixPath(local_path).relative_to(local_root)

    def exists_local(self):
        return self.local_path.exists()

    def exists_cloud(self):
        return sp.run(['rclone', 'lsf', str(self.cloud_path)], capture_output=True, encoding='utf-8').stdout != ''

    def isfile(self):
        return self.local_path.is_file() if self.exists_local() else bool(self.suffix)

    def isdir(self):
        return self.local_path.is_dir() if self.exists_local() else not self.suffix

    def upload(self):
        dest = self.cloud_path if self.isdir() else self.cloud_path.parent
        sp.run(['rclone', 'copy', str(self.local_path), str(dest)], capture_output=True, encoding='utf-8')

    def download(self):
        self.mk_local()
        dest = self.local_path if self.isdir() else self.local_path.parent
        sp.run(['rclone', 'copy', str(self.cloud_path), str(dest)], capture_output=True, encoding='utf-8')

    def ls_local(self, pattern=None):
        children = [SmartPath(p) for p in self.local_path.iterdir()]
        if pattern:
            children = [c for c in children if re.fullmatch(pattern, c.name)]
        return children

    def ls_cloud(self, dirs_only=False, pattern=None):
        if not dirs_only:
            cmd = ['rclone', 'lsf', str(self.cloud_path)]
        else:
            cmd = ['rclone', 'lsf', '--dirs-only', str(self.cloud_path)]
        children = [c.strip('/') for c in sp.run(cmd, capture_output=True, encoding='utf-8').stdout.split()]
        children = [SmartPath(self.cloud_path / p) for p in children]
        if pattern:
            children = [c for c in children if re.fullmatch(pattern, c.name)]
        return children

    def mk_local(self, recursive=False):
        if not self.exists_local() and self.isdir():
            self.local_path.mkdir(parents=True)
            if recursive:
                for child in self.ls_cloud(dirs_only=True):
                    child.mk_local(recursive=True)

    def tar(self, ):
        pass


class FullMap(SmartPath):

    def __init__(self, dirs_only=True):
        super(FullMap, self).__init__('')
        for child_dir in self.ls_cloud(dirs_only=dirs_only):
            if hasattr(self, child_dir.name):
                print(f'WARNING: the directory {child_dir.cloud_path} has the same name as a protected member '
                      f'({child_dir.name}) of the SmartPath class. Please change the name of this directory')
            else:
                setattr(self, child_dir.name, child_dir)


def remove_empty_dirs(parent_dir, remove_parent_dir=False):
    parent_dir = Path(parent_dir)
    if not parent_dir.is_dir():
        return
    for child in parent_dir.iterdir():
        remove_empty_dirs(child, remove_parent_dir=True)
    children = list(parent_dir.iterdir())
    if not children and remove_parent_dir:
        parent_dir.rmdir()

