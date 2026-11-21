from pathlib import Path
import subprocess

new = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
old_text = new.read_text().replace(
    """            /*
             * U-Boot's FSL eSDHC driver expects the controller to consume
             * the whole block count in one command.  Continue across the
             * SDMA buffer boundary instead of stopping and waiting for a
             * guest that never reprograms the transfer.
             */
            if (boundary_count == 0) {
                boundary_count = boundary_chk;
            }
""",
    """            if (page_aligned && boundary_count == 0) {
                break;
            }
""",
)
p_old = Path("/tmp/sdhci-old.c")
p_new = Path("/tmp/sdhci-new.c")
p_old.write_text(old_text)
p_new.write_text(new.read_text())
r = subprocess.run(
    ["diff", "-u", "--label", "a/hw/sd/sdhci.c", "--label", "b/hw/sd/sdhci.c",
     str(p_old), str(p_new)],
    capture_output=True, text=True,
)
out = Path("/mnt/d/Workspace/StudyNote/IM6/qemu/patches/0009-sdhci-dma-boundary.patch")
out.write_text(r.stdout)
print(r.stdout[:400])
print("bytes", out.stat().st_size)
