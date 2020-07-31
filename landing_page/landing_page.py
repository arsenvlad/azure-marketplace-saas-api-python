import os
import uuid
import json
import requests
import msal
from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session

# ======================================================================
# Multi-tenant Azure Active Directory application configuration
AUTHORITY = "https://login.microsoftonline.com/common/"
SCOPES = ["User.Read"]
CLIENT_ID = os.getenv("LANDING_PAGE_CLIENT_ID")
if not CLIENT_ID:
    raise ValueError("LANDING_PAGE_CLIENT_ID environment variable is undefined")
CLIENT_SECRET = os.getenv("LANDING_PAGE_CLIENT_SECRET")
if not CLIENT_SECRET:
    raise ValueError("LANDING_PAGE_CLIENT_SECRET environment variable is undefined")
MICROSOFT_GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0/me?$select=id,mail,givenName,surname,companyName,jobTitle,userPrincipalName"
# ======================================================================

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = str(uuid.uuid4())
Session(app)

msal_app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)

@app.route("/")
def index():
    # If user does not yet have a landing page session
    if not session.get("user"):
        # Random state value for OAuth2 authorization-code flow
        session["state"] = str(uuid.uuid4())
        # Use MSAL to generate Azure AD authorization URL and redirect the user there
        auth_url = msal_app.get_authorization_request_url(SCOPES, state=session["state"], redirect_uri=url_for("signin_oidc", _external=True), prompt="select_account")
        return redirect(auth_url)
    else:
        # Output what we know about the user's session from the id_token_claims
        claims = session.get("user")
        html_output = """<a href='logout'>Logout</a><br><br>\n
                      <h2>id_token</h2>
                      Tenant={tid}<br>\n
                      User id across applications (oid)={oid}<br>\n
                      User id for this application (sub)={sub}<br>\n
                      name={name}<br>\n
                      preferred_username={preferred_username}<br>\n
                      email={email}<br>\n""".format(
                          tid=claims["tid"],
                          oid=claims["oid"],
                          sub=claims["sub"],
                          name=claims["name"],
                          preferred_username=claims["preferred_username"],
                          email="" if "email" not in claims else claims["email"])
        # Optionally, try to get additional info from Microsoft Graph
        graph_data = getMicrosoftGraphData()
        if graph_data:
            html_output = html_output + "<br>\n<h2>Microsoft Graph</h2>\n" + json.dumps(graph_data)
        return html_output

@app.route("/signin_oidc")
def signin_oidc():
    # Check state value that was round-tripped from Azure AD
    if request.args.get("state") != session.get("state"):
        return "Error: invalid state parameter value"
    # Check if request has any other errors
    if "error" in request.args:
        return "Error: " + json.dumps(request.args)
    if request.args.get("code"):
        # Make backend call to Azure AD to exchange the "code" for access_token, id_token, and id_token_claims
        result = msal_app.acquire_token_by_authorization_code(request.args["code"], scopes=SCOPES, redirect_uri=url_for("signin_oidc", _external=True))
        if "error" in result:
            return "Error: " + json.dumps(result)
        # Store the full response in the user session
        session["user"] = result["id_token_claims"]
        # Redirect to landing page
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    if not session.get("user"):
        # User does not have landing page session
        return "Logged out...<br><br>Go to <a href='/'>landing page</a>."
    else:
        # Clear landing page session
        session.clear()
        # Redirect use to Azure AD to logout there too
        return redirect(AUTHORITY + "oauth2/v2.0/logout?post_logout_redirect_uri=" + url_for("logout", _external=True))

def getMicrosoftGraphData():
    graph_data = None
    user = session.get("user")
    # Microsoft Graph will not provide more information than already available in id_token for Microsoft Accounts
    if user["tid"] == "9188040d-6c67-4c5b-b112-36a304b66dad":
        return graph_data
    # MSAL caches previously logged in accounts using home_account_id as key
    home_account_id = user["oid"] + "." + user["tid"]
    html = "home_account_id = " + home_account_id
    for a in msal_app.get_accounts():
        if a["home_account_id"] == home_account_id:
            result = msal_app.acquire_token_silent(SCOPES, account=a)
            graph_data = requests.get(MICROSOFT_GRAPH_ENDPOINT, headers = {"Authorization": "Bearer " + result["access_token"]}).json()
    return graph_data

if __name__ == "__main__":
    # Run specifically on localhost so that the redirect_url matches one registered for the app in Azure AD 
    # (e.g. http://localhost/signin_oidc since port is optional for localhost in AAD)
    app.run(host="localhost", port=5000)
