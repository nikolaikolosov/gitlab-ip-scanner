import requests
import sys
import os
import re
import git
import shutil
import gitlab_token
import glob
import yaml
import pandas as pd

try:
    os.mkdir("./csv_files")
except Exception as e:
    print(e)

try:
    os.mkdir("./excel_reports")
except Exception as e:
    print(e)

try:
    os.mkdir("./scan_logs")
except Exception as e:
    print(e)

is_found = False

yaml_file = open("./config/values.yaml", 'r')
yaml_content = yaml.safe_load(yaml_file)

array_with_branch_names =[]
for branch_name in yaml_content['branch_names']:
    array_with_branch_names.append(branch_name)

array_with_regexes = []
for regex in yaml_content['ip_regexes']:
    array_with_regexes.append(regex)

array_with_file_extensions = []
for file_extension in yaml_content['file_extensions']:
    array_with_file_extensions.append(file_extension)

excluded_file_extenstions = tuple(array_with_file_extensions)

array_with_repo_paths = []
for repo_path in yaml_content['repo_paths']:
    array_with_repo_paths.append(repo_path)

included_repo_paths = tuple(array_with_repo_paths)

array_with_excluded_file_paths = []
for file_path in yaml_content['paths_to_exclude']:
    file_path = f"./temp/{file_path}"
    array_with_excluded_file_paths.append(file_path)

excluded_file_paths = tuple(array_with_excluded_file_paths)

for page_number in range(yaml_content['gitlab_api_starting_page'],yaml_content['gitlab_api_ending_page']): #Range must match the number of repos in the Gitlab. Each number represents 100 repos. Starting from 1, ending with n+1
    list_of_files_with_ips_path = f"./csv_files/scan_page_{page_number}.csv"
    gitlab_ip_scan_log_path = f"./scan_logs/scan_log_{page_number}.txt"

    try:
        os.remove(list_of_files_with_ips_path)
    except Exception as e:
        print(e)

    try:
        os.remove(gitlab_ip_scan_log_path)
    except Exception as e:
        print(e)

    print(f"Receiving list of repos by Gitlab API, page {page_number}")

    if gitlab_token.token == "12345678901234567890":
        try:
            array_with_repos_information = requests.get(f"{yaml_content['gitlab_address']}/api/v4/projects/?private=true&per_page=10000&page={page_number}")
        except Exception as e:
            print(e)
    else:
        try:
            array_with_repos_information = requests.get(f"{yaml_content['gitlab_address']}/api/v4/projects/?private=true&per_page=10000&page={page_number}", headers={"PRIVATE-TOKEN": f"{gitlab_token.token}"})
        except Exception as e:
            print(e)

    print(f"List of repos page {page_number} successfully received")

    for repo in array_with_repos_information.json():
        ssh_url_to_repo = repo['ssh_url_to_repo']
        folder_name = repo['path']
        repo_id = repo['id']
        web_url = repo['web_url']
        full_path = repo['namespace']['full_path']
        destFolder = f"./temp/{folder_name}"
        
        if full_path.startswith(included_repo_paths):
            print(f"Downloading repository {folder_name} into {destFolder}, page {page_number}")

            try:
                git.Repo.clone_from(ssh_url_to_repo, f"{destFolder}")
            except Exception as e:
                print(e)

            print(f"Repository {folder_name} downloaded. Starting to search for IP addresses")

            repo = git.Repo(f"{destFolder}")
            remote_refs = repo.remote().refs

            for ref in remote_refs:
                if ref.name in array_with_branch_names:
                    with open(gitlab_ip_scan_log_path, "a") as log_file:
                        log_file.write(f"Searching for IP-addresses in {destFolder}, branch is {ref.name[7:]}\n")
                        print(f"Searching for IP-addresses in {destFolder}, branch is {ref.name}")
                        repo.git.checkout(ref.name, "--force")
                        for path, subdirs, files in os.walk(destFolder):
                            for name in files:
                                if not name.endswith(excluded_file_extenstions):
                                    file_path = os.path.join(path, name)
                                    if file_path not in (excluded_file_paths):
                                        try: 
                                            txtFile = open(file_path, 'r', encoding='unicode_escape', errors='ignore')
                                            for regex in array_with_regexes:
                                                pattern = re.compile(r"%s"%regex)
                                                with open(list_of_files_with_ips_path, "a") as csv_file:
                                                    for line in txtFile:
                                                        if re.search(pattern, line) is not None:
                                                            is_found = True
                                                            line_to_write = f"{folder_name}|{web_url}|{ref.name[7:]}|{file_path[7:]}|{line}"
                                                            if line.endswith('\n'):
                                                                csv_file.write(line_to_write)
                                                            else:
                                                                csv_file.write(f"{line_to_write}\n")
                                                    csv_file.close()                          
                                            txtFile.close()
                                        except Exception as e:
                                            print(e, file_path)
                    log_file.close()
            print(f"Deleting folder {destFolder}")
            shutil.rmtree(destFolder, ignore_errors=True)

excel_report_path = "./excel_reports/list_of_files_with_ips.xlsx"
combined_csv_path = "./csv_files/combined_list_of_files_with_ips.csv"

try:
    os.remove(combined_csv_path)
except Exception as e:
    print(e)

try:
    os.remove(excel_report_path)
except Exception as e:
    print(e)

scan_page_files = os.path.join("./csv_files/", "scan_page_*.csv")

scan_page_files = glob.glob(scan_page_files)
scan_page_files.sort()

with open(combined_csv_path, 'w') as combined_csv_file:
    for fname in scan_page_files:
        with open(fname) as infile:
            for line in infile:
                combined_csv_file.write(line)

header = "Repository name|Repository URL|Branch name|File path|String with IP address\n"

with open(combined_csv_path, 'r+') as file:
   content = file.read()
   file.seek(0)
   file.write(header + content)
   file.close()

df = pd.read_csv(combined_csv_path, delimiter="|")
df.to_excel(excel_report_path, index = False)

if is_found == True:
    print("IP addresses found. Job finished with exit code 1")
    sys.exit(1)
else:
    print("IP addresses not found. All clear. Job finished with exit code 0")
    sys.exit(0)
