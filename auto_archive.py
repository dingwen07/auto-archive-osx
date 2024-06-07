import os
import platform
import shutil
import time
import json
import tempfile
import subprocess


ARCHIVE_FOLDER = 'Archive'
ARCHIVE_THRESHOLD = 30 # days
ERROR_LOG_FILE = os.path.join(tempfile.gettempdir(), 'auto_archive.log')
LOG_LEVEL = 'INFO' # INIT, INFO, ERROR

def get_path():
    return os.path.dirname(__file__)

def get_path_osx():
    path = os.getcwd()
    while not path.endswith('.app'):
        path = os.path.dirname(path)
        if path == '/':
            return get_path()
    return path

def err_log(msg, log_type='ERROR'):
    if log_type == 'INFO' and LOG_LEVEL == 'ERROR':
        return
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        if msg == '' and (log_type == 'INFO' or log_type == 'INIT'):
            f.write('\n')
        else:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} {log_type}: {msg}\n")

def revert(run_log, target_dir, archive_folder=ARCHIVE_FOLDER):
    err_log(f'Reverting {run_log}', log_type='INIT')
    try:
        with open(run_log, 'r') as f:
            log = json.load(f)
            err_log(f'Run log: {log}', log_type='INFO')
    except Exception as e:
        err_log(e)
        return
    
    for item in log['moved_files']:
        try:
            src = os.path.join(target_dir, archive_folder, item['dest'])
            dest = os.path.join(target_dir, item['src'])
            err_log(f'Reverting {src} to {dest}', log_type='INFO')
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
        except Exception as e:
            err_log(e)
            continue
    
    err_log('Revert done', log_type='INIT')


if __name__ == '__main__':
    err_log('Process started', log_type='INIT')
    # Mac OS Date Added
    osx_date_added = True
    by_osx_date_added = True
    # get target directory and self name
    if platform.system() == 'Darwin':
        target_dir = get_path_osx()
        err_log(f'Running on OS X: {target_dir}', log_type='INIT')
        if target_dir.endswith('.app'):
            err_log('Running in OS X App Bundle', log_type='INIT')
            self_name = os.path.basename(target_dir)
            target_dir = os.path.dirname(target_dir)
        else:
            self_name = os.path.basename(__file__)
    else:
        target_dir = get_path()
        self_name = os.path.basename(target_dir)
        osx_date_added = False
        by_osx_date_added = False
    
    err_log(f'Target directory: {target_dir}', log_type='INIT')

    # get config from config file
    config = {
        'archive_folder': ARCHIVE_FOLDER,
        'archive_threshold': ARCHIVE_THRESHOLD,
        'ignore': ['archive_config.json', '.archive_config.json', '.localized', '.DS_Store', 'Icon\r'],
        'check_access_time': False,
        'by_osx_date_added': False,
        'disable_check_osx_date_added': False,
        'log_level': 'INFO',
        'debug': False,
        'debug_archive_threshold': 1,
    }
    config_file = os.path.join(target_dir, 'archive_config.json')
    config_file_hidden = os.path.join(target_dir, '.archive_config.json')
    try:
        load_config = {}
        if os.path.exists(config_file):
            err_log(f'Loading config from {config_file}', log_type='INIT')
            with open(config_file, 'r') as f:
                load_config = json.load(f)
                config = {**config, **load_config}
        elif os.path.exists(config_file_hidden):
            err_log(f'Loading config from {config_file_hidden}', log_type='INIT')
            with open(config_file_hidden, 'r') as f:
                load_config = json.load(f)
                config = {**config, **load_config}
        else:
            err_log(f'Config file not found, creating {config_file}', log_type='INIT')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
    except Exception as e:
        err_log(e)
        exit()
    
    err_log(f'Config: {config}', log_type='INIT')

    archive_folder = config['archive_folder']
    archive_threshold = config['archive_threshold']
    debug_mode = config['debug']
    ignore_list = config['ignore']
    check_access_time = config['check_access_time']
    by_osx_date_added = by_osx_date_added and config['by_osx_date_added'] # so it always be false on other platforms
    osx_date_added = not config['disable_check_osx_date_added']
    LOG_LEVEL = config['log_level']

    # if in debug mode, set archive folder to Archive_Debug
    # and archive threshold to 0 day
    if debug_mode:
        archive_folder = 'Archive_Debug'
        archive_threshold = config['debug_archive_threshold']
        # also, save target_dir and self_name to file
        # and config
        err_log('target_dir: {}'.format(target_dir), log_type='Debug')
        err_log('self_name: {}'.format(self_name), log_type='Debug')
        err_log('config: {}'.format(config), log_type='Debug')
    
    # check if revert mode
    if 'revert' in config:
        if os.path.exists(config['revert']):
            err_log('Revert mode', log_type='INIT')
            revert(config['revert'], target_dir, archive_folder)
            # move the json to reverted.json
            file_name, file_ext = os.path.splitext(config['revert'])
            shutil.move(config['revert'], file_name + '_reverted' + file_ext)
            err_log('Process ended', log_type='INIT')
            err_log('', log_type='INIT')
            exit()

    # check if archive folder exists
    archive_dir = os.path.join(target_dir, archive_folder)
    if not os.path.exists(archive_dir):
        try:
            os.mkdir(archive_dir)
        except Exception as e:
            err_log(e)
            err_log('Process ended', log_type='INIT')
            err_log('', log_type='INIT')
            exit()


    # check all files under target directory 
    # except self and archive_folder
    # if the Last Modified Time is older than archive_threshold days
    # move it to yyyy-mm folder under archive_folder
    ignore_list.append(self_name)
    ignore_list.append(archive_folder)
    moved_files = []
    start_time = time.time()
    for file in os.listdir(target_dir):
        if file in ignore_list:
            err_log(f'Ignored: {file}', log_type='INFO')
            continue
        file_path = os.path.join(target_dir, file)
        err_log(f'Checking: {file_path}', log_type='INFO')
        file_stat = os.stat(file_path)
        err_log(f'File stat: {file_stat}', log_type='INFO')
        file_modified_time = file_stat.st_mtime
        file_added_time = file_modified_time
        if osx_date_added or by_osx_date_added:
            try:
                file_added_time_str = subprocess.check_output(['mdls', '-name', 'kMDItemDateAdded', '-raw', file_path]).decode('utf-8').strip()
                file_added_time = time.mktime(time.strptime(file_added_time_str, '%Y-%m-%d %H:%M:%S %z'))
                err_log(f'File added time (OSX): {file_added_time}', log_type='INFO')
            except Exception as e:
                err_log(e)
        # determine file time
        if by_osx_date_added:
            file_time = file_added_time
        else:
            file_time = file_modified_time
        err_log(f'File time: {file_time}', log_type='INFO')
        # determine file threshold time, which one is older
        file_threshold_time = file_modified_time
        if osx_date_added:
            # if file added time is newer than modified time
            # use added time
            file_threshold_time = max(file_modified_time, file_added_time)
            err_log(f'osx_date_added: file threshold time: {file_threshold_time}', log_type='INFO')
        if check_access_time:
            file_access_time = file_stat.st_atime
            file_threshold_time = max(file_threshold_time, file_access_time)
            err_log(f'check_access_time: file threshold time: {file_threshold_time}', log_type='INFO')
        
        err_log(f'Final file threshold time: {file_threshold_time}', log_type='INFO')
        if time.time() - file_threshold_time > archive_threshold * 24 * 60 * 60:
            success = True
            err = None
            try:
                # move file to archive folder
                file_archive_dir_relative = time.strftime('%Y-%m', time.localtime(file_time))
                file_archive_dir = os.path.join(archive_dir, file_archive_dir_relative)
                err_log(f'File archive dir: {file_archive_dir}', log_type='INFO')
                if not os.path.exists(file_archive_dir):
                    try:
                        os.mkdir(file_archive_dir)
                    except Exception as e:
                        err_log(e)
                # check if file with same name exists in archive folder
                # if so, append a number to the file name, but keep extension
                file_archive_path = os.path.join(file_archive_dir, file)
                err_log(f'Init file archive path: {file_archive_path}', log_type='INFO')
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
                err_log(f'Final file archive path: {file_archive_path}', log_type='INFO')
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
            log_file = os.path.join(log_dir, time.strftime('%Y-%m.log', time.localtime(file_time)))
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' ' + file + ' ' + errmsg + '\n')
            except Exception as e:
                err_log(e)
        else:
            err_log(f'File {file} not old enough', log_type='INFO')

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
    
    err_log('Process ended', log_type='INIT')
    err_log('', log_type='INIT')
