import os
import platform
import shutil
import time
import json
import tempfile


ARCHIVE_FOLDER = 'Archive'
ARCHIVE_THRESHOLD = 30 # days
ERROR_LOG_FILE = os.path.join(tempfile.gettempdir(), 'autoarchive_error.log')

def get_path():
    return os.path.dirname(__file__)

def get_path_osx():
    path = os.getcwd()
    while not path.endswith('.app'):
        path = os.path.dirname(path)
        if path == '/':
            return get_path()
    return path

def err_log(e):
    # save error to debug log
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' ' + 'Error: {}\n'.format(e))

def revert(run_log, target_dir, archive_folder=ARCHIVE_FOLDER):
    try:
        with open(run_log, 'r') as f:
            log = json.load(f)
    except Exception as e:
        err_log(e)
        return
    
    for item in log['moved_files']:
        try:
            src = os.path.join(target_dir, archive_folder, item['dest'])
            dest = os.path.join(target_dir, item['src'])
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
        except Exception as e:
            err_log(e)
            continue


if __name__ == '__main__':
    # get target directory and self name
    if platform.system() == 'Darwin':
        target_dir = get_path_osx()
        if target_dir.endswith('.app'):
            self_name = os.path.basename(target_dir)
            target_dir = os.path.dirname(target_dir)
        else:
            self_name = os.path.basename(__file__)
    else:
        target_dir = get_path()
        self_name = os.path.basename(target_dir)

    # get config from config file
    config = {
        'archive_folder': ARCHIVE_FOLDER,
        'archive_threshold': ARCHIVE_THRESHOLD,
        'ignore': ['archive_config.json'],
        'debug': False
    }
    config_file = os.path.join(target_dir, 'archive_config.json')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                load_config = json.load(f)
                config = {**config, **load_config}
        else:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
    except Exception as e:
        err_log(e)
        exit()

    archive_folder = config['archive_folder']
    archive_threshold = config['archive_threshold']
    debug_mode = config['debug']
    ignore_list = config['ignore']

    # if in debug mode, set archive folder to Archive_Debug
    # and archive threshold to 0 day
    if debug_mode:
        archive_folder = 'Archive_Debug'
        archive_threshold = 0
        # also, save target_dir and self_name to file
        # and config
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            dbgmsg_prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' ' + 'Debug: '
            f.write('\n')
            f.write(dbgmsg_prefix + 'target_dir: {}\n'.format(target_dir))
            f.write(dbgmsg_prefix + 'self_name: {}\n'.format(self_name))
            f.write(dbgmsg_prefix + 'config: {}\n'.format(config))
            f.write('\n')
    
    # check if revert mode
    if 'revert' in config:
        if os.path.exists(config['revert']):
            revert(config['revert'], target_dir, archive_folder)
            # move the json to reverted.json
            file_name, file_ext = os.path.splitext(config['revert'])
            shutil.move(config['revert'], file_name + '_reverted' + file_ext)
            exit()

    # check if archive folder exists
    archive_dir = os.path.join(target_dir, archive_folder)
    if not os.path.exists(archive_dir):
        try:
            os.mkdir(archive_dir)
        except Exception as e:
            err_log(e)
            exit()


    # check all files under target directory 
    # except self and archive_folder
    # if the Last Modified Time is older than archive_threshold days
    # move it to yyyy-mm folder under archive_folder
    moved_files = []
    start_time = time.time()
    for file in os.listdir(target_dir):
        ignore_list.append(self_name)
        ignore_list.append(archive_folder)
        if file in ignore_list:
            continue
        file_path = os.path.join(target_dir, file)
        file_modified_time = os.path.getmtime(file_path)
        if time.time() - file_modified_time > archive_threshold * 24 * 60 * 60:
            success = True
            err = None
            try:
                # move file to archive folder
                file_archive_dir_relative = time.strftime('%Y-%m', time.localtime(file_modified_time))
                file_archive_dir = os.path.join(archive_dir, file_archive_dir_relative)
                if not os.path.exists(file_archive_dir):
                    try:
                        os.mkdir(file_archive_dir)
                    except Exception as e:
                        err_log(e)
                # check if file with same name exists in archive folder
                # if so, append a number to the file name, but keep extension
                file_archive_path = os.path.join(file_archive_dir, file)
                file_relative = file
                if os.path.exists(file_archive_path):
                    file_name, file_ext = os.path.splitext(file)
                    i = 1
                    while True:
                        file_relative = file_name + ' (' + str(i) + ')' + file_ext
                        file_archive_path = os.path.join(file_archive_dir, file_relative)
                        if not os.path.exists(file_archive_path):
                            break
                        i += 1
                shutil.move(file_path, file_archive_path)
                # success
                moved_files.append({
                    'src': file,
                    'dest': os.path.join(file_archive_dir_relative, file_relative)
                })
            except Exception as e:
                # save error to debug log
                success = False
                err = e
                err_log(e)
            # log to archive_folder\LOG\yyyy-mm.log
            errmsg = 'Success'
            if not success:
                errmsg = 'Error: {}'.format(err).replace('\n', ' ')
            log_dir = os.path.join(archive_dir, 'LOG')
            if not os.path.exists(log_dir):
                try:
                    os.mkdir(log_dir)
                except Exception as e:
                    err_log(e)
            log_file = os.path.join(log_dir, time.strftime('%Y-%m.log', time.localtime(file_modified_time)))
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' ' + file + ' ' + errmsg + '\n')
            except Exception as e:
                err_log(e)

    end_time = time.time()
    # log to archive_folder\LOG\RUN\yyyy-mm-dd-HH-MM-SS.json
    run_log_dir = os.path.join(archive_dir, 'LOG', 'RUN')
    if not os.path.exists(run_log_dir):
        try:
            os.makedirs(run_log_dir)
        except Exception as e:
            err_log(e)
    run_log_file = os.path.join(run_log_dir, time.strftime('%Y-%m-%d-%H-%M-%S.json', time.localtime()))
    try:
        with open(run_log_file, 'w') as f:
            json.dump({
                'start_time': start_time,
                'end_time': end_time,
                'moved_files': moved_files
            }, f, indent=4)
    except Exception as e: 
        err_log(e)
