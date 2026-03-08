# Scrapy Cloud deployment helpers

## 1. Local verification

```powershell
pwsh -File .\scripts\run-local.ps1 -SeedUrl "https://your-feed.example/latest.xml" -Topic "cats shorts"
```

This writes JSON to `feeds/manual-output.json` and also updates `feeds/latest.json`.

## 2. Deploy to Scrapy Cloud

```powershell
pwsh -File .\scripts\deploy-scrapy-cloud.ps1 `
  -SeedUrl "https://your-feed.example/latest.xml" `
  -FeedUri "s3://your-bucket/video-candidates/latest.json" `
  -Topic "cats shorts"
```

## 3. What you must provide manually

- `SeedUrl`: an RSS / Atom / JSON feed URL that contains platform video links.
- `FeedUri`: a stable cloud storage target such as S3 / GCS / FTP.
- Public HTTP URL of the exported `latest.json`.

## 4. What to send back to Codex

Send the final public JSON URL, for example:

```text
https://your-bucket.s3.amazonaws.com/video-candidates/latest.json
```

That URL becomes `SCRAPY_CLOUD_FEED_URL` in the video pipeline.
