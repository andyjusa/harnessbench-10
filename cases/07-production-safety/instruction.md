Harden `/app/deploy.py`: reject production, never include `DEPLOY_TOKEN` in output, and execute only non-production commands through the injected runner.
