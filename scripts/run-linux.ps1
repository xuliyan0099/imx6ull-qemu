param(
    [switch]$Headless
)

$qemu = "C:\Program Files\qemu\qemu-system-arm.exe"
$images = Join-Path $PSScriptRoot "..\images"
$runs = Join-Path $PSScriptRoot "..\runs"

$args = @(
    "-M", "mcimx6ul-evk",
    "-m", "512",
    "-smp", "1",
    "-kernel", (Join-Path $images "zImage"),
    "-dtb", (Join-Path $images "imx6ull-14x14-emmc-7-800x480-c.dtb"),
    "-append", "console=ttymxc0,115200 earlyprintk ignore_loglevel root=/dev/mmcblk1p2 rw rootwait",
    "-drive", "if=sd,index=1,file=$($images -replace '\\','/')/emmc.img,format=raw"
)

if ($Headless) {
    New-Item -ItemType Directory -Path $runs -Force | Out-Null
    $args += @("-serial", "file:$($runs -replace '\\','/')/linux-serial.log", "-display", "none", "-no-reboot")
} else {
    $args += @("-serial", "stdio", "-display", "gtk")
}

& $qemu @args
