$qemu = "C:\Program Files\qemu\qemu-system-arm.exe"
$elf = Join-Path $PSScriptRoot "..\baremetal\hello.elf"

& $qemu `
  -M mcimx6ul-evk -m 512 `
  -kernel $elf `
  -serial stdio `
  -display none `
  -no-reboot
