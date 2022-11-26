# Glitlab-IP-Scanner

Python script which scans each repository in your Gitlab installation for IPs and saves found addreses into Excel file. Could be useful to prevent data leaks or to find hardcoded configuration data.

## Configuring parameters before usage

File ```./config/values.yaml```:

1. Fill the variable ```gitlab_address``` with domain, where your Gitlab located.
2. Set the starting and ending Gitlab API pages with ```gitlab_api_starting_page``` and ```gitlab_api_ending_page```. Gitlab API returns maximum 100 repos per page, that's why it requires to use pagintation.
3. Specify ```repo_paths``` where you want to search. It could be paths to specific repos or just name of catalogue with bunch of repos (For example COMPANYNAME/backend).
4. Specify full ```branch_names``` (origin/master, origin/develop, etc) where you want to search. If you want to search in all branches, just remove "if" in the script on the line 110.
5. Specify ```ip_regexes``` for ratios of IPs which you want to search. By default script searches in 10.0.0.0/8, 172.0.0.0/8 and 192.0.0.0/8 ratios.
6. Specify ```file_extensions``` which must be excluded from search. Useful when you repos has committed .svg images, .sql database dumps, etc.
7. You also can specify ```path_to_exclude``` if you don't want search for IP addresses in specific files. It must be full path to your file from root of Gitlab repository, for example COMPANYNAME/backend/payment_api/config/gateways.yaml.

File ```./gitlab_token.py```:
This file required for proper work of the script. It contains dummy personal access token, which must be replaced with your real Gitlab API token. More information could be found in [documentation](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html). If you don't use personal access token, just keep default value.

## Temporary files and output Excel file

This script generates a .csv file for each Gitlab API page. Format of the lines is Repository name|Repository URL|Branch name|File path|String with IP address. Delimeter is |. Temporary folder is ```./csv_files```. After checking all pages script concatenates all .csv files into one and generate .xlsx file into folder ```./excel_reports```. Script also writes log file for each Gitlab API page in ```./scan_logs``` folder.

## Requirements

I used this script with Python 3.10.6 and pip3 22.0.2. Work with other Python and pip versions wasn't tested. Dependencies could be installed by a standard command:

```bash
pip3 install -r requirements.txt
```

## How to run

Just use standard command:

```bash
python3 gitlab_ip_scanner.py
```
