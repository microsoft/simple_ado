import os
import simple_ado
from helpers.ado_url import AdoUrl
import argparse
import logging
import colorama
from tqdm import tqdm

def handle_progress(chunk_size=None,response=None,output=None):
    if chunk_size and response:
        print("output hp = " + output)
        length = int(response.headers.get("content-length",0))
        print("content length = " + str(length))
        if length == 0:
            print("Dealing with Unknown Size")
            with open(output, "wb") as file:
                for chunk in tqdm(response.iter_content(chunk_size),
                                  desc="Unknown file size",
                                  unit="kB", unit_scale=True, unit_divisor=1024):
                    file.write(chunk)
                    file.flush()
        else:
            with open(output, "wb") as file:
                for chunk in tqdm(response.iter_content(chunk_size),
                                  desc="Downloading file",
                                  total=length/1024, unit="kB",
                                  unit_scale = True, unit_divisor=1024):
                    file.write(chunk)
                    file.flush()
    return 0
 
def main():
    logger = logging.getLogger("test")
    project_id = os.environ["SIMPLE_ADO_PROJECT_ID"]
    repo_id = os.environ["SIMPLE_ADO_REPO_ID"]
    token = os.environ["SIMPLE_ADO_BASE_TOKEN"]
    username = os.environ["SIMPLE_ADO_USERNAME"]
    tenant = os.environ["SIMPLE_ADO_TENANT"]

    output = os.path.join(outputDir, repo_id + ".zip")
    print("* Fetching the repo: " + repoUrlStr)
    
    try:
        print("** Setting up ADOHTTPClient with " + tenant)
        http = simple_ado.http_client.ADOHTTPClient(tenant=tenant,
                    credentials=(username,token),
                    user_agent="test",
                    log = logger
                )
        git_client = simple_ado.git.ADOGitClient(http_client=http, log=logger)
        print("** Getting Repository: " + repo_id + " from " + project_id)
        repo = git_client.get_repository(repository_id=repo_id, project_id=project_id)
        print("** Getting an Item: " + repo["id"] + " from " + project_id + " and path = " + outputDir)
        #item = git_client.get_item(repository_id=repo["id"],path="/",project_id=project_id,include_content_metadata=True,include_content=False)
        branch = repo["defaultBranch"]
        branch = branch.split("/")[-1]
        callback=None
        if progress:
            callback=handle_progress
        zip = git_client.download_zip(output_path=output, repository_id=repo["id"], branch=branch, project_id=project_id,callback=callback)
    except Exception as e:
        print(e)

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

