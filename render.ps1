$ErrorActionPreference = 'Stop'
$filmRoot = $PSScriptRoot
python (Join-Path $filmRoot 'score.py')
if ($LASTEXITCODE -ne 0) { throw 'Audio generation failed' }
python (Join-Path $filmRoot 'tools\render.py') (Join-Path $filmRoot 'comp.html') --out (Join-Path $filmRoot 'OFF-GRID.mp4') --sfx (Join-Path $filmRoot 'score.wav') --workers 8 --gap 8 --samples-max 20
if ($LASTEXITCODE -ne 0) { throw 'Video rendering failed' }
