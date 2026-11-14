#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

import struct
from typing import Any

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

def stub_plt_symbol(symbol_name: str):
    def impl(ctx: Any, file: Any, file_path: str, *args: Any, **kwargs: Any):
        with open(file_path, 'rb+') as f:
            data = f.read()
            if len(data) < 64 or data[:4] != b'\x7fELF':
                return

            e_shoff, = struct.unpack('<Q', data[40:48])
            e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHH', data[58:64])

            sections = []
            for i in range(e_shnum):
                offset = e_shoff + i * e_shentsize
                sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack('<IIQQQQIIQQ', data[offset:offset+64])
                sections.append({
                    'name_idx': sh_name, 'type': sh_type, 'flags': sh_flags, 'addr': sh_addr,
                    'offset': sh_offset, 'size': sh_size, 'link': sh_link, 'info': sh_info, 'entsize': sh_entsize
                })

            shstrtab_sec = sections[e_shstrndx]
            shstrtab = data[shstrtab_sec['offset']:shstrtab_sec['offset']+shstrtab_sec['size']]

            for s in sections:
                s['name'] = shstrtab[s['name_idx']:shstrtab.find(b'\0', s['name_idx'])].decode('latin1')

            dynsym_sec = next((s for s in sections if s['name'] == '.dynsym'), None)
            rela_plt_sec = next((s for s in sections if s['name'] == '.rela.plt'), None)
            plt_sec = next((s for s in sections if s['name'] == '.plt'), None)
            if not dynsym_sec or not rela_plt_sec or not plt_sec:
                return

            dynstr_sec = sections[dynsym_sec['link']]
            dynstr = data[dynstr_sec['offset']:dynstr_sec['offset']+dynstr_sec['size']]

            sym_idx = None
            num_syms = dynsym_sec['size'] // dynsym_sec['entsize']
            for i in range(num_syms):
                sym_offset = dynsym_sec['offset'] + i * dynsym_sec['entsize']
                st_name, = struct.unpack('<I', data[sym_offset:sym_offset+4])
                st_name_str = dynstr[st_name:dynstr.find(b'\0', st_name)].decode('latin1')
                if st_name_str == symbol_name:
                    sym_idx = i
                    break

            if sym_idx is None:
                return

            got_addr = None
            num_relas = rela_plt_sec['size'] // rela_plt_sec['entsize']
            for i in range(num_relas):
                rela_offset = rela_plt_sec['offset'] + i * rela_plt_sec['entsize']
                r_offset, r_info, r_addend = struct.unpack('<QQq', data[rela_offset:rela_offset+24])
                r_sym = r_info >> 32
                r_type = r_info & 0xffffffff
                if r_sym == sym_idx and r_type == 1026:  # R_AARCH64_JUMP_SLOT
                    got_addr = r_offset
                    break

            if got_addr is None:
                return

            got_page_offset = got_addr & 0xfff
            ldr_insn = 0xf9400211 | ((got_page_offset >> 3) << 10)
            ldr_bytes = struct.pack('<I', ldr_insn)

            plt_start = plt_sec['offset']
            plt_size = plt_sec['size']

            for off in range(plt_start + 16, plt_start + plt_size, 16):
                if data[off+4:off+8] == ldr_bytes:
                    f.seek(off)
                    f.write(b'\xc0\x03\x5f\xd6')
                    break

    return impl

namespace_imports = [
    'device/xiaomi/air-micam',
    'vendor/xiaomi/air',
]

blob_fixups: blob_fixups_user_type = {
    'system/lib64/libcamera_algoup_jni.xiaomi.so': blob_fixup()
        .add_needed('libgui_shim_miuicamera.so')
        .sig_replace('08 AD 40 F9', '08 A9 40 F9'),
    'system/lib64/libcamera_ispinterface_jni.xiaomi.so': blob_fixup()
        .add_needed('libgui_shim_miuicamera.so')
        .remove_needed('libhidltransport.so')
        .replace_needed('vendor.mediatek.hardware.camera.isphal@1.0.so', 'vendor.mediatek.hardware.camera.isphal@1.0-system.so'),
    'system/lib64/libcamera_mianode_jni.xiaomi.so': blob_fixup()
        .add_needed('libgui_shim_miuicamera.so'),
    'system/lib64/vendor.mediatek.hardware.camera.isphal@1.0-system.so': blob_fixup()
        .fix_soname(),
    'system/lib64/vendor.mediatek.hardware.camera.isphal-V1-ndk.so': blob_fixup()
        .replace_needed('android.hardware.graphics.common-V5-ndk.so', 'android.hardware.graphics.common-V7-ndk.so'),
    'vendor/lib64/libmialgoengine.so': blob_fixup()
        .call(stub_plt_symbol('_ZN7android7RefBaseD2Ev')),
    'vendor/lib64/libmialgoengine2.so': blob_fixup()
        .call(stub_plt_symbol('_ZN7android7RefBaseD2Ev')),
    'system/priv-app/MiuiCamera/MiuiCamera.apk': blob_fixup()
        .apktool_patch('patches'),
}  # fmt: skip

module = ExtractUtilsModule(
    'air-micam',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
