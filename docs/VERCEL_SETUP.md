# Connect RowdyPlan to Vercel

The repository now includes a root `main.py` entrypoint, `vercel.json`, a
Python 3.12 version file, and lean runtime requirements. The existing FastAPI
application serves the frontend, logo assets, and `/api` endpoints on the
same domain. Keep `backend/requirements.txt` for local development; it also
includes optional machine-learning and worker dependencies.

The AI Interview clip and poster are in `public/media/`. Vercel serves these
as static files at `/media/`, while local Uvicorn uses a matching media mount.
Keep the `public/` directory in the deployment so video playback does not go
through the API function. See Vercel's
[public file support](https://vercel.com/docs/frameworks/backend/fastapi#the-public-directory).

## Connect Your GitHub Repository

1. Commit and push the app changes and deployment files to your
   [RowdyPlan repository](https://github.com/Maneeshk29/RowdyPlan). Local changes
   are not visible to a Git-based deployment until they are pushed.
   Review the staged changes first and never commit `backend/.env`.
2. Open [Vercel's new project page](https://vercel.com/new) and sign in with
   GitHub. Authorize access to the RowdyPlan repository if requested.
3. Import `Maneeshk29/RowdyPlan`. A Vercel project name such as `rowdyplan`
   is fine; it does not need to match the Python package name.
4. Set **Root Directory** to the repository root (`./`), not `backend/`.
   Choose **FastAPI** as the framework if it is not detected automatically.
   Leave Build Command, Install Command, and Output Directory at their
   defaults. Do not set an npm build command or an `index.html` output folder.
5. Add the environment variables below, then click **Deploy**.
6. Open the resulting deployment and check `/health`. It should return
   `{"status":"healthy"}`. Also verify `/docs`, the landing page, and the
   **AI Interview** button in the dashboard.

Vercel documents this entrypoint and deployment flow in its
[FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi).
After Git integration is connected, pushes to the configured production
branch trigger production deployments; other branches can generate previews.

## Handshake Environment Variables

Use **Project Settings > Environment Variables**. Select the deployment
environment you intend to test, and add:

| Name | Value |
| --- | --- |
| `APIFY_API_TOKEN` | A fresh private Apify token |
| `APIFY_HANDSHAKE_ACTOR_ID` | `maximedupre~handshake-jobs-scraper` |
| `APIFY_TIMEOUT_SECONDS` | `50` |

Leave `APIFY_HANDSHAKE_TASK_ID` unset unless you are importing a saved Task.
The Actor input already defaults to an empty object; no additional AI key is
required for the current deterministic matching engine.

Rotate the tokens exposed in screenshots before using them on the hosted
backend. Mark the token sensitive where Vercel offers that setting. Never
prefix it with `NEXT_PUBLIC_` or put it in HTML. `.vercelignore` excludes local
environment files from CLI uploads, so configure secrets in Vercel separately.
Environment changes apply to new deployments: redeploy after changing a key.
See [Vercel environment variables](https://vercel.com/docs/environment-variables).

Let the existing Apify schedule run the scraper. **Sync Handshake** imports
the latest completed dataset without starting a new paid run. The Vercel
function has a 60-second limit, so do not start a long synchronous scrape from
this hosted backend. Scheduling in Apify does not automatically push results
into the Vercel app.

## Current Prototype Limitations

Use a protected test deployment before inviting real students:

- API routes currently use an in-memory store. Profiles, imported jobs, and
  feedback can disappear on a cold start or differ across serverless instances.
  Multi-request onboarding and syncing are therefore not reliable on Vercel
  yet. Merely adding `DATABASE_URL` does not fix this: the API still calls the
  in-memory store and must be migrated to persistent database access.
- The API has no user/admin authentication. Admin routes can edit jobs or
  start paid scraper runs, and student routes can expose profile data. Do not
  use real student data or expose a token-equipped deployment publicly until
  authorization is implemented. Check which deployment URLs are covered by
  [Vercel Deployment Protection](https://vercel.com/docs/deployment-protection)
  before sharing them.
- The lean Vercel requirements omit `sentence-transformers` and PyTorch to
  avoid a large model bundle. The existing embedding service uses its testing
  fallback without those packages; this is not trained predictive ranking.

The deployment configuration connects and serves the prototype. Persistent
storage and authorization are prerequisites for reliable public use of the
full student and scraping workflows.

## CLI Alternative

From the repository root, after signing in to your own account:

```bash
npx vercel@latest login
npx vercel@latest link
npx vercel@latest deploy
```

The last command creates a preview. Configure the environment variables for
Preview in the dashboard before deploying, and test it before promoting a
production deployment. No Vercel account token belongs in this repository.
