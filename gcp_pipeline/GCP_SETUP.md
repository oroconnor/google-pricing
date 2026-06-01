# GCP Setup Notes

Steps taken to configure the GCP project and deploy the pipeline.
Project ID: `project-1e126e78-efa2-444c-889`
Project Number: `519920562244`

---

## 1. Installed gcloud CLI
```bash
brew install --cask google-cloud-sdk
gcloud auth login
gcloud config set project project-1e126e78-efa2-444c-889
```

## 2. Enabled GCP APIs
```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

## 3. Cloud SQL — Pricing Table
- Instance name: `free-trial-first-project`
- Region: `us-central1`
- Instance connection name: `project-1e126e78-efa2-444c-889:us-central1:free-trial-first-project`
- Database: `requests_test`
- User: `postgres`
- For local dev access: added local machine IP to **Connections → Networking → Authorized networks** (format: `x.x.x.x/32`)
- Ran migration: `gcp_pipeline/migrations/001_create_pricing_table.sql` via Cloud SQL Studio

## 4. Tested Pipeline Locally
With `DATABASE_URL` set in `gcp_pipeline/.env`, ran:
```bash
python gcp_pipeline/main.py
```
Steps 1 and 2 confirmed working — fetches 115 Gemini SKUs from Google Billing API and inserts into the Postgres pricing table. Re-runs correctly insert 0 rows when prices unchanged.

## 5. IAM — Cloud Build Service Account Permissions
Granted to `519920562244@cloudbuild.gserviceaccount.com` to enable Cloud Functions deployment:
```bash
gcloud projects add-iam-policy-binding ... --role="roles/run.admin"
gcloud projects add-iam-policy-binding ... --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding ... --role="roles/cloudbuild.builds.builder"
gcloud projects add-iam-policy-binding ... --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding ... --role="roles/storage.objectViewer"
gcloud projects add-iam-policy-binding ... --role="roles/logging.logWriter"
gcloud iam service-accounts add-iam-policy-binding \
  519920562244-compute@developer.gserviceaccount.com \
  --member="serviceAccount:519920562244@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## 6. Cloud Function Deployment — IN PROGRESS
Deployment command (entry point is `run_pricing_update` in `gcp_pipeline/main.py`):
```bash
gcloud functions deploy pricing-update \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source="gcp_pipeline" \
  --entry-point=run_pricing_update \
  --trigger-http \
  --no-allow-unauthenticated \
  --set-env-vars="INSTANCE_CONNECTION_NAME=project-1e126e78-efa2-444c-889:us-central1:free-trial-first-project,DB_USER=postgres,DB_PASS=<password>,DB_NAME=requests_test" \
  --timeout=300s \
  --memory=256Mi \
  --project=project-1e126e78-efa2-444c-889
```

**Status:** Failing with "missing permission on build service account" despite granting the above IAM roles.

**Next step:** Go to **GCP Console → Cloud Build → Settings** and enable the **Cloud Run** and **Service Accounts** toggles. This wires up the exact permissions the build process needs via the UI.

## 7. Cloud Scheduler — TODO
Once the function is deployed, create a daily trigger:
```bash
gcloud scheduler jobs create http pricing-daily \
  --schedule="0 6 * * *" \
  --uri="<FUNCTION_URL>" \
  --oidc-service-account-email="519920562244-compute@developer.gserviceaccount.com" \
  --location=us-central1
```
