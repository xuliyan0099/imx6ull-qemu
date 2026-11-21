from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()
old = """            if (page_aligned && boundary_count == 0) {
                break;
            }
"""
new = """            /*
             * U-Boot's FSL eSDHC driver expects the controller to consume
             * the whole block count in one command.  Continue across the
             * SDMA buffer boundary instead of stopping and waiting for a
             * guest that never reprograms the transfer.
             */
            if (boundary_count == 0) {
                boundary_count = boundary_chk;
            }
"""
count = s.count(old)
print("occurrences", count)
assert count >= 1
p.write_text(s.replace(old, new))
print("boundary break removed")
