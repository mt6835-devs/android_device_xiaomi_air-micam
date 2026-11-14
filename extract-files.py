#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

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
        .sig_replace('10 00 00 b0 11 fe 43 f9 10 e2 1f 91 20 02 1f d6', 'c0 03 5f d6 11 fe 43 f9 10 e2 1f 91 20 02 1f d6'),
    'vendor/lib64/libmialgoengine2.so': blob_fixup()
        .sig_replace('10 00 00 b0 11 a6 45 f9 10 22 2d 91 20 02 1f d6', 'c0 03 5f d6 11 a6 45 f9 10 22 2d 91 20 02 1f d6'),
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
