/*
 * Copyright (c) 2018 Jean-Christophe Dubois <jcd@tribudubois.net>
 *
 * MCIMX6UL_EVK Board System emulation.
 *
 * This code is licensed under the GPL, version 2 or later.
 * See the file `COPYING' in the top level directory.
 *
 * It (partially) emulates a mcimx6ull_alientek board, with a Freescale
 * i.MX6ul SoC
 */

#include "qemu/osdep.h"
#include "qapi/error.h"
#include "hw/arm/fsl-imx6ul.h"
#include "hw/arm/boot.h"
#include "hw/arm/machines-qom.h"
#include "hw/core/boards.h"
#include "hw/core/loader.h"
#include "hw/core/qdev-properties.h"
#include "qemu/error-report.h"
#include "system/address-spaces.h"
#include "system/block-backend.h"
#include "system/block-backend-io.h"
#include "system/memory.h"
#include "system/qtest.h"

#define IMX6ULL_IVT_MAGIC      0x402000d1
#define IMX6ULL_IVT_OFFSET     0x400
#define IMX6ULL_MAX_BOOT_IMAGE (16 * MiB)

static uint16_t dcd_be16(const uint8_t *p)
{
    return (p[0] << 8) | p[1];
}

/*
 * Replay the DCD (Device Configuration Data) block found by the IVT.
 *
 * U-Boot's .imx contains a DCD made of 0xCC write commands.  Each command
 * carries an array of (address, value) pairs.  The real BootROM applies these
 * before starting the image; doing the same here lets us boot the untouched
 * vendor image and exercise the same MMDC/CCM/IOMUX setup path.  The block is
 * inside the image buffer, at dcd_addr relative to self (the IVT address).
 */
static void mcimx6ull_alientek_apply_dcd(const uint8_t *buf, size_t len,
                                         uint64_t self, uint64_t dcd_addr)
{
    const uint8_t *dcd, *p, *end;
    uint64_t off;
    uint16_t dcd_len;
    unsigned writes = 0;
    MemTxResult res;

    if (dcd_addr < self) {
        return;
    }
    off = dcd_addr - self;
    if (off > len || len - off < 4) {
        return;
    }
    dcd = buf + off;
    if (dcd[0] != 0xd2) {
        return;
    }

    dcd_len = dcd_be16(dcd + 1);
    if (dcd_len < 8 || off + dcd_len > len) {
        return;
    }

    p = dcd + 4;
    end = dcd + dcd_len;
    while (p + 4 <= end) {
        uint8_t tag = p[0];
        uint16_t cmd_len = dcd_be16(p + 1);

        if (cmd_len < 4 || p + cmd_len > end) {
            break;
        }
        if (tag == 0xcc) {
            size_t n = (cmd_len - 4) / 8;
            size_t i;

            for (i = 0; i < n; i++) {
                uint32_t addr = ldl_be_p(p + 4 + i * 8);
                uint32_t value = ldl_be_p(p + 4 + i * 8 + 4);

                res = address_space_write(&address_space_memory, addr,
                                          MEMTXATTRS_UNSPECIFIED,
                                          &value, sizeof(value));
                if (res == MEMTX_OK) {
                    writes++;
                }
            }
        }
        p += cmd_len;
    }

    if (writes) {
        error_report("imx6ull BootROM: applied DCD, %u register writes",
                     writes);
    }
}

/*
 * Minimal i.MX6ULL BootROM replacement.
 *
 * The real BootROM reads an IVT from the boot device, applies the DCD, copies
 * the boot image to the address in self_ptr/boot_data and jumps to the entry
 * point.  The DCD is replayed so the vendor .imx image follows its original
 * initialization sequence; QEMU's MMDC model accepts the same register
 * programming that the real DDR controller receives.
 */
static bool mcimx6ull_alientek_load_uboot(BlockBackend *blk)
{
    uint32_t ivt[8];
    uint32_t boot_data[3];
    uint64_t entry, self, dcd_ptr, boot_data_addr;
    uint64_t image_start, image_size;
    uint64_t image_len;
    uint32_t rom[2];
    g_autofree uint8_t *buf = NULL;
    MemTxResult res;

    if (!blk) {
        return false;
    }

    if (blk_pread(blk, IMX6ULL_IVT_OFFSET, sizeof(ivt), ivt, 0) < 0) {
        return false;
    }
    if (ivt[0] != IMX6ULL_IVT_MAGIC) {
        return false;
    }

    entry = ivt[1];
    dcd_ptr = ivt[3];
    boot_data_addr = ivt[4];
    self = ivt[5];
    if (entry < 0x80000000 || self < 0x80000000 ||
        boot_data_addr < self || boot_data_addr - self > 0x1000) {
        return false;
    }

    if (blk_pread(blk, IMX6ULL_IVT_OFFSET + (boot_data_addr - self),
                  sizeof(boot_data), boot_data, 0) < 0) {
        return false;
    }
    image_start = boot_data[0];
    image_size = boot_data[1];
    if (image_size > IMX6ULL_MAX_BOOT_IMAGE ||
        self < image_start || self - image_start > image_size) {
        return false;
    }

    /* Bytes [self, self + image_len) are the actual .imx payload. */
    image_len = image_size - (self - image_start);
    buf = g_malloc(image_len);
    if (blk_pread(blk, IMX6ULL_IVT_OFFSET, image_len, buf, 0) < 0) {
        return false;
    }

    mcimx6ull_alientek_apply_dcd(buf, image_len, self, dcd_ptr);

    res = address_space_write(&address_space_memory, self,
                              MEMTXATTRS_UNSPECIFIED, buf, image_len);
    if (res != MEMTX_OK) {
        return false;
    }

    /*
     * The first instruction in the SoC ROM is a jump to the loaded image.
     * QEMU starts the CPU at address 0, so this also makes the same eMMC
     * image bootable without a host-side -kernel file.
     */
    rom[0] = 0xe51ff004; /* ldr pc, [pc, #-4] */
    rom[1] = entry;
    rom_add_blob_fixed("imx6ull.bootrom", rom, sizeof(rom), 0);

    return true;
}

static void mcimx6ull_alientek_init(MachineState *machine)
{
    static struct arm_boot_info boot_info;
    FslIMX6ULState *s;
    BlockBackend *emmc_blk = NULL;
    int i;

    if (machine->ram_size > FSL_IMX6UL_MMDC_SIZE) {
        error_report("RAM size " RAM_ADDR_FMT " above max supported (%08x)",
                     machine->ram_size, FSL_IMX6UL_MMDC_SIZE);
        exit(1);
    }

    boot_info = (struct arm_boot_info) {
        .loader_start = FSL_IMX6UL_MMDC_ADDR,
        .board_id = -1,
        .ram_size = machine->ram_size,
        .psci_conduit = QEMU_PSCI_CONDUIT_SMC,
    };

    s = FSL_IMX6UL(object_new(TYPE_FSL_IMX6UL));
    object_property_add_child(OBJECT(machine), "soc", OBJECT(s));
    object_property_set_uint(OBJECT(s), "fec1-phy-num", 2, &error_fatal);
    object_property_set_uint(OBJECT(s), "fec2-phy-num", 1, &error_fatal);
    object_property_set_bool(OBJECT(s), "fec1-phy-connected", false,
                             &error_fatal);
    qdev_realize(DEVICE(s), NULL, &error_fatal);

    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_MMDC_ADDR,
                                machine->ram);

    for (i = 0; i < FSL_IMX6UL_NUM_USDHCS; i++) {
        BusState *bus;
        DeviceState *carddev;
        DriveInfo *di;
        BlockBackend *blk;

        di = drive_get(IF_SD, 0, i);
        blk = di ? blk_by_legacy_dinfo(di) : NULL;
        if (i == 1 && blk) {
            emmc_blk = blk;
        }
        bus = qdev_get_child_bus(DEVICE(&s->usdhc[i]), "sd-bus");
        carddev = qdev_new(TYPE_SD_CARD);
        qdev_prop_set_drive_err(carddev, "drive", blk, &error_fatal);
        qdev_realize_and_unref(carddev, bus, &error_fatal);
    }

    if (!qtest_enabled()) {
        if (machine->kernel_filename) {
            /* Existing Linux direct-boot path. */
            arm_load_kernel(&s->cpu, machine, &boot_info);
        } else {
            /*
             * No -kernel: behave like the on-chip BootROM.  The eMMC image
             * must contain u-boot.imx at offset 0x400, exactly as a real
             * board's first-stage image is flashed.
             */
            if (!mcimx6ull_alientek_load_uboot(emmc_blk)) {
                error_report("no kernel and no valid i.MX IVT in eMMC at 0x%x",
                             IMX6ULL_IVT_OFFSET);
                exit(1);
            }
            arm_load_kernel(&s->cpu, machine, &boot_info);
        }
    }
}

static void mcimx6ull_alientek_machine_init(MachineClass *mc)
{
    mc->desc = "Alientek I.MX6ULL Mini (Cortex-A7, eMMC + 7in LCD)";
    mc->init = mcimx6ull_alientek_init;
    mc->max_cpus = FSL_IMX6UL_NUM_CPUS;
    mc->default_ram_id = "mcimx6ul-evk.ram";
    mc->auto_create_sdcard = true;
}

DEFINE_MACHINE_ARM("mcimx6ull-alientek", mcimx6ull_alientek_machine_init)
