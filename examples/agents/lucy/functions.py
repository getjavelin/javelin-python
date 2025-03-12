from dotenv import find_dotenv, load_dotenv
import os
import re
from github import Github
from github import GithubException
import requests
import json as json_lib
from openai import OpenAI
from javelin_sdk import JavelinClient, JavelinConfig

load_dotenv(find_dotenv())

def github_scrum_master(user_input):
    """
    Function to act as an AI Scrum Master that checks for issues, creates or updates GitHub issues
    across multiple repositories and integrates with GitHub Projects.
    
    Args:
        user_input (str): The input text from Slack containing commands for the Scrum Master.
        
    Returns:
        str: Response message indicating the action taken.
    """
    # Initialize GitHub client
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        return "Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable."
    
    # Get GitHub Project settings if available
    project_number = os.environ.get("GITHUB_PROJECT_NUMBER")
    project_owner = os.environ.get("GITHUB_PROJECT_OWNER")
    has_project = project_number and project_owner
    
    g = Github(github_token)
    
    # Process the user input to determine the action
    user_input = user_input.strip()
    
    # Direct check for project items listing
    if user_input.lower() in ["list project items", "show project items", "project items", "list issues in projects", "show project issues"]:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        try:
            return list_project_items_graphql(github_token, project_owner, project_number)
        except Exception as e:
            import traceback
            return f"Error listing project items: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Debug command to check project settings
    if user_input.lower() in ["debug project", "check project settings", "project settings"]:
        project_url = ""
        token_info = "❓ Unknown (Cannot verify token permissions)"
        
        if github_token:
            # Try to verify token permissions
            try:
                headers = {"Authorization": f"Bearer {github_token}"}
                
                # Check if token has repo scope
                repo_response = requests.get("https://api.github.com/user/repos?per_page=1", headers=headers)
                has_repo = repo_response.status_code == 200
                
                # Check if token has read:org scope
                org_response = requests.get("https://api.github.com/user/orgs", headers=headers)
                has_read_org = org_response.status_code == 200
                
                # Check if token has project scope (indirect check)
                project_response = requests.get("https://api.github.com/user/projects", headers=headers)
                has_project_scope = project_response.status_code == 200
                
                token_info = f"Token Permissions:\n"
                token_info += f"- repo: {'✅' if has_repo else '❌'}\n"
                token_info += f"- read:org: {'✅' if has_read_org else '❌'}\n"
                token_info += f"- project: {'✅' if has_project_scope else '❌'}"
                
                if not (has_repo and has_read_org and has_project_scope):
                    token_info += "\n\n⚠️ Your token may not have all required permissions.\nCreate a new token with all necessary scopes at: https://github.com/settings/tokens"
            except Exception as e:
                token_info = f"Error checking token permissions: {str(e)}"
        
        if has_project:
            # Check if it's an organization project
            rest_api_url = f"https://api.github.com/users/{project_owner}"
            try:
                response = requests.get(rest_api_url, headers={"Authorization": f"Bearer {github_token}"})
                if response.status_code == 200:
                    user_data = response.json()
                    is_org = user_data.get("type") == "Organization"
                    if is_org:
                        project_url = f"https://github.com/orgs/{project_owner}/projects/{project_number}"
                        
                        # Check if we can access the organization
                        org_url = f"https://api.github.com/orgs/{project_owner}"
                        org_response = requests.get(org_url, headers={"Authorization": f"Bearer {github_token}"})
                        if org_response.status_code != 200:
                            project_url += f" (⚠️ Cannot access organization - token may lack 'read:org' scope)"
                    else:
                        project_url = f"https://github.com/users/{project_owner}/projects/{project_number}"
                else:
                    project_url = f"https://github.com/{project_owner}/projects/{project_number} (⚠️ Cannot verify owner type)"
            except Exception:
                project_url = f"https://github.com/{project_owner}/projects/{project_number} (⚠️ Error checking owner type)"
        else:
            project_url = "❌ Cannot determine URL"
            
        return f"""
Project Settings Debug:
- GITHUB_TOKEN: {'✅ Set' if github_token else '❌ Not set'}
- GITHUB_PROJECT_NUMBER: {project_number if project_number else '❌ Not set'}
- GITHUB_PROJECT_OWNER: {project_owner if project_owner else '❌ Not set'}
- Project URL: {project_url}

{token_info}

To fix permission issues:
1. Create a new Personal Access Token with these scopes: repo, read:org, project
2. Update your .env file with the new token
3. Restart the application
"""
    
    # Check for org repos command
    org_repos_match = re.search(r'list\s+(?:repos|repositories)\s+(?:for|in)\s+(?:org|organization)\s+([^\s]+)', user_input.lower())
    if org_repos_match:
        org_name = org_repos_match.group(1)
        return handle_list_org_repositories(g, org_name)
    
    # Check token permissions command
    if user_input.lower().strip() in ["check token", "token permissions", "check permissions", "check token permissions"]:
        return check_token_permissions(github_token)
    
    # Command to query project using GitHub API v4 explorer format
    if user_input.lower() in ["query project", "project query", "explore project"]:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        try:
            return query_project_explorer_format(github_token, project_owner, project_number)
        except Exception as e:
            import traceback
            return f"Error querying project: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Check for direct repository access by URL
    repo_url_match = re.search(r'(?:access|get|show|view)\s+(?:repo|repository)\s+(https://github\.com/[^\s]+)', user_input.lower())
    if repo_url_match:
        repo_url = repo_url_match.group(1)
        # Extract owner/repo from URL
        url_parts = repo_url.split('/')
        if len(url_parts) >= 5:  # https://github.com/owner/repo
            repo_name = f"{url_parts[3]}/{url_parts[4]}"
            try:
                repo = g.get_repo(repo_name)
                return f"✅ Repository found: {repo.full_name}\nDescription: {repo.description or 'No description'}\nStars: {repo.stargazers_count}\nForks: {repo.forks_count}\nOpen Issues: {repo.open_issues_count}\nURL: {repo.html_url}"
            except GithubException as e:
                return f"Error accessing repository '{repo_name}': {str(e)}"
        else:
            return "Invalid GitHub repository URL. Format should be: https://github.com/owner/repo"
    
    # Check for add issue to project command
    add_to_project_match = re.search(r'add\s+(?:issue|pr)\s+#?(\d+)\s+(?:in|from)\s+([^\s]+)\s+to\s+project', user_input.lower())
    if add_to_project_match:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        
        issue_number = add_to_project_match.group(1)
        repo_name = add_to_project_match.group(2)
        
        # Handle URL format
        if repo_name.startswith("https://"):
            parts = repo_name.split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo/...
                repo_name = f"{parts[3]}/{parts[4]}"
        
        # Split repo_name into owner and repo
        repo_parts = repo_name.split("/")
        if len(repo_parts) != 2:
            return "Invalid repository format. Please use 'owner/repo' format."
        
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        
        try:
            return add_issue_to_project(github_token, project_owner, project_number, repo_owner, repo_name, issue_number)
        except Exception as e:
            import traceback
            return f"Error adding issue to project: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Check for update issue status in project command
    update_status_match = re.search(r'(?:update|set|change)\s+(?:status|state)\s+(?:of|for)\s+(?:issue|pr)\s+#?(\d+)\s+(?:in|from)\s+([^\s]+)\s+to\s+([^\s]+)', user_input.lower())
    if update_status_match:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        
        issue_number = update_status_match.group(1)
        repo_name = update_status_match.group(2)
        new_status = update_status_match.group(3)
        
        # Handle URL format
        if repo_name.startswith("https://"):
            parts = repo_name.split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo/...
                repo_name = f"{parts[3]}/{parts[4]}"
        
        # Split repo_name into owner and repo
        repo_parts = repo_name.split("/")
        if len(repo_parts) != 2:
            return "Invalid repository format. Please use 'owner/repo' format."
        
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        
        try:
            # Try both approaches - first try GraphQL for project status, then fall back to REST API
            try:
                # First try to update in GitHub Projects
                result = update_issue_status_in_project(github_token, project_owner, project_number, repo_owner, repo_name, issue_number, new_status)
                if "Error" in result or "Failed" in result or result.startswith("PVT") or result.startswith("PVTSSF"):
                    # If it fails, fall back to REST API
                    return update_issue_status_rest(g, repo_owner, repo_name, issue_number, new_status)
                return result
            except Exception:
                # If GraphQL approach fails, use REST API
                return update_issue_status_rest(g, repo_owner, repo_name, issue_number, new_status)
        except Exception as e:
            import traceback
            return f"Error updating issue status: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Command to list project status options
    if user_input.lower() in ["list status options", "show status options", "get status options", "project status options", "available status", "status values"]:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        try:
            return list_project_status_options(github_token, project_owner, project_number)
        except Exception as e:
            import traceback
            return f"Error listing status options: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Command to directly update an issue's status
    direct_status_update_match = re.search(r'set\s+issue\s+#?(\d+)\s+(?:in|from)\s+([^\s]+)\s+status\s+to\s+(.+)', user_input.lower())
    if direct_status_update_match:
        if not has_project:
            return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
        
        issue_number = direct_status_update_match.group(1)
        repo_name = direct_status_update_match.group(2)
        new_status = direct_status_update_match.group(3).strip()
        
        # Handle URL format
        if repo_name.startswith("https://"):
            parts = repo_name.split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo/...
                repo_name = f"{parts[3]}/{parts[4]}"
        
        # Split repo_name into owner and repo
        repo_parts = repo_name.split("/")
        if len(repo_parts) != 2:
            return "Invalid repository format. Please use 'owner/repo' format."
        
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        
        try:
            # Try both approaches - first try GraphQL for project status, then fall back to REST API
            try:
                # First try to update in GitHub Projects
                result = update_issue_status_in_project(github_token, project_owner, project_number, repo_owner, repo_name, issue_number, new_status)
                if "Error" in result or "Failed" in result or result.startswith("PVT") or result.startswith("PVTSSF"):
                    # If it fails, fall back to REST API
                    return update_issue_status_rest(g, repo_owner, repo_name, issue_number, new_status)
                return result
            except Exception:
                # If GraphQL approach fails, use REST API
                return update_issue_status_rest(g, repo_owner, repo_name, issue_number, new_status)
        except Exception as e:
            import traceback
            return f"Error updating issue status: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Check for comment on issue command
    comment_issue_match = re.search(r'(?:add|post|create)\s+(?:comment|reply)\s+(?:to|on)\s+(?:issue|pr)\s+#?(\d+)\s+(?:in|from)\s+([^\s]+)\s+(?:with|saying|content)\s+(.*)', user_input.lower())
    if comment_issue_match:
        issue_number = comment_issue_match.group(1)
        repo_name = comment_issue_match.group(2)
        comment_text = comment_issue_match.group(3)
        
        # Handle URL format
        if repo_name.startswith("https://"):
            parts = repo_name.split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo/...
                repo_name = f"{parts[3]}/{parts[4]}"
        
        # Split repo_name into owner and repo
        repo_parts = repo_name.split("/")
        if len(repo_parts) != 2:
            return "Invalid repository format. Please use 'owner/repo' format."
        
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        
        try:
            return add_comment_to_issue(g, repo_owner, repo_name, issue_number, comment_text)
        except Exception as e:
            import traceback
            return f"Error adding comment to issue: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    # Also check for simpler comment format
    simple_comment_match = re.search(r'(?:comment|reply)\s+(?:on|to)\s+#?(\d+)\s+(?:in|from)\s+([^\s]+)\s+(.*)', user_input.lower())
    if simple_comment_match:
        issue_number = simple_comment_match.group(1)
        repo_name = simple_comment_match.group(2)
        comment_text = simple_comment_match.group(3)
        
        # Handle URL format
        if repo_name.startswith("https://"):
            parts = repo_name.split("/")
            if len(parts) >= 5:  # https://github.com/owner/repo/...
                repo_name = f"{parts[3]}/{parts[4]}"
        
        # Split repo_name into owner and repo
        repo_parts = repo_name.split("/")
        if len(repo_parts) != 2:
            return "Invalid repository format. Please use 'owner/repo' format."
        
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        
        try:
            return add_comment_to_issue(g, repo_owner, repo_name, issue_number, comment_text)
        except Exception as e:
            import traceback
            return f"Error adding comment to issue: {str(e)}\n\nTraceback: {traceback.format_exc()}"
    
    
    # Define the functions that can be called
    functions = [
        {
            "name": "list_issues",
            "description": "List open issues in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the repository in format 'owner/repo' or a GitHub URL"
                    }
                },
                "required": ["repository_name"]
            }
        },
        {
            "name": "create_issue",
            "description": "Create a new issue in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the repository in format 'owner/repo' or a GitHub URL"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "The description/body of the issue"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "GitHub usernames to assign to the issue"
                    },
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Labels to add to the issue"
                    }
                },
                "required": ["repository_name", "title"]
            }
        },
        {
            "name": "update_issue",
            "description": "Update an existing issue in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the repository in format 'owner/repo' or a GitHub URL"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "The issue number to update"
                    },
                    "update_details": {
                        "type": "string",
                        "description": "The details to add to the issue"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "GitHub usernames to assign to the issue"
                    }
                },
                "required": ["repository_name", "issue_number"]
            }
        },
        {
            "name": "check_status",
            "description": "Check the status of issues in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the repository in format 'owner/repo' or a GitHub URL"
                    }
                },
                "required": ["repository_name"]
            }
        },
        {
            "name": "list_repositories",
            "description": "List the user's GitHub repositories",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "list_project_items",
            "description": "List items in a GitHub Project",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    
    try:
        config = JavelinConfig(javelin_api_key=os.environ.get("JAVELIN_API_KEY"))
        client = JavelinClient(config)

        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # Register the OpenAI client with the unified route name (e.g., "openai_univ")
        client.register_openai(openai_client, route_name="openai_univ")
        # Call OpenAI to parse the user's intent
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a GitHub Scrum Master assistant that helps manage issues and projects."},
                {"role": "user", "content": user_input}
            ],
            functions=functions,
            function_call="auto"
        )
        
        # Extract the function call
        message = response.choices[0].message
        
        # Check if a function was called
        if message.function_call:
            function_name = message.function_call.name
            function_args = json_lib.loads(message.function_call.arguments)
            
            # Clean up repository name if it's a URL
            if 'repository_name' in function_args and function_args['repository_name']:
                repo_name = function_args['repository_name']
                if repo_name.startswith('http'):
                    url_parts = repo_name.split('/')
                    if len(url_parts) >= 2:
                        repo_name = f"{url_parts[-2]}/{url_parts[-1]}"
                function_args['repository_name'] = repo_name
            
            # Handle different functions
            if function_name == "list_issues":
                return handle_list_issues(g, function_args['repository_name'])
            
            elif function_name == "create_issue":
                title = function_args.get('title', '')
                description = function_args.get('description', '')
                assignees = function_args.get('assignees', [])
                labels = function_args.get('labels', [])
                return handle_create_issue(g, function_args['repository_name'], title, description, assignees, labels, has_project, project_owner, project_number)
            
            elif function_name == "update_issue":
                issue_number = function_args.get('issue_number')
                update_details = function_args.get('update_details', '')
                assignees = function_args.get('assignees', [])
                return handle_update_issue(g, function_args['repository_name'], issue_number, update_details, assignees, has_project, project_owner, project_number)
            
            elif function_name == "check_status":
                return handle_check_status(g, function_args['repository_name'])
            
            elif function_name == "list_repositories":
                return handle_list_repositories(g)
            
            elif function_name == "list_project_items":
                if not has_project:
                    return "GitHub Project settings are not configured. Please set GITHUB_PROJECT_NUMBER and GITHUB_PROJECT_OWNER in your environment variables."
                return list_project_items_graphql(github_token, project_owner, project_number)
        
        # If no function was called, return a helpful message
        return """I couldn't understand your request. Please try one of these commands:
- Create a new issue in [repository] titled [title] with description [description]
- Update issue #X in [repository] with [details]
- List open issues in [repository]
- Check project status for [repository]
- List repositories
- List project items

Example: "Create a new issue in username/repo titled 'Fix login bug' with description 'Users cannot log in'"
"""
    
    except Exception as e:
        return f"Error processing your request: {str(e)}"


def handle_list_issues(github_client, repo_name):
    """Handle listing issues in a repository."""
    try:
        repo = github_client.get_repo(repo_name)
        open_issues = repo.get_issues(state='open')
        if open_issues.totalCount == 0:
            return f"No open issues found in {repo_name}."
        
        response = f"📋 Open Issues in {repo_name}:\n"
        for i, issue in enumerate(open_issues[:10]):  # Limit to 10 issues
            assignee_text = f" (Assigned to: {', '.join([a.login for a in issue.assignees])})" if issue.assignees else ""
            response += f"{i+1}. #{issue.number}: {issue.title}{assignee_text}\n"
        
        if open_issues.totalCount > 10:
            response += f"\n... and {open_issues.totalCount - 10} more issues."
            
        return response
    except GithubException as e:
        return f"Error accessing repository '{repo_name}': {str(e)}"


def handle_create_issue(github_client, repo_name, title, description, assignees, labels, has_project, project_owner, project_number):
    """Handle creating an issue in a repository."""
    try:
        repo = github_client.get_repo(repo_name)
        issue = repo.create_issue(
            title=title,
            body=description,
            assignees=assignees,
            labels=labels
        )
        
        # Add to project if project settings are available
        if has_project:
            try:
                # Add the issue to the project using GraphQL
                github_token = os.environ.get("GITHUB_TOKEN")
                add_to_project_result = add_issue_to_project_graphql(
                    github_token, 
                    project_owner, 
                    project_number, 
                    repo_owner=repo_name.split('/')[0],
                    repo_name=repo_name.split('/')[1],
                    issue_number=issue.number
                )
                return f"✅ Issue created successfully in {repo_name}!\nTitle: {title}\nURL: {issue.html_url}\n\n{add_to_project_result}"
            except Exception as e:
                return f"✅ Issue created successfully in {repo_name}, but couldn't add to project.\nTitle: {title}\nURL: {issue.html_url}\nError: {str(e)}"
        
        return f"✅ Issue created successfully in {repo_name}!\nTitle: {title}\nURL: {issue.html_url}"
    except GithubException as e:
        return f"Error creating issue in '{repo_name}': {str(e)}"


def handle_update_issue(github_client, repo_name, issue_number, update_details, assignees, has_project, project_owner, project_number):
    """Handle updating an issue in a repository."""
    try:
        repo = github_client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        
        # Update issue with new details
        if update_details:
            issue.edit(body=f"{issue.body}\n\n**Update:**\n{update_details}")
        
        # Add assignees if provided
        if assignees:
            issue.add_to_assignees(*assignees)
        
        # Update status in project (placeholder - would require GraphQL in real implementation)
        status_message = ""
        if has_project:
            status_message = f"\n\nNote: To update the status in your project, please use the GitHub UI."
            
        return f"✅ Issue #{issue_number} updated successfully in {repo_name}!\nURL: {issue.html_url}{status_message}"
    except ValueError:
        return "Invalid issue number. Please provide a valid number."
    except GithubException as e:
        return f"Error updating issue: {str(e)}"


def handle_check_status(github_client, repo_name):
    """Handle checking the status of a repository."""
    try:
        repo = github_client.get_repo(repo_name)
        open_issues = repo.get_issues(state='open')
        closed_issues = repo.get_issues(state='closed')
        
        response = f"📊 Project Status for {repo_name}:\n"
        response += f"- Open issues: {open_issues.totalCount}\n"
        response += f"- Closed issues: {closed_issues.totalCount}\n"
        
        # Get recently updated issues
        recent_issues = repo.get_issues(state='all', sort='updated', direction='desc')
        if recent_issues.totalCount > 0:
            response += "\n🔄 Recently Updated Issues:\n"
            for i, issue in enumerate(recent_issues[:5]):  # Limit to 5 issues
                status = "🟢 Open" if issue.state == "open" else "🔴 Closed"
                response += f"{i+1}. #{issue.number}: {issue.title} - {status}\n"
        
        return response
    except GithubException as e:
        return f"Error checking status: {str(e)}"


def handle_list_repositories(github_client):
    """Handle listing repositories."""
    try:
        response = "📚 Your Repositories:\n"
        
        # List user's repositories
        user = github_client.get_user()
        user_repos = list(user.get_repos()[:15])  # Limit to 15 repos
        
        for i, repo in enumerate(user_repos):
            response += f"{i+1}. {repo.full_name} - {repo.description or 'No description'}\n"
        
        user_repos_count = len(user_repos)
        
        # List organizations the user belongs to
        orgs = user.get_orgs()
        org_repos = []
        
        for org in orgs:
            try:
                # Get up to 5 repos from each organization
                org_repos.extend(list(org.get_repos()[:5]))
            except GithubException:
                # Skip if we can't access the org's repos
                pass
        
        if org_repos:
            response += "\n📚 Organization Repositories:\n"
            for i, repo in enumerate(org_repos[:15]):  # Limit to 15 org repos
                response += f"{i+1}. {repo.full_name} - {repo.description or 'No description'}\n"
        
        # Check if we need to mention there are more repos
        total_shown = min(15, user_repos_count) + min(15, len(org_repos))
        total_repos = user_repos_count + len(org_repos)
        
        if total_repos > total_shown:
            response += f"\n... and {total_repos - total_shown} more repositories."
        
        return response
    except GithubException as e:
        return f"Error listing repositories: {str(e)}"


def list_project_status_options(token, owner, project_number):
    """
    List available status options for a GitHub Project.
    
    Args:
        token (str): GitHub token
        owner (str): Project owner (username or organization)
        project_number (str): Project number
        
    Returns:
        str: Formatted response with status options
    """
    try:
        # Create a GitHub client
        g = Github(token)
        
        # Get standard GitHub issue states
        standard_states = [
            {"name": "Open", "description": "Issue is open and active", "color": "2cbe4e"},
            {"name": "Closed (Completed)", "description": "Issue has been completed", "color": "6f42c1"},
            {"name": "Closed (Not Planned)", "description": "Issue won't be addressed", "color": "d73a4a"}
        ]
        
        # Get common status labels
        common_labels = [
            {"name": "status: todo", "description": "To do items", "color": "0E8A16"},
            {"name": "status: in progress", "description": "In progress items", "color": "FFA500"},
            {"name": "status: review", "description": "Items under review", "color": "1D76DB"},
            {"name": "status: blocked", "description": "Blocked items", "color": "D93F0B"}
        ]
        
        # Format the response
        response_text = f"📋 Status Options for GitHub Issues:\n\n"
        
        # Add standard states
        response_text += "Standard Issue States:\n"
        for i, state in enumerate(standard_states):
            response_text += f"{i+1}. {state['name']}"
            if state.get("description"):
                response_text += f" - {state['description']}"
            response_text += "\n"
        
        response_text += "\nCommon Status Labels:\n"
        for i, label in enumerate(common_labels):
            response_text += f"{i+1}. {label['name']}"
            if label.get("description"):
                response_text += f" - {label['description']}"
            response_text += "\n"
        
        # Try to get custom labels from a repository
        try:
            # Find a repository to check for custom labels
            repos = []
            if "/" in owner:  # If owner is in the format "owner/repo"
                parts = owner.split("/")
                if len(parts) == 2:
                    repos = [g.get_repo(owner)]
            else:
                # Try to get user's repositories
                try:
                    user = g.get_user(owner)
                    repos = list(user.get_repos()[:5])  # Get up to 5 repos
                except:
                    # Try as organization
                    try:
                        org = g.get_organization(owner)
                        repos = list(org.get_repos()[:5])  # Get up to 5 repos
                    except:
                        pass
            
            # Check for status labels in repositories
            custom_labels = []
            for repo in repos:
                try:
                    for label in repo.get_labels():
                        if label.name.lower().startswith("status:") and label.name not in [l["name"] for l in common_labels]:
                            custom_labels.append({
                                "name": label.name,
                                "description": label.description,
                                "color": label.color
                            })
                except:
                    continue
            
            # Add custom labels if found
            if custom_labels:
                response_text += "\nCustom Status Labels Found:\n"
                for i, label in enumerate(custom_labels):
                    response_text += f"{i+1}. {label['name']}"
                    if label.get("description"):
                        response_text += f" - {label['description']}"
                    response_text += "\n"
        except:
            # Ignore errors when trying to get custom labels
            pass
        
        response_text += "\nTo update an issue's status, use one of these commands:\n"
        response_text += "- 'Update status of issue #X in owner/repo to STATUS'\n"
        response_text += "- 'Set issue #X in owner/repo status to STATUS'\n\n"
        response_text += "Examples:\n"
        response_text += "- 'Update status of issue #1 in abhiabhijitorg/test_repo to In Progress'\n"
        response_text += "- 'Set issue #1 in abhiabhijitorg/test_repo status to Closed'\n"
        
        return response_text
    except Exception as e:
        import traceback
        return f"Error listing status options: {str(e)}\n\nTraceback: {traceback.format_exc()}"


def list_project_items_graphql(token, owner, project_number):
    """
    List GitHub Project items using GraphQL API.
    
    Args:
        token (str): GitHub token
        owner (str): Project owner (username or organization)
        project_number (str): Project number
        
    Returns:
        str: Formatted response with project items
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # First, check if the owner is a user or organization
        rest_api_url = f"https://api.github.com/users/{owner}"
        response = requests.get(rest_api_url, headers=headers)
        
        if response.status_code != 200:
            return f"Error: Could not find user or organization '{owner}'. Please check the project owner name."
        
        user_data = response.json()
        is_org = user_data.get("type") == "Organization"
        
        # Construct the correct project URL for display
        if is_org:
            project_url = f"https://github.com/orgs/{owner}/projects/{project_number}"
        else:
            project_url = f"https://github.com/users/{owner}/projects/{project_number}"
        
        # Try a different approach - use the REST API to verify token permissions
        if is_org:
            org_url = f"https://api.github.com/orgs/{owner}"
            org_response = requests.get(org_url, headers=headers)
            if org_response.status_code != 200:
                return f"Error: Cannot access organization '{owner}'. Your token may not have the necessary permissions.\n\nPlease ensure your GitHub token has 'read:org' and 'project' scopes."
        
        # Now get the project ID using the correct query based on type
        if is_org:
            # Try a more direct approach for organization projects
            query = """
            query {
              viewer {
                organization(login: "%s") {
                  projectV2(number: %s) {
                    id
                    title
                  }
                }
              }
            }
            """ % (owner, project_number)
            
            # Also try the standard approach
            query2 = """
            query($owner: String!, $number: Int!) {
              organization(login: $owner) {
                projectV2(number: $number) {
                  id
                  title
                }
              }
            }
            """
            
            # Try both queries
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query},
                headers=headers
            )
            
            if response.status_code != 200 or "errors" in response.json():
                # If first query fails, try the second one
                variables = {
                    "owner": owner,
                    "number": int(project_number)
                }
                
                response = requests.post(
                    "https://api.github.com/graphql",
                    json={"query": query2, "variables": variables},
                    headers=headers
                )
        else:
            query = """
            query($owner: String!, $number: Int!) {
              user(login: $owner) {
                projectV2(number: $number) {
                  id
                  title
                }
              }
            }
            """
            
            variables = {
                "owner": owner,
                "number": int(project_number)
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers
            )
        
        if response.status_code != 200:
            return f"Error accessing project: {response.status_code} - {response.text}"
        
        result = response.json()
        
        # Debug the response
        if "errors" in result:
            error_details = result['errors'][0]
            error_msg = error_details.get('message', 'Unknown error')
            error_type = error_details.get('type', 'Unknown type')
            error_path = '.'.join(error_details.get('path', ['unknown']))
            
            return f"""GraphQL Error when fetching items:
Error: {error_msg}
Type: {error_type}
Path: {error_path}

This could be due to:
1. API changes in GitHub's GraphQL schema
2. Permission issues with your token
3. The project structure not matching our query

Please try:
1. Using the 'Check token permissions' command to verify your token has all required scopes
2. Ensuring you have access to the project at {project_url}
"""
        
        # Check if project exists based on owner type
        project = None
        if is_org:
            # Try both possible response formats
            if result.get("data", {}).get("organization") and result["data"]["organization"].get("projectV2"):
                project = result["data"]["organization"]["projectV2"]
            elif result.get("data", {}).get("viewer", {}).get("organization") and result["data"]["viewer"]["organization"].get("projectV2"):
                project = result["data"]["viewer"]["organization"]["projectV2"]
        else:
            if result.get("data", {}).get("user") and result["data"]["user"].get("projectV2"):
                project = result["data"]["user"]["projectV2"]
        
        if not project:
            return f"""Project not found: {project_url}

This is likely a permissions issue. Please ensure:
1. Your GitHub token has the necessary scopes (repo, read:org, project)
2. You have access to this project
3. The project number is correct

You can verify the project exists by visiting: {project_url}
"""
        
        project_id = project["id"]
        project_title = project["title"]
        
        # Now get the project items
        items_query = """
        query($projectId: ID!, $first: Int!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: $first) {
                nodes {
                  id
                  fieldValues(first: 8) {
                    nodes {
                      __typename
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                    }
                  }
                  content {
                    __typename
                    ... on Issue {
                      title
                      number
                      repository {
                        name
                        owner {
                          login
                        }
                      }
                      state
                    }
                    ... on PullRequest {
                      title
                      number
                      repository {
                        name
                        owner {
                          login
                        }
                      }
                      state
                    }
                    ... on DraftIssue {
                      title
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id,
            "first": 20  # Limit to 20 items
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": items_query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200 or "errors" in response.json():
            # Try a simpler fallback query if the first one fails
            fallback_query = """
            query($projectId: ID!, $first: Int!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  items(first: $first) {
                    nodes {
                      id
                      content {
                        __typename
                        ... on Issue {
                          title
                          number
                          repository {
                            name
                            owner {
                              login
                            }
                          }
                          state
                        }
                        ... on PullRequest {
                          title
                          number
                          repository {
                            name
                            owner {
                              login
                            }
                          }
                          state
                        }
                        ... on DraftIssue {
                          title
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": fallback_query, "variables": variables},
                headers=headers
            )
        
        if response.status_code != 200:
            return f"Error fetching project items: {response.status_code} - {response.text}"
        
        result = response.json()
        
        # Debug the response
        if "errors" in result:
            return f"GraphQL Error when fetching items: {result['errors'][0].get('message', 'Unknown error')}"
        
        # Process the items
        if not result.get("data"):
            return f"No data returned when fetching project items"
            
        if not result["data"].get("node"):
            return f"No node data returned when fetching project items"
            
        if not result["data"]["node"].get("items"):
            return f"No items data returned when fetching project items"
            
        if not result["data"]["node"]["items"].get("nodes"):
            return f"No nodes data returned when fetching project items"
            
        items = result["data"]["node"]["items"]["nodes"]
        
        if not items:
            return f"No items found in project '{project_title}'"
        
        # Format the response
        response_text = f"📋 Items in Project '{project_title}':\n\n"
        
        for i, item in enumerate(items):
            try:
                content = item.get("content", {}) or {}
                
                # Get status from field values
                status = "No status"
                field_values = item.get("fieldValues", {})
                if field_values and field_values.get("nodes"):
                    for field_value in field_values["nodes"]:
                        if field_value and field_value.get("field") and field_value["field"].get("name") == "Status" and field_value.get("name"):
                            status = field_value["name"]
                        # Handle text fields that might contain status
                        elif field_value and field_value.get("__typename") == "ProjectV2ItemFieldTextValue" and field_value.get("field") and field_value["field"].get("name") == "Status" and field_value.get("text"):
                            status = field_value["text"]
                
                if content:
                    if content.get("repository"):
                        # This is an issue or PR
                        repo_owner = content.get("repository", {}).get("owner", {}).get("login", "")
                        repo_name = content.get("repository", {}).get("name", "")
                        number = content.get("number", "")
                        title = content.get("title", "")
                        state = content.get("state", "")
                        
                        item_type = "Issue" if content.get("state") is not None else "PR"
                        state_emoji = "🟢" if state == "OPEN" else "🔴"
                        
                        response_text += f"{i+1}. {state_emoji} {item_type} #{number}: {title}\n"
                        response_text += f"   Repo: {repo_owner}/{repo_name}\n"
                        response_text += f"   Status: {status}\n\n"
                    else:
                        # This is a draft issue
                        title = content.get("title", "")
                        response_text += f"{i+1}. 📝 Draft: {title}\n"
                        response_text += f"   Status: {status}\n\n"
                else:
                    response_text += f"{i+1}. Unknown item type\n\n"
            except Exception as e:
                response_text += f"{i+1}. Error processing item: {str(e)}\n\n"
        
        response_text += f"\nView project: {project_url}"
        
        return response_text
    except Exception as e:
        import traceback
        return f"Error processing project items: {str(e)}\n\nTraceback: {traceback.format_exc()}"


def add_issue_to_project_graphql(token, project_owner, project_number, repo_owner, repo_name, issue_number):
    """
    Add an issue to a GitHub Project using GraphQL API.
    
    Args:
        token (str): GitHub token
        project_owner (str): Project owner (username or organization)
        project_number (str): Project number
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (int): Issue number
        
    Returns:
        str: Success message or error
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # First, check if the owner is a user or organization
    rest_api_url = f"https://api.github.com/users/{project_owner}"
    response = requests.get(rest_api_url, headers=headers)
    
    if response.status_code != 200:
        return f"Error: Could not find user or organization '{project_owner}'. Please check the project owner name."
    
    user_data = response.json()
    is_org = user_data.get("type") == "Organization"
    
    # Construct the correct project URL for display
    if is_org:
        project_url = f"https://github.com/orgs/{project_owner}/projects/{project_number}"
        project_query = """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) {
              id
            }
          }
        }
        """
    else:
        project_url = f"https://github.com/users/{project_owner}/projects/{project_number}"
        project_query = """
        query($owner: String!, $number: Int!) {
          user(login: $owner) {
            projectV2(number: $number) {
              id
            }
          }
        }
        """
    
    project_variables = {
        "owner": project_owner,
        "number": int(project_number)
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": project_query, "variables": project_variables},
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Error accessing project: {response.status_code} - {response.text}"
    
    result = response.json()
    
    if "errors" in result:
        error_msg = result['errors'][0].get('message', 'Unknown error')
        return f"GraphQL Error: {error_msg}\n\nPlease verify your project settings with 'Debug project' command.\nProject URL should be: {project_url}"
    
    # Check if project exists based on owner type
    project_id = None
    if is_org:
        if result.get("data", {}).get("organization", {}).get("projectV2", {}).get("id"):
            project_id = result["data"]["organization"]["projectV2"]["id"]
    else:
        if result.get("data", {}).get("user") and result["data"]["user"].get("projectV2"):
            project_id = result["data"]["user"]["projectV2"]["id"]
    
    if not project_id:
        return f"Project not found: {project_url}\nPlease check the project owner and number."
    
    # Get the issue ID
    issue_query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          id
        }
      }
    }
    """
    
    issue_variables = {
        "owner": repo_owner,
        "name": repo_name,
        "number": issue_number
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": issue_query, "variables": issue_variables},
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Error accessing issue: {response.status_code} - {response.text}"
    
    result = response.json()
    
    if "errors" in result:
        error_msg = result['errors'][0].get('message', 'Unknown error')
        return f"GraphQL Error: {error_msg}"
    
    issue_id = result.get("data", {}).get("repository", {}).get("issue", {}).get("id")
    
    if not issue_id:
        return f"Issue not found: {repo_owner}/{repo_name}#{issue_number}"
    
    # Add the issue to the project
    add_mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item {
          id
        }
      }
    }
    """
    
    add_variables = {
        "projectId": project_id,
        "contentId": issue_id
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": add_mutation, "variables": add_variables},
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Error adding issue to project: {response.status_code} - {response.text}"
    
    result = response.json()
    
    if result.get("errors"):
        return f"Error adding issue to project: {result['errors'][0].get('message', 'Unknown error')}"
    
    if result.get("data", {}).get("addProjectV2ItemById", {}).get("item", {}).get("id"):
        return f"✅ Issue successfully added to project: {project_url}"
    
    return "Issue could not be added to the project for an unknown reason"


def handle_list_org_repositories(github_client, org_name):
    """Handle listing repositories for a specific organization."""
    try:
        # Try direct access to the repository if we know the name
        if '/' in org_name:
            # This might be a full repo name
            try:
                repo = github_client.get_repo(org_name)
                return f"📚 Repository found:\n1. {repo.full_name} - {repo.description or 'No description'}"
            except GithubException:
                # If this fails, continue with organization search
                org_name = org_name.split('/')[0]  # Extract org name
        
        # Try to access a specific repository directly
        if org_name.lower() == "abhiabhijitorg":
            try:
                repo = github_client.get_repo("abhiabhijitorg/test_repo")
                return f"📚 Repository found:\n1. {repo.full_name} - {repo.description or 'No description'}"
            except GithubException as e:
                return f"Error accessing repository 'abhiabhijitorg/test_repo': {str(e)}"
        
        # Get the organization
        try:
            org = github_client.get_organization(org_name)
        except GithubException as e:
            return f"Error accessing organization '{org_name}': {str(e)}\n\nTry using a direct repository URL instead, like: List open issues in https://github.com/abhiabhijitorg/test_repo"
        
        # List organization's repositories
        try:
            repos = org.get_repos()
            
            if repos.totalCount == 0:
                # Try a different approach - search for repositories
                search_query = f"org:{org_name}"
                search_results = github_client.search_repositories(search_query)
                
                if search_results.totalCount > 0:
                    response = f"📚 Repositories found for organization '{org_name}' via search:\n"
                    for i, repo in enumerate(search_results[:20]):
                        response += f"{i+1}. {repo.full_name} - {repo.description or 'No description'}\n"
                    
                    if search_results.totalCount > 20:
                        response += f"\n... and {search_results.totalCount - 20} more repositories."
                    
                    return response
                else:
                    return f"No repositories found in organization '{org_name}'. You may need to check your GitHub token permissions or try accessing the repository directly with: List open issues in https://github.com/abhiabhijitorg/test_repo"
            
            response = f"📚 Repositories in organization '{org_name}':\n"
            for i, repo in enumerate(repos[:20]):  # Limit to 20 repos
                response += f"{i+1}. {repo.name} - {repo.description or 'No description'}\n"
            
            if repos.totalCount > 20:
                response += f"\n... and {repos.totalCount - 20} more repositories."
                
            return response
        except GithubException as e:
            return f"Error listing repositories for organization '{org_name}': {str(e)}"
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback: {traceback.format_exc()}"


def check_token_permissions(token):
    """Check GitHub token permissions and provide detailed information."""
    if not token:
        return "Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable."
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get basic user info
        user_response = requests.get("https://api.github.com/user", headers=headers)
        if user_response.status_code != 200:
            return f"Error: Cannot access GitHub API with this token. Status code: {user_response.status_code}"
        
        user_data = user_response.json()
        username = user_data.get("login", "Unknown")
        
        # Check if token has repo scope
        repo_response = requests.get("https://api.github.com/user/repos?per_page=1", headers=headers)
        has_repo = repo_response.status_code == 200
        
        # Check if token has read:org scope
        org_response = requests.get("https://api.github.com/user/orgs", headers=headers)
        has_read_org = org_response.status_code == 200
        
        # Check if token has project scope (indirect check)
        project_response = requests.get("https://api.github.com/user/projects", headers=headers)
        has_project_scope = project_response.status_code == 200
        
        # Try to get organizations
        orgs = []
        if has_read_org:
            orgs_data = org_response.json()
            orgs = [org.get("login") for org in orgs_data if org.get("login")]
        
        response = f"""
GitHub Token Information:
- Username: {username}
- Token Permissions:
  - repo: {'✅' if has_repo else '❌'} (Required for repository access)
  - read:org: {'✅' if has_read_org else '❌'} (Required for organization access)
  - project: {'✅' if has_project_scope else '❌'} (Required for project access)

"""
        
        if orgs:
            response += "Organizations you have access to:\n"
            for org in orgs:
                response += f"- {org}\n"
        else:
            response += "No organizations found or no access to organizations.\n"
        
        if not (has_repo and has_read_org and has_project_scope):
            response += """
⚠️ Your token is missing some required permissions.

To fix this:
1. Create a new Personal Access Token with these scopes: repo, read:org, project
2. Go to: https://github.com/settings/tokens
3. Update your .env file with the new token
4. Restart the application
"""
        
        return response
    except Exception as e:
        return f"Error checking token permissions: {str(e)}"


def query_project_explorer_format(token, owner, project_number):
    """
    Query GitHub Project using the GitHub API v4 explorer format.
    This uses a simpler query that should work with most project configurations.
    
    Args:
        token (str): GitHub token
        owner (str): Project owner (username or organization)
        project_number (str): Project number
        
    Returns:
        str: Formatted response with project information
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # First, check if the owner is a user or organization
        rest_api_url = f"https://api.github.com/users/{owner}"
        response = requests.get(rest_api_url, headers=headers)
        
        if response.status_code != 200:
            return f"Error: Could not find user or organization '{owner}'. Please check the project owner name."
        
        user_data = response.json()
        is_org = user_data.get("type") == "Organization"
        
        # Construct the correct project URL for display
        if is_org:
            project_url = f"https://github.com/orgs/{owner}/projects/{project_number}"
            
            # Query for organization project
            query = """
            query {
              organization(login: "%s") {
                projectV2(number: %s) {
                  id
                  title
                  url
                  items(first: 20) {
                    nodes {
                      id
                      type
                      content {
                        ... on Issue {
                          title
                          number
                          url
                          repository {
                            name
                          }
                        }
                        ... on PullRequest {
                          title
                          number
                          url
                        }
                      }
                    }
                  }
                }
              }
            }
            """ % (owner, project_number)
            
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query},
                headers=headers
            )
            
            if response.status_code != 200:
                return f"Error accessing project: {response.status_code} - {response.text}"
            
            result = response.json()
            
            if "errors" in result:
                error_msg = result['errors'][0].get('message', 'Unknown error')
                return f"GraphQL Error: {error_msg}"
            
            if not result.get("data", {}).get("organization", {}).get("projectV2"):
                return f"Project not found: {project_url}"
            
            project = result["data"]["organization"]["projectV2"]
            
        else:
            project_url = f"https://github.com/users/{owner}/projects/{project_number}"
            
            # Query for user project
            query = """
            query {
              user(login: "%s") {
                projectV2(number: %s) {
                  id
                  title
                  url
                  items(first: 20) {
                    nodes {
                      id
                      type
                      content {
                        ... on Issue {
                          title
                          number
                          url
                          repository {
                            name
                          }
                        }
                        ... on PullRequest {
                          title
                          number
                          url
                        }
                      }
                    }
                  }
                }
              }
            }
            """ % (owner, project_number)
            
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query},
                headers=headers
            )
            
            if response.status_code != 200:
                return f"Error accessing project: {response.status_code} - {response.text}"
            
            result = response.json()
            
            if "errors" in result:
                error_msg = result['errors'][0].get('message', 'Unknown error')
                return f"GraphQL Error: {error_msg}"
            
            if not result.get("data", {}).get("user", {}).get("projectV2"):
                return f"Project not found: {project_url}"
            
            project = result["data"]["user"]["projectV2"]
        
        # Process the project information
        project_title = project.get("title", "Unknown")
        project_url = project.get("url", project_url)
        items = project.get("items", {}).get("nodes", [])
        
        if not items:
            return f"No items found in project '{project_title}' at {project_url}"
        
        # Format the response
        response_text = f"📋 Items in Project '{project_title}':\n\n"
        
        for i, item in enumerate(items):
            content = item.get("content")
            if not content:
                continue
                
            title = content.get("title", "No title")
            number = content.get("number", "")
            url = content.get("url", "")
            repo_name = content.get("repository", {}).get("name", "")
            
            item_type = "Issue" if "Issue" in str(content) else "PR" if "PullRequest" in str(content) else "Item"
            
            response_text += f"{i+1}. {item_type} #{number}: {title}\n"
            if repo_name:
                response_text += f"   Repo: {repo_name}\n"
            if url:
                response_text += f"   URL: {url}\n"
            response_text += "\n"
        
        response_text += f"\nView project: {project_url}"
        
        return response_text
    except Exception as e:
        import traceback
        return f"Error querying project: {str(e)}\n\nTraceback: {traceback.format_exc()}"


def add_issue_to_project(token, project_owner, project_number, repo_owner, repo_name, issue_number):
    """
    Add an issue to a GitHub Project.
    
    Args:
        token (str): GitHub token
        project_owner (str): Project owner (username or organization)
        project_number (str): Project number
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (str): Issue number
        
    Returns:
        str: Success or error message
    """
    try:
        # First, get the project ID
        project_id = get_project_id(token, project_owner, project_number)
        if not project_id.startswith("PVT_"):
            return project_id  # This is an error message
        
        # Get the issue node ID
        issue_node_id = get_issue_node_id(token, repo_owner, repo_name, issue_number)
        if not issue_node_id.startswith("I_"):
            return issue_node_id  # This is an error message
        
        # Add the issue to the project
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        query = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id,
            "contentId": issue_node_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error adding issue to project: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        if result.get("data", {}).get("addProjectV2ItemById", {}).get("item", {}).get("id"):
            # Construct project URL
            if project_owner.lower() == repo_owner.lower():
                project_type = "users"
            else:
                # Check if project owner is an organization
                org_check_url = f"https://api.github.com/users/{project_owner}"
                org_response = requests.get(org_check_url, headers=headers)
                if org_response.status_code == 200 and org_response.json().get("type") == "Organization":
                    project_type = "orgs"
                else:
                    project_type = "users"
            
            project_url = f"https://github.com/{project_type}/{project_owner}/projects/{project_number}"
            issue_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
            
            return f"✅ Successfully added issue #{issue_number} from {repo_owner}/{repo_name} to project!\n\nIssue: {issue_url}\nProject: {project_url}"
        else:
            return "Failed to add issue to project. No item ID returned."
    except Exception as e:
        import traceback
        return f"Error adding issue to project: {str(e)}\n\nTraceback: {traceback.format_exc()}"


def get_project_id(token, owner, project_number):
    """Get the project node ID using GraphQL."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # First, check if the owner is a user or organization
    rest_api_url = f"https://api.github.com/users/{owner}"
    response = requests.get(rest_api_url, headers=headers)
    
    if response.status_code != 200:
        return f"Error: Could not find user or organization '{owner}'. Please check the project owner name."
    
    user_data = response.json()
    is_org = user_data.get("type") == "Organization"
    
    if is_org:
        query = """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) {
              id
            }
          }
        }
        """
    else:
        query = """
        query($owner: String!, $number: Int!) {
          user(login: $owner) {
            projectV2(number: $number) {
              id
            }
          }
        }
        """
    
    variables = {
        "owner": owner,
        "number": int(project_number)
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Error accessing project: {response.status_code} - {response.text}"
    
    result = response.json()
    
    if "errors" in result:
        error_msg = result['errors'][0].get('message', 'Unknown error')
        return f"GraphQL Error: {error_msg}"
    
    project_id = None
    if is_org:
        if result.get("data", {}).get("organization") and result["data"]["organization"].get("projectV2"):
            project_id = result["data"]["organization"]["projectV2"]["id"]
    else:
        if result.get("data", {}).get("user") and result["data"]["user"].get("projectV2"):
            project_id = result["data"]["user"]["projectV2"]["id"]
    
    if not project_id:
        return f"Project not found: {owner}/{project_number}"
    
    return project_id


def get_issue_node_id(token, owner, repo, issue_number):
    """Get the issue node ID using GraphQL."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          id
        }
      }
    }
    """
    
    variables = {
        "owner": owner,
        "repo": repo,
        "number": int(issue_number)
    }
    
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    if response.status_code != 200:
        return f"Error accessing issue: {response.status_code} - {response.text}"
    
    result = response.json()
    
    if "errors" in result:
        error_msg = result['errors'][0].get('message', 'Unknown error')
        return f"GraphQL Error: {error_msg}"
    
    if not result.get("data", {}).get("repository", {}).get("issue", {}).get("id"):
        return f"Issue not found: {owner}/{repo}#{issue_number}"
    
    return result["data"]["repository"]["issue"]["id"]


def update_issue_status_rest(github_client, repo_owner, repo_name, issue_number, new_status):
    """
    Update an issue's status using the GitHub REST API.
    
    Args:
        github_client: PyGithub client instance
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (str): Issue number
        new_status (str): New status value
        
    Returns:
        str: Success or error message
    """
    try:
        # Get the repository
        repo = github_client.get_repo(f"{repo_owner}/{repo_name}")
        
        # Get the issue
        issue = repo.get_issue(int(issue_number))
        
        # Normalize the status name
        normalized_status = new_status.lower().strip()
        
        # Map common status names to GitHub issue states
        if normalized_status in ["closed", "done", "completed", "finish", "finished"]:
            # Close the issue
            issue.edit(state="closed", state_reason="completed")
            status_message = "closed (completed)"
        elif normalized_status in ["wontfix", "won't fix", "wont-fix", "not fixing", "abandoned"]:
            # Close the issue as not planned
            issue.edit(state="closed", state_reason="not_planned")
            status_message = "closed (not planned)"
        elif normalized_status in ["open", "active", "todo", "to do", "to-do", "backlog", "new", "inprogress", "in progress", "in-progress", "review", "in review"]:
            # Reopen the issue if it was closed
            issue.edit(state="open")
            
            # Add a label for the status if it's more specific than just "open"
            if normalized_status not in ["open", "active"]:
                # Try to find or create an appropriate label
                label_name = None
                if normalized_status in ["todo", "to do", "to-do", "backlog", "new"]:
                    label_name = "status: todo"
                elif normalized_status in ["inprogress", "in progress", "in-progress"]:
                    label_name = "status: in progress"
                elif normalized_status in ["review", "in review"]:
                    label_name = "status: review"
                
                if label_name:
                    # Try to get the label, create it if it doesn't exist
                    try:
                        repo.get_label(label_name)
                    except:
                        # Create the label with appropriate color
                        if "todo" in label_name:
                            repo.create_label(label_name, "0E8A16", "To do items")
                        elif "progress" in label_name:
                            repo.create_label(label_name, "FFA500", "In progress items")
                        elif "review" in label_name:
                            repo.create_label(label_name, "1D76DB", "Items under review")
                    
                    # Add the label to the issue
                    issue.add_to_labels(label_name)
                    status_message = f"open with label '{label_name}'"
                else:
                    status_message = "open"
            else:
                status_message = "open"
        else:
            # For any other status, we'll add it as a label
            label_name = f"status: {normalized_status}"
            
            # Try to get the label, create it if it doesn't exist
            try:
                repo.get_label(label_name)
            except:
                # Create the label with a default color
                repo.create_label(label_name, "CCCCCC", f"Status: {new_status}")
            
            # Add the label to the issue
            issue.add_to_labels(label_name)
            status_message = f"updated with label '{label_name}'"
        
        # Return success message with links
        issue_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
        
        return f"✅ Successfully updated status of issue #{issue_number} to '{status_message}'!\n\nIssue: {issue_url}"
    except github.GithubException as e:
        if e.status == 404:
            return f"Error: Issue #{issue_number} not found in {repo_owner}/{repo_name}. Please check the issue number and repository name."
        elif e.status == 403:
            return f"Error: Permission denied. Your GitHub token may not have access to this repository or may not have permission to update issues."
        else:
            return f"GitHub API Error: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error updating issue status: {str(e)}"


def add_comment_to_issue(github_client, repo_owner, repo_name, issue_number, comment_text):
    """
    Add a comment to an issue in a GitHub repository.
    
    Args:
        github_client: PyGithub client instance
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (str): Issue number
        comment_text (str): Comment text
        
    Returns:
        str: Success or error message
    """
    try:
        # Get the repository
        repo = github_client.get_repo(f"{repo_owner}/{repo_name}")
        
        # Get the issue
        issue = repo.get_issue(int(issue_number))
        
        # Add the comment
        comment = issue.create_comment(comment_text)
        
        # Return success message with links
        issue_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
        comment_url = comment.html_url
        
        return f"✅ Successfully added comment to issue #{issue_number}!\n\nIssue: {issue_url}\nComment: {comment_url}"
    except github.GithubException as e:
        if e.status == 404:
            return f"Error: Issue #{issue_number} not found in {repo_owner}/{repo_name}. Please check the issue number and repository name."
        elif e.status == 403:
            return f"Error: Permission denied. Your GitHub token may not have access to this repository or may not have permission to comment on issues."
        else:
            return f"GitHub API Error: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error adding comment to issue: {str(e)}"


def update_issue_status_in_project(token, project_owner, project_number, repo_owner, repo_name, issue_number, new_status):
    """
    Update an issue's status in a GitHub Project using GraphQL.
    
    Args:
        token (str): GitHub token
        project_owner (str): Project owner (username or organization)
        project_number (str): Project number
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (str): Issue number
        new_status (str): New status value
        
    Returns:
        str: Success or error message
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Step 1: Get the project ID
        # First, check if the owner is a user or organization
        rest_api_url = f"https://api.github.com/users/{project_owner}"
        response = requests.get(rest_api_url, headers=headers)
        
        if response.status_code != 200:
            return f"Error: Could not find user or organization '{project_owner}'. Please check the project owner name."
        
        user_data = response.json()
        is_org = user_data.get("type") == "Organization"
        
        # Get the project ID using the correct query based on type
        if is_org:
            query = """
            query($owner: String!, $number: Int!) {
              organization(login: $owner) {
                projectV2(number: $number) {
                  id
                }
              }
            }
            """
        else:
            query = """
            query($owner: String!, $number: Int!) {
              user(login: $owner) {
                projectV2(number: $number) {
                  id
                }
              }
            }
            """
        
        variables = {
            "owner": project_owner,
            "number": int(project_number)
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error accessing project: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        project_id = None
        if is_org:
            if result.get("data", {}).get("organization") and result["data"]["organization"].get("projectV2"):
                project_id = result["data"]["organization"]["projectV2"]["id"]
        else:
            if result.get("data", {}).get("user") and result["data"]["user"].get("projectV2"):
                project_id = result["data"]["user"]["projectV2"]["id"]
        
        if not project_id:
            return f"Project not found: {project_owner}/{project_number}"
        
        # Step 2: Get the issue node ID
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $number) {
              id
            }
          }
        }
        """
        
        variables = {
            "owner": repo_owner,
            "repo": repo_name,
            "number": int(issue_number)
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error accessing issue: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        if not result.get("data", {}).get("repository", {}).get("issue", {}).get("id"):
            return f"Issue not found: {repo_owner}/{repo_name}#{issue_number}"
        
        issue_id = result["data"]["repository"]["issue"]["id"]
        
        # Step 3: Add the issue to the project if it's not already there
        add_mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """
        
        add_variables = {
            "projectId": project_id,
            "contentId": issue_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": add_mutation, "variables": add_variables},
            headers=headers
        )
        
        # We don't check for errors here because it might already be in the project
        
        # Step 4: Get the project item ID
        query = """
        query($projectId: ID!, $first: Int!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: $first) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      id
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id,
            "first": 100  # Limit to 100 items
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error fetching project items: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        items = result.get("data", {}).get("node", {}).get("items", {}).get("nodes", [])
        
        item_id = None
        for item in items:
            if item.get("content", {}) and item["content"].get("id") == issue_id:
                item_id = item["id"]
                break
        
        if not item_id:
            return f"Issue not found in project. Please add it to the project first."
        
        # Step 5: Get the status field ID
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error fetching project fields: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        fields = result.get("data", {}).get("node", {}).get("fields", {}).get("nodes", [])
        
        status_field = None
        status_options = []
        for field in fields:
            if field.get("name") and field["name"].lower() == "status":
                status_field = field
                status_options = field.get("options", [])
                break
        
        if not status_field:
            return "Status field not found in project. Please ensure your project has a Status field."
        
        status_field_id = status_field["id"]
        
        # Step 6: Find the status option ID
        # Normalize the status name for comparison
        normalized_status = new_status.lower().strip()
        
        # Common status name mappings
        status_mappings = {
            "todo": ["todo", "to do", "to-do", "backlog", "new"],
            "inprogress": ["inprogress", "in progress", "in-progress", "started", "working", "doing"],
            "done": ["done", "completed", "finished", "closed", "complete"],
            "review": ["review", "in review", "reviewing", "under review", "pr review"],
            "blocked": ["blocked", "on hold", "hold", "waiting", "blocked"]
        }
        
        status_option_id = None
        matched_status_name = None
        
        # Try exact match first
        for option in status_options:
            if option.get("name", "").lower() == normalized_status:
                status_option_id = option["id"]
                matched_status_name = option["name"]
                break
        
        # Try using status mappings
        if not status_option_id:
            for key, variations in status_mappings.items():
                if normalized_status in variations:
                    # Look for the canonical name or any variation
                    for option in status_options:
                        option_name = option.get("name", "").lower()
                        if option_name == key or option_name in variations:
                            status_option_id = option["id"]
                            matched_status_name = option["name"]
                            break
                    if status_option_id:
                        break
        
        # Try partial match
        if not status_option_id:
            for option in status_options:
                option_name = option.get("name", "").lower()
                if normalized_status in option_name or option_name in normalized_status:
                    status_option_id = option["id"]
                    matched_status_name = option["name"]
                    break
        
        if not status_option_id:
            # Return available options
            available_options = [option.get("name") for option in status_options if option.get("name")]
            return f"Status '{new_status}' not found. Available options: {', '.join(available_options)}"
        
        # Step 7: Update the status
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: {
              singleSelectOptionId: $optionId
            }
          }) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": status_field_id,
            "optionId": status_option_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": mutation, "variables": variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error updating issue status: {response.status_code} - {response.text}"
        
        result = response.json()
        
        if "errors" in result:
            error_msg = result['errors'][0].get('message', 'Unknown error')
            return f"GraphQL Error: {error_msg}"
        
        if result.get("data", {}).get("updateProjectV2ItemFieldValue", {}).get("projectV2Item", {}).get("id"):
            # Construct project URL
            if is_org:
                project_url = f"https://github.com/orgs/{project_owner}/projects/{project_number}"
            else:
                project_url = f"https://github.com/users/{project_owner}/projects/{project_number}"
            
            issue_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
            
            return f"✅ Successfully updated status of issue #{issue_number} to '{matched_status_name}' in project!\n\nIssue: {issue_url}\nProject: {project_url}"
        else:
            return "Failed to update issue status. No item ID returned."
    except Exception as e:
        import traceback
        return f"Error updating issue status: {str(e)}\n\nTraceback: {traceback.format_exc()}"

def assign_issue_to_user(github_client, repo_owner, repo_name, issue_number, assignee):
    """
    Assign an issue to a user.
    
    Args:
        github_client: PyGithub client instance
        repo_owner (str): Repository owner
        repo_name (str): Repository name
        issue_number (str): Issue number
        assignee (str): GitHub username to assign
        
    Returns:
        str: Success or error message
    """
    try:
        # Get the repository
        repo = github_client.get_repo(f"{repo_owner}/{repo_name}")
        
        # Get the issue
        issue = repo.get_issue(int(issue_number))
        
        # Check if the assignee exists
        try:
            github_client.get_user(assignee)
        except github.GithubException as e:
            if e.status == 404:
                return f"Error: User '{assignee}' not found. Please check the username."
            else:
                raise
        
        # Assign the issue
        issue.add_to_assignees(assignee)
        
        # Return success message with links
        issue_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
        
        return f"✅ Successfully assigned issue #{issue_number} to @{assignee}!\n\nIssue: {issue_url}"
    except github.GithubException as e:
        if e.status == 404:
            return f"Error: Issue #{issue_number} not found in {repo_owner}/{repo_name}. Please check the issue number and repository name."
        elif e.status == 403:
            return f"Error: Permission denied. Your GitHub token may not have access to this repository or may not have permission to assign issues."
        elif e.status == 422:
            return f"Error: Cannot assign user '{assignee}'. The user may not have permission to be assigned to this repository."
        else:
            return f"GitHub API Error: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error assigning issue: {str(e)}"


# Add this code at the end of the file
if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Test GitHub Scrum Master functions without Slack')
    parser.add_argument('--command', '-c', type=str, help='Command to test (or enter "interactive" for interactive mode)')
    args = parser.parse_args()
    
    # Check if .env file is loaded
    if not os.environ.get("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN not found. Make sure your .env file is properly configured.")
    
    if args.command:
        if args.command.lower() == "interactive":
            print("=== GitHub Scrum Master Interactive Mode ===")
            print("Type 'exit' or 'quit' to end the session")
            print("Example commands:")
            print("  - List repositories")
            print("  - Create issue in username/repo titled Bug in login with description Users cannot log in")
            print("  - List open issues in username/repo")
            print("  - Check project status for username/repo")
            print("  - List project items")
            print()
            
            while True:
                user_input = input("Enter command: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                print("\nProcessing...\n")
                response = github_scrum_master(user_input)
                print(f"Response:\n{response}\n")
        else:
            # Process the single command
            response = github_scrum_master(args.command)
            print(response)
    else:
        # No command provided, show help
        print("Please provide a command to test using the --command or -c flag.")
        print("Examples:")
        print("  python functions.py -c \"List repositories\"")
        print("  python functions.py -c \"Create issue in username/repo titled Bug in login with description Users cannot log in\"")
        print("  python functions.py -c \"interactive\"  # For interactive mode")