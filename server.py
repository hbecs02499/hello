from flask import Flask, render_template, request, redirect, url_for
import os
import subprocess
import git
import time
from threading import Thread

app = Flask(__name__)
projects = {}

def build_project(repo_path, project_name):
    try:
        # Run the make command
        result = subprocess.run(['make'], cwd=repo_path, capture_output=True, text=True)
        if result.returncode == 0:
            # Save the artifact
            artifact_path = os.path.join('build/artifacts', f"{project_name}.bin")
            with open(artifact_path, 'wb') as f:
                f.write(result.stdout.encode())
            return "Success"
        else:
            # Log the error
            log_path = os.path.join('build/logs', f"{project_name}.log")
            with open(log_path, 'w') as f:
                f.write(result.stderr)
            return "Failed"
    except Exception as e:
        return f"Error: {str(e)}"

def periodic_builds():
    while True:
        for project_name, repo_info in projects.items():
            repo = repo_info['repo']
            repo.remotes.origin.pull()  # Fetch new commits
            status = build_project(repo_info['path'], project_name)
            repo_info['status'] = status
        time.sleep(60)  # Check every minute

@app.route('/')
def index():
    return render_template('index.html', projects=projects)

@app.route('/register', methods=['POST'])
def register():
    project_name = request.form['project_name']
    repo_url = request.form['repo_url']
    repo_path = os.path.join('build/repos', project_name)

    if not os.path.exists(repo_path):
        os.makedirs(repo_path)
        repo = git.Repo.clone_from(repo_url, repo_path)
        projects[project_name] = {'repo': repo, 'path': repo_path, 'status': 'Not built'}
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Start periodic build thread
    Thread(target=periodic_builds, daemon=True).start()
    app.run(debug=True)
