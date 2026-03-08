param(
    [string]$Topic = 'viral video',
    [Parameter(Mandatory = $true)][string]$SeedUrl,
    [string]$OutputPath = 'feeds/manual-output.json'
)

$ErrorActionPreference = 'Stop'

scrapy crawl video_candidates `
  -a "topic=$Topic" `
  -a "seed_url=$SeedUrl" `
  -O $OutputPath
