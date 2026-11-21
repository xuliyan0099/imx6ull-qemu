$qemu = "C:\Program Files\qemu\qemu-system-arm.exe"
$elf = Join-Path $PSScriptRoot "..\baremetal\lcdif_probe.elf"

& $qemu `
  -M mcimx6ul-evk -m 512 `
  -kernel $elf `
  -serial null `
  -display gtk `
  -monitor stdio `
  -no-reboot
