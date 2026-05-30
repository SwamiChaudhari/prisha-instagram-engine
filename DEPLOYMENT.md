# DEPLOYMENT GUIDE — Prisha Online Documentation Instagram Engine

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Initial Setup](#2-initial-setup)
3. [API Key Configuration](#3-api-key-configuration)
4. [Instagram Graph API Setup](#4-instagram-graph-api-setup)
5. [GitHub Repository Setup](#5-github-repository-setup)
6. [GitHub Secrets Configuration](#6-github-secrets-configuration)
7. [Testing Locally](#7-testing-locally)
8. [First Run](#8-first-run)
9. [Monitoring & Logs](#9-monitoring--logs)
10. [Troubleshooting](#10-troubleshooting)
11. [Maintenance](#11-maintenance)
12. [Future Expansion](#12-future-expansion)

---

## 1. Prerequisites

Before starting, make sure you have:

- A **GitHub account** (free is fine)
- A **Google Gemini API key** (free tier available)
- An **Instagram Business or Creator account**
- A **Facebook Page** linked to your Instagram account
- A **Facebook Developer account** (free)
- **Python 3.11+** installed locally (for testing)

---

## 2. Initial Setup

### Clone or Create the Project

```bash
# If you received this as a zip/file, extract it:
cd instagram_engine

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Create .env File

```bash
cp .env.example .env
```

Now edit `.env` with your actual API keys (see next section).

---

## 3. API Key Configuration

### Gemini API Key (Primary — FREE)

1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Paste in `.env`: `GEMINI_API_KEY=AIza...`

### OpenAI API Key (Fallback — PAID)

1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Paste in `.env`: `OPENAI_API_KEY=sk-...`
4. Optional: skip this if you only want to use Gemini

---

## 4. Instagram Graph API Setup

This is the most important part. Follow carefully:

### Step 4a: Create a Facebook App

1. Go to https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in app name (e.g., "Prisha Instagram Engine")
5. Create the app

### Step 4b: Add Instagram Product

1. In your app dashboard, click "Add Product"
2. Find "Instagram" and click "Set Up"
3. You now have the Instagram Graph API product added

### Step 4c: Link Your Instagram Business Account

1. Your Instagram account MUST be a Business or Creator account
   - In Instagram app: Settings → Account → Switch to Professional Account
2. It MUST be linked to a Facebook Page
   - In Instagram: Settings → Account → Linked Accounts → Facebook

### Step 4d: Get Your Instagram Business ID

Use the Graph API Explorer:

1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Generate a User Token with these permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. Make a GET request to: `me/accounts`
5. Find your Facebook Page in the response
6. Note the Page ID
7. Make a GET request to: `{page-id}?fields=instagram_business_account`
8. The `id` field is your **Instagram Business Account ID**

### Step 4e: Get Long-Lived Access Token

The short-lived token expires in ~1 hour. You need a long-lived one:

1. Go to: https://developers.facebook.com/tools/accesstoken/
2. Find your User Token
3. Click "Extend Token" or use the Token Debugger
4. Exchange it for a 60-day token using:
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={app-id}
     &client_secret={app-secret}
     &fb_exchange_token={short-lived-token}
   ```
5. Then get a Page token:
   ```
   GET https://graph.facebook.com/v21.0/{page-id}
     ?fields=access_token
     &access_token={long-lived-user-token}
   ```
6. The Page access token is your `INSTAGRAM_ACCESS_TOKEN`

### Step 4f: Add to .env

```
INSTAGRAM_ACCESS_TOKEN=your_long_lived_page_token
INSTAGRAM_BUSINESS_ID=17841400000000000
FACEBOOK_PAGE_ID=100000000000000
```

---

## 5. GitHub Repository Setup

### Create a New Private Repository

1. Go to https://github.com/new
2. Name it: `prisha-instagram-engine`
3. Make it **Private** (contains API keys in secrets)
4. Do NOT initialize with README

### Push Your Code

```bash
cd instagram_engine
git init
git add .
git commit -m "Initial commit: Instagram Engine v1.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prisha-instagram-engine.git
git push -u origin main
```

---

## 6. GitHub Secrets Configuration

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name              | Value                                    |
|--------------------------|------------------------------------------|
| `GEMINI_API_KEY`         | Your Gemini API key                      |
| `OPENAI_API_KEY`         | Your OpenAI API key (optional)           |
| `INSTAGRAM_ACCESS_TOKEN` | Your long-lived Page access token        |
| `INSTAGRAM_BUSINESS_ID`  | Your Instagram Business Account ID       |
| `FACEBOOK_PAGE_ID`       | Your Facebook Page ID                    |
| `IMGUR_CLIENT_ID`        | Imgur API client ID (see below)          |

### Getting Imgur Client ID (for image hosting)

1. Go to https://api.imgur.com/oauth2/addclient
2. Register an application
3. Choose "Anonymous usage without user authorization"
4. Note the **Client ID**
5. Add as `IMGUR_CLIENT_ID` secret

---

## 7. Testing Locally

### Test Content Generation

```bash
source venv/bin/activate
python main.py --test-content
```

This will generate a sample post JSON without publishing. Check the output.

### Test Image Generation

```bash
python main.py --test-image
```

This will create a test image in `images/test_output.png`. Open it to verify quality.

### Test Instagram Credentials

```bash
python main.py --verify
```

This will verify your API token and business ID are correct.

### Test Full Pipeline (Dry Run)

```bash
python main.py --dry-run
```

This runs everything EXCEPT the actual Instagram publish. Safe to run anytime.

### Run Full Test Suite

```bash
python tests/test_pipeline.py
```

---

## 8. First Run

### Manual First Run

```bash
python main.py
```

This will:
1. Generate content via Gemini
2. Create a branded image
3. Publish to Instagram
4. Save to history

### Automated Daily Runs

Once pushed to GitHub with secrets configured, the workflow runs automatically at **10:00 AM IST daily**.

You can also trigger manually:
- Go to GitHub → Actions → "Prisha Instagram Engine" → "Run workflow"

---

## 9. Monitoring & Logs

### Local Logs

Check `logs/engine_YYYY-MM-DD.log` for detailed daily logs.

### GitHub Actions Logs

1. Go to GitHub → Actions
2. Click on the latest workflow run
3. Expand the "Run Instagram Engine" step

### Post History

`data/generated_posts.json` contains all generated posts. This file is committed back to the repo after each run.

---

## 10. Troubleshooting

### "Missing API Key" Error

- Check `.env` file exists and has correct keys
- For GitHub: verify secrets are set in repo settings

### "Access Token Expired"

- Instagram tokens expire after ~60 days
- Re-generate using Step 4e above
- Update the GitHub secret

### "Media container not ready"

- Instagram is still processing the image
- The engine retries automatically
- If persistent: check image size (< 8MB recommended)

### "Rate Limited"

- Instagram allows ~25 posts per day per account
- The engine posts 1/day, so this shouldn't happen
- If it does: wait 30 minutes, retry

### Image looks wrong / text cut off

- Check `config.yaml` image dimensions
- The engine auto-wraps text, but very long headlines may need manual adjustment
- Edit `lib/image_engine.py` font sizes if needed

### "Duplicate content detected"

- This is normal — the engine retries with new content
- If it happens frequently: the history file may have grown large
- The engine tracks all topics and avoids them

### GitHub Action fails

1. Check the Actions tab for error logs
2. Common issues:
   - Missing secrets
   - Token expired
   - Network timeout (retry by re-running the workflow)

---

## 11. Maintenance

### Weekly

- Check GitHub Actions ran successfully
- Review the generated post on Instagram
- Check logs for any warnings

### Monthly

- Refresh Instagram access token (before 60-day expiry)
- Review `data/generated_posts.json` for content quality
- Update `config.yaml` if services or business info changes

### Quarterly

- Review and update content categories in `config.yaml`
- Check for Pillow or dependency updates
- Review hashtag strategy based on Instagram analytics

---

## 12. Future Expansion

### Adding LinkedIn Support

1. Create `lib/linkedin_publisher.py` with same interface
2. In `main.py`, add after Instagram publish:
   ```python
   from lib.linkedin_publisher import LinkedInPublisher
   linkedin = LinkedInPublisher()
   linkedin.publish(image_path=image_path, caption=caption)
   ```

### Adding Facebook Support

Same pattern — the content is generated once, published to multiple platforms.

### Adding X (Twitter)

Twitter has different image ratios (16:9). Add a `resize_for_platform()` method in `ImageEngine`.

### Content Calendar

To plan content themes in advance, add a `content_calendar.json` that pre-defines weekly themes. The engine reads this before picking categories.
