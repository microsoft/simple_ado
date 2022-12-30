import os
import pathlib

import simple_ado
import argparse
import logging
from auth_helper import AuthHelper
from simple_ado import ADOException
from simple_ado.exceptions import ADOHTTPException

def main():
    logger = logging.getLogger("test")
    project_id = os.environ["SIMPLE_ADO_PROJECT_ID"]
    repo_id = os.environ["SIMPLE_ADO_REPO_ID"]
    token = os.environ["SIMPLE_ADO_BASE_TOKEN"]
    username = os.environ["SIMPLE_ADO_USERNAME"]
    tenant = os.environ["SIMPLE_ADO_TENANT"]
    output = pathlib.Path(__file__).parent / pathlib.Path(outputDir) / pathlib.Path(repo_id + ".zip")
    if not pathlib.Path.is_dir(pathlib.Path(output).parent):
        pathlib.Path.mkdir(pathlib.Path(output).parent)
    print("* Fetching the repo: " + repoUrlStr)
    
    try:
        ah = AuthHelper()
        token = ah.adoAuthenticate()

        print("** Setting up ADOHTTPClient with " + tenant)
        http = simple_ado.http_client.ADOHTTPClient(tenant=tenant,
                    credentials=token,
                    user_agent="test",
                    log = logger
                )
        git_client = simple_ado.git.ADOGitClient(http_client=http, log=logger)
        print("** Getting Repository: " + repo_id + " from " + project_id)
        repo = git_client.get_repository(repository_id=repo_id, project_id=project_id)
        branch = repo["defaultBranch"]
        branch = branch.split("/")[-1]
        #callback=None
        #if progress:
        #    callback=handle_progress
        #zip = git_client.download_zip(output_path=output, repository_id=repo["id"], branch=branch, project_id=project_id,callback=callback)
        zip = git_client.download_zip(output_path=output, repository_id=repo["id"], branch=branch, project_id=project_id)
    except ADOHTTPException as e:
        print("ADOHTTPException " + str(e.response.status_code) + " on: ")
        print("e.message = " + e.message)
        print("e.response = " + str(e.response.content))
        print("e.request.url = " + e.response.request.url + " path: " + e.response.request.path_url)
        if e.response.request.body:
            print("e.request.body = " + e.response.request.body)
    except ADOException as e:
        if "The output path already exists" in str(e):
            print("Skipping for " + repoUrlStr + " it already exists.")
            pass
        else:
            print("ADOException " + str(e) + " on: ")

if __name__=="__main__":
    parser = argparse.ArgumentParser(
            prog = 'python progress_callback_test.py',
            description = '''Notes.''',
            epilog = '''Notes.'''
    )
    parser.add_argument('-r','--repo',type=str,dest='repoUrlStr',help="REQUIRED: Output directory.")
    parser.add_argument('-o','--output',type=str,dest='output',help="REQUIRED: Output directory.")
    parser.add_argument('-p','--progress',action='store_true',dest='progress',help="Turn on callbacks to show progress of long-running operations.")
    args = parser.parse_args()
    if not args.output:
        print("\n\n*** No output directory provided. See help below. ***\n\n")
        parser.print_help()
        exit(1)
    else:
        outputDir = args.output
        progress = args.progress
        repoUrlStr = args.repoUrlStr
    main()

