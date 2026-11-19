# Ajoute marcel.yourdomain.com au tunnel Cloudflare existant (yourdomain.com)
# Backend: Open WebUI sur LXC 100 (http://192.168.1.150:8080)

param(
  [string]$Hostname = "marcel.yourdomain.com",
  [string]$Service = "http://192.168.1.150:8080",
  [string]$ZoneName = "yourdomain.com",
  [string]$DnsName = "marcel",
  [string]$ApiToken = $env:CLOUDFLARE_API_TOKEN,
  [string]$AccountId = $env:CLOUDFLARE_ACCOUNT_ID
)

$ErrorActionPreference = "Stop"

if (-not $ApiToken) {
  Write-Error "CLOUDFLARE_API_TOKEN manquant. Veuillez passer le token ou definir `$env:CLOUDFLARE_API_TOKEN."
}

$headers = @{
  Authorization = "Bearer $ApiToken"
  "Content-Type" = "application/json"
}

function Invoke-CfApi {
  param([string]$Method, [string]$Path, $Body = $null)
  $uri = "https://api.cloudflare.com/client/v4$Path"
  if ($null -ne $Body) {
    $json = $Body | ConvertTo-Json -Depth 20
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $json
  }
  return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
}

Write-Host "[cf] Recherche de la Zone $ZoneName..." -ForegroundColor Cyan
$zones = Invoke-CfApi -Method GET -Path "/zones?name=$ZoneName"
if (-not $zones.result.Count) { throw "Zone introuvable : $ZoneName" }
$zoneId = $zones.result[0].id

if (-not $AccountId) {
  Write-Host "[cf] Recherche du Account ID..." -ForegroundColor Cyan
  $accounts = Invoke-CfApi -Method GET -Path "/accounts?per_page=50"
  if ($accounts.result.Count -eq 1) {
    $AccountId = $accounts.result[0].id
  } else {
    $AccountId = "your_cloudflare_account_id"
  }
}

Write-Host "[cf] Recherche des Tunnels..." -ForegroundColor Cyan
$tunnelPath = "/accounts/$AccountId/cfd_tunnel?is_deleted=false&per_page=100"
$tunnels = Invoke-CfApi -Method GET -Path $tunnelPath
if (-not $tunnels.result.Count) { throw "Aucun tunnel trouve sur ce compte." }

$tunnel = $null
foreach ($t in $tunnels.result) {
  try {
    $cfgPath = "/accounts/$AccountId/cfd_tunnel/$($t.id)/configurations"
    $cfg = Invoke-CfApi -Method GET -Path $cfgPath
    $ingress = $cfg.result.config.ingress
    $match = $ingress | Where-Object { $_.hostname -and $_.hostname -like "*.$ZoneName" }
    if ($match) {
      $tunnel = $t
      break
    }
  } catch {}
}
if (-not $tunnel) {
  $tunnel = ($tunnels.result | Where-Object { $_.status -eq "healthy" } | Select-Object -First 1)
}
if (-not $tunnel) {
  $tunnel = $tunnels.result[0]
}
Write-Host "[cf] Tunnel selectionne : $($tunnel.name) ($($tunnel.id))" -ForegroundColor Yellow

$cfgPath = "/accounts/$AccountId/cfd_tunnel/$($tunnel.id)/configurations"
$current = Invoke-CfApi -Method GET -Path $cfgPath
$ingress = @($current.result.config.ingress)
if (-not $ingress.Count) { $ingress = @() }

$existingRule = $ingress | Where-Object { $_.hostname -eq $Hostname }
if ($existingRule) {
  Write-Host "[cf] Mise a jour de la regle pour $Hostname -> $Service" -ForegroundColor Yellow
  $catchAll = $ingress | Where-Object { -not $_.hostname -and $_.service }
  $rules = @()
  foreach ($r in ($ingress | Where-Object { $_.hostname })) {
    if ($r.hostname -eq $Hostname) {
      $rules += @{ hostname = $Hostname; service = $Service }
    } else {
      $rules += @{ hostname = $r.hostname; service = $r.service }
    }
  }
  if ($catchAll) {
    $rules += @{ service = $catchAll[0].service }
  } else {
    $rules += @{ service = "http_status:404" }
  }
  Invoke-CfApi -Method PUT -Path $cfgPath -Body @{ config = @{ ingress = $rules } } | Out-Null
} else {
  Write-Host "[cf] Ajout du hostname ingress $Hostname -> $Service" -ForegroundColor Green
  $catchAll = $ingress | Where-Object { -not $_.hostname -and $_.service }
  $rules = @()
  foreach ($r in ($ingress | Where-Object { $_.hostname })) {
    $rules += @{ hostname = $r.hostname; service = $r.service }
  }
  $rules += @{ hostname = $Hostname; service = $Service }
  if ($catchAll) {
    $rules += @{ service = $catchAll[0].service }
  } else {
    $rules += @{ service = "http_status:404" }
  }
  Invoke-CfApi -Method PUT -Path $cfgPath -Body @{ config = @{ ingress = $rules } } | Out-Null
}

Write-Host "[cf] Creation / mise a jour du DNS CNAME $DnsName -> Tunnel..." -ForegroundColor Cyan
$cnameTarget = "$($tunnel.id).cfargotunnel.com"
$dnsPath = "/zones/$zoneId/dns_records?type=CNAME&name=$Hostname"
$existing = Invoke-CfApi -Method GET -Path $dnsPath

if ($existing.result.Count) {
  $rec = $existing.result[0]
  if ($rec.content -ne $cnameTarget -or -not $rec.proxied) {
    Invoke-CfApi -Method PUT -Path "/zones/$zoneId/dns_records/$($rec.id)" -Body @{
      type = "CNAME"
      name = $DnsName
      content = $cnameTarget
      proxied = $true
    } | Out-Null
    Write-Host "[cf] DNS mis a jour" -ForegroundColor Green
  } else {
    Write-Host "[cf] DNS deja a jour" -ForegroundColor DarkGray
  }
} else {
  Invoke-CfApi -Method POST -Path "/zones/$zoneId/dns_records" -Body @{
    type = "CNAME"
    name = $DnsName
    content = $cnameTarget
    proxied = $true
  } | Out-Null
  Write-Host "[cf] DNS cree avec succes ($DnsName -> $cnameTarget)" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " TERMINE ! Votre interface est maintenant accessible sur :" -ForegroundColor Green
Write-Host " https://$Hostname" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
