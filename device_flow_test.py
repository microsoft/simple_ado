import os
import pathlib
import sys
import simple_ado
import argparse
import logging
from auth_helper import AuthHelper, AuthError
from simple_ado import ADOException
from simple_ado.exceptions import ADOHTTPException

def main():
    logging.basicConfig(level=logging.DEBUG,handlers=[logging.StreamHandler(sys.stdout)])
    logger = logging.getLogger("ado.device_flow_test")
    app_id = os.environ["appId"]
    scope = os.environ["scope"]
    project_id = os.environ["SIMPLE_ADO_PROJECT_ID"]
    repo_id = os.environ["SIMPLE_ADO_REPO_ID"]
    tenant = os.environ["SIMPLE_ADO_TENANT"]
    output = pathlib.Path.home() / pathlib.Path(outputDir) / pathlib.Path(repo_id + ".zip")
    if not pathlib.Path.is_dir(pathlib.Path(output).parent):
        pathlib.Path.mkdir(pathlib.Path(output).parent)
    logger.debug("* Fetching the repo: " + repoUrlStr)
    
    try:
        ah = AuthHelper(scope=scope,app_id=app_id,log=logger)
        token = ah.device_flow_auth()

        logger.debug("** Setting up ADOHTTPClient with " + tenant)
        http = simple_ado.http_client.ADOHTTPClient(tenant=tenant,
                    credentials=token,
                    user_agent="test",
                    log = logger
                )
        git_client = simple_ado.git.ADOGitClient(http_client=http, log=logger)
        logger.debug("** Getting Repository: " + repo_id + " from " + project_id)
        repo = git_client.get_repository(repository_id=repo_id, project_id=project_id)
        branch = repo["defaultBranch"]
        branch = branch.split("/")[-1]
        zip = git_client.download_zip(output_path=output, repository_id=repo["id"], branch=branch, project_id=project_id)
        logger.debug("Completed.")
    except ADOHTTPException as e:
        logger.critical("ADOHTTPException " + str(e.response.status_code) + " on: ")
        logger.critical("e.message = " + e.message)
        logger.critical("e.response = " + str(e.response.content))
        logger.critical("e.request.url = " + e.response.request.url + " path: " + e.response.request.path_url)
        if e.response.request.body:
            logger.critical("e.request.body = " + e.response.request.body)
    except ADOException as e:
        if "The output path already exists" in str(e):
            logger.debug("Skipping for " + repoUrlStr + " it already exists.")
            pass
        else:
            logger.critical("ADOException " + str(e) + " on: ")
    except AuthError as e:
        logger.debug(str(e))

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

