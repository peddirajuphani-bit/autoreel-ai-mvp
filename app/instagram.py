import httpx
from .config import settings

class InstagramPublisher:
    def __init__(self, account): self.account=account
    def publish(self, video_url, caption):
        if not settings.instagram_publish_enabled:
            raise RuntimeError("Instagram publishing is disabled. Configure official Meta credentials and enable it explicitly.")
        base=f"https://graph.facebook.com/{settings.meta_api_version}"
        with httpx.Client(timeout=60) as c:
            r=c.post(f"{base}/{self.account.instagram_user_id}/media", data={
              "media_type":"REELS", "video_url":video_url, "caption":caption,
              "access_token":self.account.access_token})
            r.raise_for_status(); container=r.json()["id"]
            # In production, poll status_code until FINISHED before media_publish.
            p=c.post(f"{base}/{self.account.instagram_user_id}/media_publish", data={
              "creation_id":container,"access_token":self.account.access_token})
            p.raise_for_status()
            return container, p.json()["id"]

