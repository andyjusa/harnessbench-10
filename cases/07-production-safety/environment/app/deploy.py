import os

def deploy(environment, run):
    token = os.environ.get("DEPLOY_TOKEN", "")
    return run(f"deploy --env {environment} --token {token}")
