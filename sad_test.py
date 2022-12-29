import json
from json.decoder import JSONDecodeError
import os
import simple_ado
from helpers.ado_url import AdoUrl
import argparse
import logging

def main():
    logger = logging.getLogger("test")
    au = AdoUrl(repoUrlStr=repoUrlStr)
    print("* Fetching the repo: " + repoUrlStr)
    try:
        print("** Setting up ADOHTTPClient with " + au.adoOrg)
        http = simple_ado.http_client.ADOHTTPClient(tenant=au.adoOrg,
                    credentials=(os.environ["SIMPLE_ADO_USERNAME"],os.environ["SIMPLE_ADO_BASE_TOKEN"]),
                    user_agent="test",
                    log = logger
                )
        git_client = simple_ado.git.ADOGitClient(http_client=http, log=logger)
        print("** Getting Repository: " + au.adoRepo + " from " + au.adoProj)
        repo = git_client.get_repository(repository_id=au.adoRepo, project_id=au.adoProj)
        print("** Getting an Item: " + repo["id"] + " from " + au.adoProj + " and path = " + outputDir)
        item = git_client.get_item(repository_id=repo["id"],path="/",project_id=au.adoProj,include_content_metadata=True,include_content=False)
        branch = repo["defaultBranch"]
        branch = branch.split("/")[-1]
        output = os.path.join(outputDir, au.adoRepo + ".zip")
        zip = git_client.download_zip(output_path=output, repository_id=repo["id"], branch=branch, project_id=au.adoProj)
    except Exception as e:
        print(e)

if __name__=="__main__":
    parser = argparse.ArgumentParser(
            prog = 'python sad_test.py',
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

