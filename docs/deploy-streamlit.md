# Deploy OpsControl to Streamlit Community Cloud

## Target

Desired public URL: https://opscontrol.streamlit.app/

## Steps

1. Open https://share.streamlit.io/ and sign in with the GitHub account that owns `sechan9999/OpsControl`.
2. Select **Create app**.
3. Choose repository `sechan9999/OpsControl`, branch `main`, and file path `streamlit_app.py`.
4. Name the app `opscontrol` if the name is available; this produces the target URL above.
5. Deploy. Streamlit installs `requirements.txt` automatically.
6. After the app is live, open it in an incognito window, click **Reset desk**, replay the storm, and complete the README's judge test path.

## Secrets

No secrets are needed for the public deterministic demo.

To enable optional live GPT-5.6 triage in a private environment, add these Streamlit secrets or environment variables:

```toml
OPSCONTROL_DEMO_MODE = "0"
OPSCONTROL_USE_OPENAI = "1"
OPENAI_API_KEY = "..."
OPSCONTROL_MODEL = "gpt-5.6"
```

Do not enable live mode for the judge demo unless it has been tested separately. The deterministic path is the recommended submission configuration.