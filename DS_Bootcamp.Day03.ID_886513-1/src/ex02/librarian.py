import subprocess
import sys
import os
import shutil


def check_virtual_env():
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        raise EnvironmentError("Скрипт должен быть запущен в виртуальном окружении.")


def install_libraries():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4', 'pytest'])


def list_installed_libraries():
    installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8')
    print(installed_packages)

    with open('requirements.txt', 'w') as f:
        f.write(installed_packages)


def archive_virtual_env(env_path, output_dir):
    archive_name = os.path.join(output_dir, 'rosiesoi')
    shutil.make_archive(archive_name, 'gztar', env_path)


if __name__ == "__main__":
    try:
        check_virtual_env()
        install_libraries()
        list_installed_libraries()
        archive_virtual_env('./../../rosiesoi', './')
    except EnvironmentError as e:
        print(e)
