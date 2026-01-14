param(
  [Parameter(Mandatory=$true)][string]$Tickets,
  [int]$S = 10000,
  [int]$A = 5000
)

$ErrorActionPreference = "Stop"

if(!(Test-Path $Tickets)){
  Write-Error "Tickets not found: $Tickets"
  exit 2
}

# race-level sum by (date,jcd,race_no,tier)
$rows = Import-Csv $Tickets

# Normalize numeric
foreach($r in $rows){
  if($null -ne $r.bet_yen -and $r.bet_yen -ne ""){
    $r.bet_yen = [double]$r.bet_yen
  } else {
    $r.bet_yen = 0.0
  }
}

$g = $rows | Group-Object -Property date,jcd,race_no,tier

$bad = @()
$warn = @()

foreach($grp in $g){
  $p = $grp.Group[0]
  $tier = $p.tier
  $sum = ($grp.Group | Measure-Object -Property bet_yen -Sum).Sum
  $exp = $null
  if($tier -eq "S"){ $exp = $S }
  elseif($tier -eq "A"){ $exp = $A }
  else { $warn += [pscustomobject]@{date=$p.date;jcd=$p.jcd;race_no=$p.race_no;tier=$tier;invest=$sum;note="skip_check"}; continue }

  if([math]::Abs($sum - $exp) -gt 0.1){
    $bad += [pscustomobject]@{date=$p.date;jcd=$p.jcd;race_no=$p.race_no;tier=$tier;invest=$sum;expected=$exp}
  }
}

if($warn.Count -gt 0){
  Write-Host "[D_BET_SIZING_GUARD] WARN: tiers other than S/A exist (skip check). sample:" -ForegroundColor Yellow
  $warn | Select-Object -First 10 | Format-Table -AutoSize | Out-String | Write-Host
}

if($bad.Count -gt 0){
  Write-Host "[D_BET_SIZING_GUARD] FAIL: tier invest mismatch" -ForegroundColor Red
  $bad | Sort-Object date,jcd,race_no | Select-Object -First 20 | Format-Table -AutoSize | Out-String | Write-Host
  Write-Host ("bad_races=" + $bad.Count + " / total_races=" + $g.Count) -ForegroundColor Red
  exit 2
}

Write-Host "[D_BET_SIZING_GUARD] PASS" -ForegroundColor Green
exit 0
