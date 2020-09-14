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


def write_to_activated(wit_path, name):
    with open(wit_path+'\\activated.txt', 'w') as f:
        f.write(name)


def init(path: str = PATH) -> None:
    # make a .wit folder
    names = (path + '\\' + MAIN_DIR + '\\' + inner_dir for inner_dir in INNER_DIRS)
    for name in names:
        try:
            os.makedirs(name)
        except FileExistsError:
            print("Directory is already exist:", name)
        else:
            write_to_activated(path +f'\\{MAIN_DIR}', 'master')
    

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
                        return line.replace(commit_type + '=','') 
    except FileNotFoundError:
        return None
    return None

        
def write_to_references(wit_path, new_commit, branch_name):
    path_to_references = wit_path + '\\references.txt'
    if os.path.isfile(path_to_references):
        last_commit = look_for_commit_id(path_to_references, 'HEAD')  
        with open(path_to_references, 'r') as f:
            content = f.read()
            content = content.replace(f'HEAD={last_commit}', f'HEAD={new_commit}')
            content = content.replace(f'{branch_name}={last_commit}', f'{branch_name}={new_commit}')  
    else:
        content = f'''
        HEAD={new_commit}
        master={new_commit}
        '''
        last_commit = None
    with open(path_to_references, 'w') as f:
                f.write(content)
    return last_commit


def commit(wit_path, mesage, merge_commit=None):
    with open(wit_path+'\\activated.txt','r') as f:
        branch_name = f.read()
    path_to_images = wit_path + '\\images' 
    new_commit_id = make_a_commit_folder(path_to_images)
    file_name = path_to_images + '\\' + new_commit_id + '.txt'
    parent_commit = write_to_references(wit_path, new_commit_id, branch_name)
    if merge_commit:
        parent_commit += f',{merge_commit}'
    commit_file(file_name, mesage, parent_commit)
    for content in os.listdir(wit_path + '\\stagin_area'):
        make_a_copy(os.path.abspath(content), path_to_images + '\\' + new_commit_id)
    print(f"Commit: {new_commit_id} created")           


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


def checkout(path, commit_id, branch_name):
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
            write_to_references(path, head_id, branch_name)


def found_parent(path:str, commit_id:str) -> list:
    child_commits = commit_id.split(',')
    commits = []
    for child in child_commits:
        path_to_commit = path + f'\\images\\{child}.txt'
        parents = look_for_commit_id(path_to_commit, 'parent')
        if parents and parents != 'None':
            commits.extend(parents.split(','))
    return commits


def found_branches(path):    
    branches ={}
    with open(path+'\\references.txt', 'r') as f:
        content = f.readlines()
    for line in content:
        try:
            c = line.index('=')
        except ValueError:
            pass
        else:
            branches[line[:c].strip()]= line[c+1:].strip('\n')
    return(branches)


def graph(path):
    points = []
    branches = found_branches(path)
    for branch_name, commit_id in branches.items():
        points.append((branch_name, commit_id[:6]))
        while found_parent(path, commit_id):
            for commit in found_parent(path, commit_id):
                points.append((commit_id[:6], commit[:6]))
            commit_id = ','.join(found_parent(path, commit_id))
        points = points[:-1]
    print_graph(points)
    
        
def print_graph(dots):
    G = nx.DiGraph() 
    G.add_edges_from(dots) 
    plt.figure(figsize =(10,10)) 
    nx.draw_networkx(G, node_color ='blue', node_size=5000) 
    plt.show()


def branch(path, name):
    if len(name)> 39:
        raise ValueError('name should be loess then 40 chars, branch not made')
    path_to_references = path + '\\references.txt'
    if os.path.isfile(path_to_references):
        head_id = look_for_commit_id(path_to_references, 'HEAD')
        with open(path_to_references, 'a') as f:
                f.write(f'{name}={head_id}\n')
    else:
        print('No master yet, can not open branch')


def found_common_commit(wit_path, commit_a, commit_b):
    commita_perents= [commit_a]
    commitb_perents = [commit_b]
    while found_parent(wit_path, commit_a) or found_parent(wit_path, commit_b):
        if list(set(commita_perents).intersection(commitb_perents)):
            return list(set(commita_perents).intersection(commitb_perents))[0]  
            # credit to SilentGhost, https://stackoverflow.com/questions/2864842/common-elements-comparison-between-2-lists
        commit_a = found_parent(wit_path, commit_a)
        commita_perents.extend(commit_a)
        commit_a = ','.join(commit_a)
        if list(set(commita_perents).intersection(commitb_perents)):
            return list(set(commita_perents).intersection(commitb_perents))[0]
        commit_b = found_parent(wit_path, commit_b)
        commitb_perents.extend(commit_b)
        if list(set(commita_perents).intersection(commitb_perents)):
            return list(set(commita_perents).intersection(commitb_perents))[0]
        commit_b = ','.join(commit_b)
    return None  # never happend


def update_commit_to_merge(wit_path, commit):
    # adding all new/changes files to staging_folder
    stage_area_path = wit_path + '\\stagin_area'
    file_changes = filecmp.dircmp(stage_area_path,wit_path + f'\\images\\{commit}').right_only
    file_changes.extend(filecmp.dircmp(stage_area_path,wit_path + f'\\images\\{commit}').diff_files)
    for a_file in file_changes:
        add(a_file)


def merge(wit_path, branch_name):
    branch_commit = found_branches(wit_path)[branch_name]
    head_commit = found_branches(wit_path)['HEAD']
    common_commit = found_common_commit(wit_path, branch_commit, head_commit)
    path_to_stage_area = wit_path + '\\stagin_area'
    path_to_common_commit = wit_path + f'\\images\\{common_commit}'
    for subpath in os.listdir(path_to_common_commit):
        make_a_copy(path_to_common_commit + '\\' + subpath, path_to_stage_area)
    update_commit_to_merge(wit_path, branch_commit)
    update_commit_to_merge(wit_path, head_commit)
    commit(wit_path, 'Merging commit', branch_commit)
  

if __name__ == "__main__":
    if sys.argv[-1] == 'init':
        init(PATH)
    if sys.argv[1] == 'add':
        add(sys.argv[-1])
    if sys.argv[1] == 'commit':
        wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        commit(wit_path, sys.argv[-1])
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
            if len(sys.argv[-1]) != 40:
                commit_id = look_for_commit_id(wit_path + '\\references.txt', sys.argv[-1])
                print(commit_id)
                write_to_activated(wit_path, sys.argv[-1])
                checkout(wit_path, commit_id, sys.argv[-1])
                if not commit_id:
                    raise FileNotFoundError("master ID not found")
            else:
                commit_id = sys.argv[-1]
                checkout(wit_path, commit_id, 'master')

    if sys.argv[1] == 'graph':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("No .wit directory found :(\n")
        else:
            graph(wit_path)

    if sys.argv[1] == 'branch':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("No .wit directory found :(\n")
        else:
            branch(wit_path, sys.argv[-1])

    if sys.argv[1] == 'merge':
        try:
            wit_path = path_to_wit(os.path.abspath(sys.argv[0]))
        except FileNotFoundError:
            print("No .wit directory found :(\n")
        else:
            merge(wit_path, sys.argv[-1])
            