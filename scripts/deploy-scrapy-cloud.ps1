param(
    [Parameter(Mandatory = $true)][string]$SeedUrl,
    [string]$FeedUri = '',
    [string]$Topic = 'viral video'
)

$ErrorActionPreference = 'Stop'

if (-not $FeedUri) {
    Write-Host 'SCRAPY_FEED_URI is not set. Deploy will still work, but feed export target will remain the default.' -ForegroundColor Yellow
} else {
    $env:SCRAPY_FEED_URI = $FeedUri
}

$env:SPIDER_SEED_URL = $SeedUrl
$env:SPIDER_TOPIC = $Topic

shub deploy
