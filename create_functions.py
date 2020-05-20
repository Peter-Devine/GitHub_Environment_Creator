import requests
import json
import os
import base64

class GitCreatorFunction():

    def __init__(self, api_token):
        self.api_token = api_token

    def get_headers(self):
        return {'Authorization': 'token ' + self.api_token}

    # Creates a repo for the account holding the api token
    def create_repo(self, repo_name, repo_desc):

        post_data = {
            "name": repo_name,
            "description": repo_desc,
            "private": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "is_template": True,
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "delete_branch_on_merge": False
        }

        headers = self.get_headers()

        print(f"Creating repo: {repo_name}")

        r = requests.post("https://api.github.com/user/repos",
                         json = post_data,
                         headers = headers)

        if r.status_code != 201:
            raise Exception(f"Repo was not made due to the following error:\n{r.content}")
        else:
            print(f"Repo {repo_name} successfully created")

    # Copies all the files of a given user's repo to another user's repo
    def copy_repo(self, source_username, destination_username, source_repo_name, destination_repo_name):
        headers = self.get_headers()

        source_repo_url = f"https://api.github.com/repos/{source_username}/{source_repo_name}/contents"
        destination_repo_url = f"https://api.github.com/repos/{destination_username}/{destination_repo_name}/contents"

        def get_file_contents(url):
            return requests.get(url, headers = headers).content

        def write_to_repo(path, contents):
            print(contents)

            # Strings need to be converted to Base 64 to upload to GitHub
            contents = contents.decode('utf-8')
            contents_bytes = contents.encode('utf-8')
            base64_bytes = base64.b64encode(contents_bytes)
            base64_contents = base64_bytes.decode('utf-8')

            post_data = {
                "message": f"Adding {path} from the {source_repo_url} project",
                "content": base64_contents
            }

            print(f"Copying {path}")

            r = requests.put(path, json = post_data, headers = headers)

            if r.status_code != 201:
                raise Exception(f"Failed in upload of file {path} with error {r.status_code}:\n{r.contents}")

        def copy_items(source_path, destination_path):

            r = requests.get(source_path, headers = headers)

            items = json.loads(r.content)

            for item in items:
                if isinstance(item, str):
                    continue

                # Get the folder or file's name, and it's full source path
                relative_path = item["path"]
                source_item_path = f"{source_repo_url}/{relative_path}"
                item_name = item["name"]
                nested_destination_path = f"{destination_path}/{item_name}"

                if item["download_url"] is None:
                    # Recurse the copy in the nested folder
                    copy_items(source_item_path, nested_destination_path)

                else:
                    file_contents = get_file_contents(item["download_url"])

                    write_to_repo(nested_destination_path, file_contents)

        copy_items(source_repo_url, destination_repo_url)

    # Creates an issue for a given repo from a given user using a given title, body and set of labels
    def create_issue(self, username, repo_name, issue_title, issue_body, issue_labels):

        headers = self.get_headers()

        url = f"https://api.github.com/repos/{username}/{repo_name}/issues"

        post_data = {
            "title": issue_title,
            "body": issue_body,
            "labels": issue_labels,
        }

        r = requests.post(url, json = post_data, headers = headers)

        if r.status_code != 201:
            raise Exception(f"Issue creation failed on {username}/{repo_name} with error code {r.status_code} and message:\n{r.content}")

        data = json.loads(r.content)

        issue_number = data["number"]

        return issue_number

    # Add a comment to an existing issue username/repo_name/issue_number
    def comment_on_issue(self, username, repo_name, issue_number, comment_body):
        headers = self.get_headers()

        url = f"https://api.github.com/repos/{username}/{repo_name}/issues/{issue_number}/comments"

        post_data = {
            "body": comment_body
        }

        r = requests.post(url, json = post_data, headers = headers)

        if r.status_code != 201:
            raise Exception(f"Comment creation on {username}/{repo_name}/{issue_number} failed with error code {r.status_code} and message:\n{r.content}")
