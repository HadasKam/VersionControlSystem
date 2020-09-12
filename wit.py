import datetime
import filecmp
import os
import random
import shutil
import sys

import matplotlib.pyplot as plt
import networkx as nx


MAIN_DIR = '.wit'
INNER_DIRS = ['images', 'stagin_area']
PATH = os.getcwd()


def init(path: str = PATH) -> None:
    # make a .wit folder
    names = (path + '\\' + MAIN_DIR + '\\' + inner_dir for inner_dir in INNER_DIRS)
    for name in names:
        try:
            os.makedirs(name)
        except FileExistsError:
            print("Directory is already exist:", name)
    

def path_to_wit(path: str) -> str:
    # return the closer path to .wit folder
    original_path = path
    path = '\\'.join(path.split('\\')[:-1])
    while path:
        if os.path.exists(path + '\\.wit'):
            return(path + '\\.wit')
        path = '\\'.join(path.split('\\')[:-1])
    raise FileNotFoundError('The .wit directory not found', original_path)


def make_a_copy(full_path: str, directory_path: str) -> None:
    # copy the content of full_path to directory path
    try:
        shutil.copy(full_path, directory_path)
        
    except PermissionError:
        name = full_path.split('\\')[-1]
        directory_path = directory_path + '\\' + name  
        try:
            os.makedirs(directory_path)
        except FileExistsError:
            shutil.rmtree(directory_path)
            os.makedirs(directory_path)
        for subpath in os.listdir(full_path):
            make_a_copy(full_path + '\\' + subpath, directory_path)
        

def add(path: str) -> None: 
    # copy the content of path to .wit--> stagin area
    full_path = os.path.abspath(path)
    path_to_stagin_area = path_to_wit(full_path) + '\\stagin_area'
    make_a_copy(full_path, path_to_stagin_area)


def create_commit_id(length: int = 40) -> str:
    # return rando, str with (length) chars from a-f,0-9
    options = 'abcdef1234567890'
    password = ''
    for _ in range(length):
        password += random.choice(options)
    return password 


def make_a_commit_folder(path: str) -> str:
    # get wit->images folder and : make a commit folder & return commit ID
    try:
        commit_id = create_commit_id()
        directory_folder = path + '\\' + commit_id
        os.makedirs(directory_folder)
    except FileExistsError:
        make_a_commit_folder(path)
    else:
        return commit_id


def commit_file(file_name, commit_message, commit_parent=None) -> None:

    with open(file_name, 'w') as f:
        content = f'''
        parent={commit_parent}
        date={str(datetime.datetime.now())}
        message={commit_message}'''
        f.write(content)


def look_for_commit_id(path, commit_type):
    try:
        with open(path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith(commit_type):
                        return line.strip(commit_type + '=') 
    except FileNotFoundError:
        return None
    return None


def write_to_references(path, head_commit_id, master_commit_id):
    path_to_references = path + '\\references.txt'
    content = f'''
    HEAD={head_commit_id}
    master={master_commit_id}'''
    if os.path.isfile(path_to_references):
        last_commit = look_for_commit_id(path_to_references, 'HEAD')     
    else:
        last_commit = None
    with open(path_to_references, 'w') as f:
            f.write(content)
    return last_commit
        

def commit(path, mesage):
    wit_folder = path_to_wit(os.path.abspath(path))
    path_to_images = wit_folder + '\\images' 
    commit_id = make_a_commit_folder(path_to_images)
    file_name = path_to_images + '\\' + commit_id + '.txt'
    parent_commit = write_to_references(wit_folder, commit_id, commit_id)
    commit_file(file_name, mesage, parent_commit)
    for content in os.listdir(wit_folder + '\\stagin_area'):
        make_a_copy(os.path.abspath(content), path_to_images + '\\' + commit_id)
    print(f"Commit: {commit_id} created") 
    
        
def compare_folders(path1, path2):
    return filecmp.dircmp(path1, path2).right_only
    

def compare_files(path1, path2):
    with_changes = []
    diff = filecmp.dircmp(path1, path2).diff_files
    if diff:
        with_changes.extend(diff)
    for subdir in filecmp.dircmp(path1, path2).subdirs:
        diff = filecmp.dircmp(path1 + f'\\{subdir}', path2 + f'\\{subdir}').diff_files
        if diff:
            with_changes.append(f'{subdir}: {diff}')
    return with_changes
    

def status(path, head_id):
    path_to_last_commit = path + f'\\images\\{head_id}'
    path_to_stagin_area = path + '\\stagin_area'
    path_to_folder = path.strip('\\.wit')
    diffrences = {}
    diffrences['Changes to be commited'] = compare_folders(path_to_last_commit, path_to_stagin_area) 
    diffrences['Changes to be commited'].extend(compare_files(path_to_last_commit, path_to_stagin_area))
    diffrences['Changes not stages for commit'] = compare_files(path_to_stagin_area, path_to_folder)
    diffrences['Untraked files'] = compare_folders(path_to_stagin_area, path_to_folder)
    diffrences['Untraked files'].remove('.wit')
    return(diffrences)


def print_differnces(diff):
    for key, values in diff.items():
        if len(values) != 0:
            print('\n')
            print(key, '\n', '-' * 20)
            for value in values:
                print(value)


def copy_checkout(commit_path, wit_path):
    path_to_stage_area = wit_path + '\\stagin_area'
    path_to_main = wit_path.strip('\\.wit')
    for subpath in os.listdir(commit_path):
            make_a_copy(commit_path + '\\' + subpath, path_to_main)
            make_a_copy(commit_path + '\\' + subpath, path_to_stage_area)


def checkout(path, commit_id):
    commit_folder = path + '\\images\\' + commit_id
    try:
        os.chdir(commit_folder)
    except OSError:
        print("Unvalid Commit ID")
    else:
        diff = status(path, commit_id)
        if diff['Changes to be commited'] or diff['Changes not stages for commit']:
            print("Can't do checkout", print_differnces(diff))
        else:
            copy_checkout(commit_folder, path)
            head_id = commit_id
            master_id = look_for_commit_id(path + '\\references.txt', 'master')
            write_to_references(path, head_id, master_id)


def found_parent(path, commit_id):
    path_to_commit = path + f'\\images\\{commit_id}.txt'
    return look_for_commit_id(path_to_commit, 'parent')


def graph(path):
    head_commit = look_for_commit_id(path + '\\references.txt', 'HEAD')
    points = [('HEAD', head_commit[:6])]
    while found_parent(path, head_commit):
        points.append((head_commit[:6], found_parent(path, head_commit)[:6]))
        head_commit = found_parent(path, head_commit)
    print_graph(points[:-1])
    
        
def print_graph(dots):
    G = nx.DiGraph() 
    G.add_edges_from(dots) 
  
    plt.figure(figsize =(10,10)) 
    nx.draw_networkx(G, node_color ='blue', node_size=5000) 
    plt.show()


if __name__ == "__main__":
    if sys.argv[-1] == 'init':
        init(PATH)
    if sys.argv[1] == 'add':
        add(sys.argv[-1])
    if sys.argv[1] == 'commit':
        commit(sys.argv[0], sys.argv[-1])
    if sys.argv[1] == 'status':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("You don't have wit directory. so which status you want? :).\n")
        else:
            head_id = look_for_commit_id(wit_path, 'HEAD')
            diff = status(wit_path, head_id)
            print('\nCommit HEAD ID:', head_id)
            print_differnces(diff)
    if sys.argv[1] == 'checkout':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("You don't have wit directory. can't do checkout.\n")
        else:
            if sys.argv[-1] == 'master':
                commit_id = look_for_commit_id(wit_path + '\\references.txt', 'master')
                if not commit_id:
                    raise FileNotFoundError("master ID not found")
            else:
                commit_id = sys.argv[-1]
                checkout(wit_path, commit_id)

    if sys.argv[1] == 'graph':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("No .wit directory found :(\n")
        else:
            graph(wit_path)