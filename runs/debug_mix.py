from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()
old = '''    case ESDHC_MIX_CTRL:
        /*
         * So, when SD/MMC stack in Linux tries to write to "Transfer
'''
new = '''    case ESDHC_MIX_CTRL:
        fprintf(stderr, "USDHC MIX_CTRL val=%08x size=%u\\n", value, size);
        /*
         * So, when SD/MMC stack in Linux tries to write to "Transfer
'''
if old not in s:
    raise SystemExit("MIX marker missing")
s = s.replace(old, new, 1)
p.write_text(s)
print("MIX log added")
