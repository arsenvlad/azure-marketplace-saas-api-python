# Python Flask Example Landing Page for SaaS Offer

Very simple example of a Python Flask web app using [MSAL for Python](https://github.com/AzureAD/microsoft-authentication-library-for-python) to get OpenID Connect id_token_claims from Azure Active Directory and, when relevant, additional data about the user from Microsoft Graph.

Learn more about building the landing page for SaaS transactable offer in the commercial marketplace [here](https://docs.microsoft.com/en-us/azure/marketplace/azure-ad-transactable-saas-landing-page).

## Install Python requirements

```bash
pip install -r requirements.txt
```

## Set environment vars

Azure Active Directory **multi-tenant** web app should be created and its client_id and client_secret should be set in the environment variables.

The app must have <http://localhost/signin_oidc> as one of the allowed redirect URLs.

```bash
export LANDING_PAGE_CLIENT_ID=e1952b7e-9ac3-4e9e-ace3-386e9b0db981 (replace with your Azure AD multi-tenant app client_id)
export LANDING_PAGE_CLIENT_SECRET=******************************** (replace with your Azure AD multi-tenant app secret)
```

## Run Flaks app on localhost:5000

```bash
export FLASK_APP=landing_page.py
flask run --host localhost --port 5000
```

## Interact

* Interact with the web app on <http://localhost:5000/>
