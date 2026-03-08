# GitHub Actions setup

This project can publish `feeds/latest.json` to GitHub on every scheduled run.

## What is already configured

- Workflow: `.github/workflows/update-feed.yml`
- Output file: `feeds/latest.json`
- Default seed feeds:
  - `https://www.reddit.com/r/videos/hot/.rss`
  - `https://www.youtube.com/feeds/videos.xml?user=YouTube`

## What you need to do manually

1. Initialize git in `C:\Users\fuga_\my_spider_project` if needed.
2. Connect the repo to `https://github.com/fugamqq-oss/spider-video.git`.
3. Push the project to GitHub.
4. Enable GitHub Actions for the repository.

## Recommended commands

```powershell
git init
git branch -M main
git remote add origin https://github.com/fugamqq-oss/spider-video.git
git add .
git commit -m "Add video candidate spider and GitHub Actions feed updater"
git push -u origin main
```

## Raw URL to use in viral-video-system

After the first successful workflow run, use:

```text
https://raw.githubusercontent.com/fugamqq-oss/spider-video/main/feeds/latest.json
```

as `SCRAPY_CLOUD_FEED_URL`.

## Changing the seeds

Edit `SPIDER_SEED_URLS` in `.github/workflows/update-feed.yml`.
