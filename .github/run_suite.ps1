# Tek bir test paketini kosar, ozetini is ozetine (job summary) dusurur.
#
# Neden ayri betik: 7 adimin hepsi ayni 12 satiri tekrarlamasin diye.
# Neden ayri ADIMLAR (tek dongu degil): kirilan paket GitHub arayuzunde
# tek bakista gorunsun diye - is akisinin amaci bu.
#
# Bu dosya BILEREK yalnizca ASCII karakter icerir: Windows PowerShell 5.1
# BOM'suz .ps1'leri ANSI okur ve tek bir uzun tire betigi coker.
param([Parameter(Mandatory = $true)][string]$Suite)

$ErrorActionPreference = 'Continue'
Write-Host "=== $Suite ==="

$out = & python $Suite 2>&1
$code = $LASTEXITCODE
$line = $out | Select-String -Pattern '^RESULT:' | Select-Object -Last 1
$result = if ($line) { $line.ToString() } else { '(RESULT satiri yok - paket erken coktu)' }

if ($code -ne 0) {
    # Hata varsa TAM ciktiyi bas: neyin kirildigi loglarda dursun.
    $out | ForEach-Object { Write-Host $_ }
} else {
    # Basariliysa son 25 satir yeter (her kontrol bir satir basiyor).
    $out | Select-Object -Last 25 | ForEach-Object { Write-Host $_ }
}

if ($code -eq 0) { $icon = 'OK' } else { $icon = 'HATA' }
if ($env:GITHUB_STEP_SUMMARY) {
    "| ``$Suite`` | $icon - $result |" |
        Out-File -Append -Encoding utf8 $env:GITHUB_STEP_SUMMARY
}

Write-Host "--- $Suite -> $result (exit=$code)"
exit $code
