"""
lib/instagram_publisher.py — Meta Graph API Instagram publisher.

Uses Instagram Graph API v21.0 to:
1. Create a media container (upload image + caption)
2. Publish the container
3. Handle errors, rate limits, and retries

API Endpoints Used:
  POST /{ig-user-id}/media          — create container
  POST /{ig-user-id}/media_publish  — publish container
  GET  /{ig-user-id}                — verify account
  GET  /{creation-id}?fields=status — check publish status

Prerequisites:
  - Instagram Business or Creator account
  - Facebook Page linked to that account
  - Facebook App with instagram_basic + instagram_content_publish permissions
  - Long-lived Page Access Token

Usage:
    publisher = InstagramPublisher()
    result = publisher.publish(
        image_path="/path/to/image.png",
        caption="Full caption with hashtags..."
    )
    # result = {"success": True, "media_id": "...", "permalink": "..."}
"""

import time
import requests
from pathlib import Path
from lib.utils import get_env
from lib.logger import EngineLogger

log = EngineLogger("instagram_publisher")

API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


class InstagramPublisher:
    """Publishes posts to Instagram via the Graph API."""

    def __init__(self):
        self.access_token = get_env("INSTAGRAM_ACCESS_TOKEN")
        self.business_id = get_env("INSTAGRAM_BUSINESS_ID")
        self.page_id = get_env("FACEBOOK_PAGE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PrishaOnlineDoc-Engine/1.0"
        })

    # ── Public API ──────────────────────────────────────────────────────────────

    def verify_credentials(self) -> bool:
        """
        Verify that the access token and business ID are valid.

        Returns:
            True if credentials work, False otherwise.
        """
        if not self.access_token or not self.business_id:
            log.error("Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID")
            return False

        try:
            url = f"{BASE_URL}/{self.business_id}"
            params = {
                "fields": "id,name,username",
                "access_token": self.access_token,
            }
            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if "error" in data:
                log.error("Credential verification failed", extra={
                    "error": data["error"].get("message", "unknown"),
                    "code": data["error"].get("code", 0),
                })
                return False

            log.info(f"Credentials verified: @{data.get('username', 'unknown')}", extra={
                "id": data.get("id"),
                "name": data.get("name"),
            })
            return True

        except requests.exceptions.RequestException as e:
            log.error(f"Credential verification request failed: {e}")
            return False

    def publish(
        self,
        image_path: str,
        caption: str,
        max_retries: int = 3,
    ) -> dict:
        """
        Publish a single-image Instagram post.

        Steps:
        1. Create media container with image URL and caption
        2. Wait for processing
        3. Publish the container
        4. Verify publish status

        Args:
            image_path: Absolute path to the image file
            caption: Full post caption (including hashtags)
            max_retries: Number of retry attempts on transient failures

        Returns:
            dict with keys:
              - success: bool
              - creation_id: str (container ID)
              - media_id: str (published media ID)
              - error: str (if failed)

        NOTE: The image must be publicly accessible for the Graph API to fetch it.
        For GitHub Actions, we upload to a temporary public URL or use base64.
        """
        # Validate inputs
        if not self.access_token or not self.business_id:
            return {
                "success": False,
                "error": "Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID in environment.",
            }

        image_file = Path(image_path)
        if not image_file.exists():
            return {
                "success": False,
                "error": f"Image file not found: {image_path}",
            }

        # The Instagram Graph API needs a PUBLICLY ACCESSIBLE image URL.
        # For automated posting from CI/CD, we have two options:
        #   A) Upload image to a public CDN (imgur, Cloudinary, etc.)
        #   B) Use Facebook's resumable upload with base64
        #
        # Here we implement Option A via a simple base64 data URI for smaller images,
        # but RECOMMENDED approach is to upload to a public URL first.

        # For production: upload image to get a public URL
        image_url = self._upload_image_to_public_url(image_path)
        if not image_url:
            return {
                "success": False,
                "error": "Failed to get a public URL for the image. Configure a CDN or image host.",
            }

        # Step 1: Create media container
        creation_id = self._create_media_container(image_url, caption, max_retries)
        if not creation_id:
            return {
                "success": False,
                "error": "Failed to create media container.",
            }

        # Step 2: Wait for processing
        log.info("Waiting for media processing...")
        time.sleep(10)

        # Step 3: Publish
        media_id = self._publish_container(creation_id, max_retries)
        if not media_id:
            return {
                "success": False,
                "error": f"Failed to publish container {creation_id}.",
                "creation_id": creation_id,
            }

        log.info(f"Post published successfully! Media ID: {media_id}")
        return {
            "success": True,
            "creation_id": creation_id,
            "media_id": media_id,
        }

    # ── Step 1: Create Media Container ──────────────────────────────────────────

    def _create_media_container(
        self, image_url: str, caption: str, max_retries: int
    ) -> str | None:
        """
        Create an Instagram media container.

        POST /{ig-user-id}/media
          ?image_url=...
          &caption=...
          &access_token=...

        Returns:
            Creation ID string, or None on failure.
        """
        url = f"{BASE_URL}/{self.business_id}/media"
        params = {
            "image_url": image_url,
            "caption": caption[:2200],  # Instagram caption limit
            "access_token": self.access_token,
        }

        for attempt in range(1, max_retries + 1):
            try:
                log.debug(f"Creating media container (attempt {attempt}/{max_retries})")
                resp = self.session.post(url, params=params, timeout=60)
                data = resp.json()

                if "error" in data:
                    error = data["error"]
                    code = error.get("code", 0)
                    msg = error.get("message", "unknown error")

                    # Rate limit — back off
                    if code == 4 or code == 32 or code == 613:
                        wait = 30 * attempt
                        log.warn(f"Rate limited, waiting {wait}s...", extra={"code": code})
                        time.sleep(wait)
                        continue

                    # Token expired
                    if code == 190:
                        log.error("Access token expired. Please refresh it.")
                        return None

                    log.error(f"Container creation failed: {msg}", extra={"code": code})
                    if attempt < max_retries:
                        time.sleep(5 * attempt)
                        continue
                    return None

                creation_id = data.get("id")
                if creation_id:
                    log.info(f"Media container created: {creation_id}")
                    return creation_id

                log.warn("Container creation returned no ID", extra={"response": str(data)[:200]})

            except requests.exceptions.RequestException as e:
                log.warn(f"Container creation request failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(5 * attempt)

        return None

    # ── Step 2: Publish Container ───────────────────────────────────────────────

    def _publish_container(self, creation_id: str, max_retries: int) -> str | None:
        """
        Publish a media container.

        POST /{ig-user-id}/media_publish
          ?creation_id=...
          &access_token=...

        Returns:
            Published media ID string, or None on failure.
        """
        url = f"{BASE_URL}/{self.business_id}/media_publish"
        params = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }

        for attempt in range(1, max_retries + 1):
            try:
                log.debug(f"Publishing container (attempt {attempt}/{max_retries})")
                resp = self.session.post(url, params=params, timeout=60)
                data = resp.json()

                if "error" in data:
                    error = data["error"]
                    code = error.get("code", 0)
                    msg = error.get("message", "unknown error")

                    if code == 4 or code == 32:
                        wait = 30 * attempt
                        log.warn(f"Rate limited on publish, waiting {wait}s...")
                        time.sleep(wait)
                        continue

                    if code == 190:
                        log.error("Access token expired during publish.")
                        return None

                    # "Media ID is not available" — container still processing
                    if "not available" in msg.lower():
                        log.warn("Container still processing, waiting 15s...")
                        time.sleep(15)
                        continue

                    log.error(f"Publish failed: {msg}", extra={"code": code})
                    if attempt < max_retries:
                        time.sleep(5 * attempt)
                        continue
                    return None

                media_id = data.get("id")
                if media_id:
                    log.info(f"Container published: {media_id}")
                    return media_id

                log.warn("Publish returned no media ID", extra={"response": str(data)[:200]})

            except requests.exceptions.RequestException as e:
                log.warn(f"Publish request failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(5 * attempt)

        return None

    # ── Image Upload Helper ─────────────────────────────────────────────────────

    def _upload_image_to_public_url(self, image_path: str) -> str | None:
        """
        Upload image to a publicly accessible URL so Instagram can fetch it.

        Strategy (in order of preference):
        1. GitHub raw URL (for GitHub Actions CI/CD)
        2. Imgur anonymous upload (free, requires IMGUR_CLIENT_ID)
        3. Custom IMAGE_HOST_URL

        Args:
            image_path: Local path to image file

        Returns:
            Publicly accessible URL string, or None on failure.
        """
        # Option 0: Explicit image URL override (for CI/CD)
        image_url_override = get_env("IMAGE_URL_OVERRIDE")
        if image_url_override:
            log.info(f"Using IMAGE_URL_OVERRIDE: {image_url_override}")
            return image_url_override

        # Option 1: GitHub Actions — construct raw GitHub URL
        # In CI, the image is committed to the repo and accessed via raw.githubusercontent.com
        github_repo = get_env("GITHUB_REPOSITORY")  # e.g., "SwamiChaudhari/prisha-instagram-engine"
        if github_repo:
            image_name = Path(image_path).name
            github_branch = get_env("GITHUB_REF_NAME", "main")
            raw_url = f"https://raw.githubusercontent.com/{github_repo}/{github_branch}/images/{image_name}"
            log.info(f"Using GitHub raw URL: {raw_url}")
            return raw_url

        # Option 2: Imgur upload
        imgur_client_id = get_env("IMGUR_CLIENT_ID")
        if imgur_client_id:
            return self._upload_to_imgur(image_path, imgur_client_id)

        # Option 3: Custom image host
        image_host = get_env("IMAGE_HOST_URL")
        if image_host:
            log.info(f"IMAGE_HOST_URL configured: {image_host}")
            # For custom hosts, assume the image is already accessible
            # Implement custom upload logic here if needed

        log.error(
            "No image upload service configured. "
            "Set IMGUR_CLIENT_ID for local runs, or run in GitHub Actions."
        )
        return None

    def _upload_to_imgur(self, image_path: str, client_id: str) -> str | None:
        """Upload image to Imgur anonymously and return the public URL."""
        try:
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            resp = self.session.post(
                "https://api.imgur.com/3/image",
                headers={"Authorization": f"Client-ID {client_id}"},
                data={"image": image_data, "type": "base64"},
                timeout=30,
            )
            data = resp.json()

            if data.get("success"):
                link = data["data"]["link"]
                log.info(f"Image uploaded to Imgur: {link}")
                return link
            else:
                log.error("Imgur upload failed", extra={"response": str(data)[:200]})

        except Exception as e:
            log.error(f"Imgur upload error: {e}")

        return None

    # ── Status Check ────────────────────────────────────────────────────────────

    def check_publish_status(self, creation_id: str) -> dict:
        """
        Check the status of a media container.

        GET /{creation-id}?fields=status_code,status

        Returns:
            dict with status info
        """
        url = f"{BASE_URL}/{creation_id}"
        params = {
            "fields": "status_code,status,error_message",
            "access_token": self.access_token,
        }

        try:
            resp = self.session.get(url, params=params, timeout=30)
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
