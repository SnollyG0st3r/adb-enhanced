#!/usr/bin/python

# Python 2 and 3, print compatibility
from __future__ import print_function

import re
import sys

import os
import random
import subprocess
import docopt

"""
Swiss-army knife for Android testing and development.

List of things which this enhanced adb tool does

* adbe.py [options] rotate (landscape | portrait | left | right)
* adbe.py [options] gfx (on | off | lines)
* adbe.py [options] overdraw (on | off | deut)
* adbe.py [options] layout (on | off)
* adbe.py [options] airplane (on | off)
* adbe.py [options] battery level <percentage>
* adbe.py [options] battery saver (on | off)
* adbe.py [options] battery reset
* adbe.py [options] doze (on | off)
* adbe.py [options] jank <app_name>
* adbe.py [options] devices
* adbe.py [options] top-activity
* adbe.py [options] dump-ui <xml_file>
* adbe.py [options] mobile-data (on | off)
* adbe.py [options] mobile-data saver (on | off)
* adbe.py [options] rtl (on | off) - This is not working properly as of now.
* adbe.py [options] screenshot <filename.png>
* adbe.py [options] screenrecord <filename.mp4>
* adbe.py [options] dont-keep-activities (on | off)
* adbe.py [options] animations (on | off)
* adbe.py [options] input-text <text>
* adbe.py [options] press back
* adbe.py [options] open-url <url>
* adbe.py [options] permission-groups list all
* adbe.py [options] permissions list (all | dangerous)
* adbe.py [options] permissions (grant | revoke) <app_name> (calendar | camera | contacts | location | microphone | phone | sensors | sms | storage)
* adbe.py [options] standby-bucket get <app_name>
* adbe.py [options] standby-bucket set <app_name> (active | working_set | frequent | rare)
* adbe.py [options] restrict-background (true | false) <app_name>
* adbe.py [options] ls [-l] <file_path> - A smart ls which automatically configures "run-as" for accessing files under app-private directories like /data/data/com.example/
* adbe.py [options] pull <remote> [local] [-a] - A smart pull which automatically configures "run-as" for accessing files under app-private directories like /data/data/com.example/
* adbe.py [options] start <app_name> - Launches an Android app's default launcher activity, which in most cases corresponds to how a developer wants to start the app
* adbe.py [options] stop <app_name> - Force stop an application
* adbe.py [options] restart <app_name>
* adbe.py [options] force-stop <app_name>
* adbe.py [options] clear-data <app_name>
* adbe.py [options] app-info <app_name>
* adbe.py [options] print-apk-path <app_name>


List of things which this tool will do in the future

* adbe b[ack]g[round-]c[ellular-]d[ata] [on|off] $app_name # This might not be needed at all after mobile-data saver mode
* adbe app-standby $app_name
* adbe wifi [on|off]  # svc wifi enable/disable does not seem to always work
* adbe rtl (on | off)  # adb shell settings put global debug.force_rtl 1 does not seem to work
* adbe screen (on|off|toggle)  # https://stackoverflow.com/questions/7585105/turn-on-screen-on-device
* adb shell input keyevent KEYCODE_POWER can do the toggle
* adbe press up
* adbe set_app_name [-f] $app_name
* adbe reset_app_name
* adbe apps list (debugabble | system | third-party)
* adbe print-signature <app_name>

Use -q[uite] for quite mode

"""

USAGE_STRING = """
Swiss-army knife for Android testing and development.

Usage:
    adbe.py [options] rotate (landscape | portrait | left | right)
    adbe.py [options] gfx (on | off | lines)
    adbe.py [options] overdraw (on | off | deut)
    adbe.py [options] layout (on | off)
    adbe.py [options] airplane (on | off)
    adbe.py [options] battery level <percentage>
    adbe.py [options] battery saver (on | off)
    adbe.py [options] battery reset
    adbe.py [options] doze (on | off)
    adbe.py [options] jank <app_name>
    adbe.py [options] devices
    adbe.py [options] top-activity
    adbe.py [options] dump-ui <xml_file>
    adbe.py [options] mobile-data (on | off)
    adbe.py [options] mobile-data saver (on | off)
    adbe.py [options] rtl (on | off)
    adbe.py [options] screenshot <filename.png>
    adbe.py [options] screenrecord <filename.mp4>
    adbe.py [options] dont-keep-activities (on | off)
    adbe.py [options] animations (on | off)
    adbe.py [options] input-text <text>
    adbe.py [options] press back
    adbe.py [options] open-url <url>
    adbe.py [options] permission-groups list all
    adbe.py [options] permissions list (all | dangerous)
    adbe.py [options] permissions (grant | revoke) <app_name> (calendar | camera | contacts | location | microphone | phone | sensors | sms | storage)
    adbe.py [options] standby-bucket get <app_name>
    adbe.py [options] standby-bucket set <app_name> (active | working_set | frequent | rare)
    adbe.py [options] restrict-background (true | false) <app_name>
    adbe.py [options] ls [-l] [-R] <file_path>
    adbe.py [options] pull [-a] <remote>
    adbe.py [options] pull [-a] <remote> <local>
    adbe.py [options] cat <file_path>
    adbe.py [options] start <app_name>
    adbe.py [options] stop <app_name>
    adbe.py [options] restart <app_name>
    adbe.py [options] force-stop <app_name>
    adbe.py [options] clear-data <app_name>
    adbe.py [options] app-info <app_name>
    adbe.py [options] print-apk-path <app_name>

Options:
    -e, --emulator          directs the command to the only running emulator
    -d, --device            directs the command to the only connected "USB" device
    -s, --serial SERIAL     directs the command to the device or emulator with the given serial number or qualifier.
                            Overrides ANDROID_SERIAL environment variable.
    -l                      For long list format, only valid for "ls" command
    -R                      For recursive directory listing, only valid for "ls" command
    -v, --verbose           Verbose mode

"""

_KEYCODE_BACK = 4
_MIN_API_FOR_RUNTIME_PERMISSIONS = 23

_verbose = False
_adb_prefix = 'adb'


def main():
    global _verbose
    global _adb_prefix
    args = docopt.docopt(USAGE_STRING, version='1.0.0rc2')

    validate_options(args)
    options = ''
    if args['--emulator']:
        options += '-e '
    if args['--device']:
        options += '-d '
    if args['--serial']:
        options += '-s %s ' % args['--serial']
    _verbose = args['--verbose']

    if len(options) > 0:
        _adb_prefix = '%s %s' % (_adb_prefix, options)

    if args['rotate']:
        direction = 'portrait' if args['portrait'] else \
            'landscape' if args['landscape'] else \
                'left' if args['left'] else \
                    'right'
        handle_rotate(direction)
    elif args['gfx']:
        value = 'on' if args['on'] else \
            ('off' if args['off'] else
             'lines')
        handle_gfx(value)
    elif args['overdraw']:
        value = 'on' if args['on'] else \
            ('off' if args['off'] else
             'deut')
        handle_overdraw(value)
    elif args['layout']:
        value = args['on']
        handle_layout(value)
    elif args['airplane']:
        # This does not always work
        value = args['on']
        handle_airplane(value)
    elif args['battery']:
        if args['saver']:
            handle_battery_saver(args['on'])
        elif args['level']:
            handle_battery_level(int(args['<percentage>']))
        elif args['reset']:
            handle_battery_reset()
    elif args['doze']:
        handle_doze(args['on'])
    elif args['jank']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        handle_get_jank(app_name)
    elif args['devices']:
        handle_list_devices()
    elif args['top-activity']:
        print_top_activity()
    elif args['dump-ui']:
        dump_ui(args['<xml_file>'])
    elif args['force-stop']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        force_stop(app_name)
    elif args['clear-data']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        clear_disk_data(app_name)
    elif args['mobile-data']:
        if args['saver']:
            handle_mobile_data_saver(args['on'])
        else:
            handle_mobile_data(args['on'])
    elif args['rtl']:
        # This is not working as expected
        force_rtl(args['on'])
    elif args['screenshot']:
        dump_screenshot(args['<filename.png>'])
    elif args['screenrecord']:
        dump_screenrecord(args['<filename.mp4>'])
    elif args['dont-keep-activities']:
        handle_dont_keep_activities_in_background(args['on'])
    elif args['animations']:
        toggle_animations(args['on'])
    elif args['input-text']:
        input_text(args['<text>'])
    elif args['back']:
        press_back()
    elif args['open-url']:
        url = args['<url>']
        open_url(url)
    elif args['permission-groups'] and args['list'] and args['all']:
        list_permission_groups()
    elif args['permissions'] and args['list']:
        list_permissions(args['dangerous'])
    elif args['permissions']:
        android_api_version = _get_device_android_api_version()
        if android_api_version < _MIN_API_FOR_RUNTIME_PERMISSIONS:
            print_error_and_exit(
                'Runtime permissions are supported only on API %d and above, your version is %d' %
                (_MIN_API_FOR_RUNTIME_PERMISSIONS, android_api_version))
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        permission_group = get_permission_group(args)
        permissions = get_permissions_in_permission_group(permission_group)
        grant_or_revoke_runtime_permissions(
            app_name, args['grant'], permissions)
    elif args['standby-bucket']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        if args['get']:
            get_standby_bucket(app_name)
        elif args['set']:
            set_standby_bucket(app_name, _calculate_standby_mode(args))
    elif args['restrict-background']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        apply_or_remove_background_restriction(app_name, args['true'])
    elif args['ls']:
        file_path = args['<file_path>']
        long_format = args['-l']
        recursive = args['-R']
        list_directory(file_path, long_format, recursive)
    elif args['pull']:
        remote_file_path = args['<remote>']
        local_file_path = args['<local>']
        copy_ancillary = args['-a']
        pull_file(remote_file_path, local_file_path, copy_ancillary)
    elif args['cat']:
        file_path = args['<file_path>']
        cat_file(file_path)
    elif args['start']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        launch_app(app_name)
    elif args['stop']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        stop_app(app_name)
    elif args['restart']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        stop_app(app_name)
        launch_app(app_name)
    elif args['app-info']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        print_app_info(app_name)
    elif args['print-apk-path']:
        app_name = args['<app_name>']
        _ensure_package_exists(app_name)
        print_app_path(app_name)
    else:
        print_error_and_exit('Not implemented: "%s"' % ' '.join(sys.argv))


def validate_options(args):
    count = 0
    if args['--emulator']:
        count += 1
    if args['--device']:
        count += 1
    if args['--serial']:
        count += 1
    if count > 1:
        print_error_and_exit('Only one out of -e, -d, or -s can be provided')


# Source:
# https://github.com/dhelleberg/android-scripts/blob/master/src/devtools.groovy
def handle_gfx(value):
    if value == 'on':
        cmd = 'setprop debug.hwui.profile visual_bars'
    elif value == 'off':
        cmd = 'setprop debug.hwui.profile false'
    elif value == 'lines':
        cmd = 'setprop debug.hwui.profile visual_lines'
    else:
        print_error_and_exit('Unexpected value for gfx %s' % value)
        return

    execute_adb_shell_command_and_poke_activity_service(cmd)


# Source: https://github.com/dhelleberg/android-scripts/blob/master/src/devtools.groovy
# https://plus.google.com/+AladinQ/posts/dpidzto1b8B
def handle_overdraw(value):
    version = _get_device_android_api_version()
    if version < 19:
        if value is 'on':
            cmd = 'setprop debug.hwui.show_overdraw true'
        elif value is 'off':
            cmd = 'setprop debug.hwui.show_overdraw false'
        elif value is 'deut':
            print_error_and_exit(
                'This command is not support on API %d' % version)
        else:
            print_error_and_exit('Unexpected value for overdraw %s' % value)
    else:
        if value is 'on':
            cmd = 'setprop debug.hwui.overdraw show'
        elif value is 'off':
            cmd = 'setprop debug.hwui.overdraw false'
        elif value is 'deut':
            cmd = 'setprop debug.hwui.overdraw show_deuteranomaly'
        else:
            print_error_and_exit('Unexpected value for overdraw %s' % value)
            return

    execute_adb_shell_command_and_poke_activity_service(cmd)


# Source:
# https://stackoverflow.com/questions/25864385/changing-android-device-orientation-with-adb
def handle_rotate(direction):
    disable_acceleration = 'settings put system accelerometer_rotation 0'
    execute_adb_shell_command(disable_acceleration)

    if direction is 'portrait':
        new_direction = 0
    elif direction is 'landscape':
        new_direction = 1
    elif direction is 'left':
        current_direction = get_current_rotation_direction()
        print_verbose("Current direction: %s" % current_direction)
        if current_direction is None:
            return
        new_direction = (current_direction + 1) % 4
    elif direction is 'right':
        current_direction = get_current_rotation_direction()
        print_verbose("Current direction: %s" % current_direction)
        if current_direction is None:
            return
        new_direction = (current_direction - 1) % 4
    else:
        print_error_and_exit('Unexpected direction %s' % direction)
        return

    cmd = 'settings put system user_rotation %s' % new_direction
    execute_adb_shell_command(cmd)


def get_current_rotation_direction():
    cmd = 'settings get system user_rotation'
    direction = execute_adb_shell_command(cmd)
    print_verbose("Return value is %s" % direction)
    if not direction or direction == 'null':
        return 0  # default direction is 0, vertical straight
    try:
        return int(direction)
    except ValueError as e:
        print_error("Failed to get direction, error: \"%s\"" % e)


def handle_layout(value):
    if value:
        cmd = 'setprop debug.layout true'
    else:
        cmd = 'setprop debug.layout false'
    execute_adb_shell_command_and_poke_activity_service(cmd)


# Source: https://stackoverflow.com/questions/10506591/turning-airplane-mode-on-via-adb
# This is incomplete
def handle_airplane(turn_on):
    if turn_on:
        cmd = 'settings put global airplane_mode_on 1'
    else:
        cmd = 'settings put global airplane_mode_on 0'

    broadcast_change = 'am broadcast -a android.intent.action.AIRPLANE_MODE'
    execute_adb_shell_command(cmd)
    execute_adb_shell_command(broadcast_change)


# Source:
# https://stackoverflow.com/questions/28234502/programmatically-enable-disable-battery-saver-mode
def handle_battery_saver(turn_on):
    if turn_on:
        cmd = 'settings put global low_power 1'
    else:
        cmd = 'settings put global low_power 0'

    execute_adb_shell_command(get_battery_unplug_cmd())
    execute_adb_shell_command(get_battery_discharging_cmd())
    execute_adb_shell_command(cmd)


# Source:
# https://stackoverflow.com/questions/28234502/programmatically-enable-disable-battery-saver-mode
def handle_battery_level(level):
    if level < 0 or level > 100:
        print_error_and_exit(
            'Battery percentage %d is outside the valid range of 0 to 100' %
            level)
    cmd = 'dumpsys battery set level %d' % level

    execute_adb_shell_command(get_battery_unplug_cmd())
    execute_adb_shell_command(get_battery_discharging_cmd())
    execute_adb_shell_command(cmd)


# Source:
# https://stackoverflow.com/questions/28234502/programmatically-enable-disable-battery-saver-mode
def handle_battery_reset():
    cmd = 'dumpsys battery reset'
    execute_adb_shell_command(cmd)


# https://developer.android.com/training/monitoring-device-state/doze-standby.html
def handle_doze(turn_on):
    if turn_on:
        cmd = 'dumpsys deviceidle force-idle'
        execute_adb_shell_command(get_battery_unplug_cmd())
        execute_adb_shell_command(get_battery_discharging_cmd())
        execute_adb_shell_command(cmd)
    else:
        cmd = 'dumpsys deviceidle unforce'
        execute_adb_shell_command(handle_battery_reset())
        execute_adb_shell_command(cmd)


# Source: https://github.com/dhelleberg/android-scripts/blob/master/src/devtools.groovy
# Ref:
# https://gitlab.com/SaberMod/pa-android-frameworks-base/commit/a53de0629f3b94472c0f160f5bbe1090b020feab
def get_update_activity_service_cmd():
    # Note: 1599295570 == ('_' << 24) | ('S' << 16) | ('P' << 8) | 'R'
    return 'service call activity 1599295570'


# This command puts the battery in discharging mode (most likely this is
# Android 6.0 onwards only)
def get_battery_discharging_cmd():
    return 'dumpsys battery set status 3'


def get_battery_unplug_cmd():
    return 'dumpsys battery unplug'


def handle_get_jank(app_name):
    cmd = 'dumpsys gfxinfo %s ' % app_name
    execute_adb_shell_command(cmd, 'grep Janky')


def handle_list_devices():
    s1 = execute_adb_command('devices -l')
    # Skip the first line, it says "List of devices attached"
    device_infos = s1.split('\n')[1:]

    if len(device_infos) == 0 or (
            len(device_infos) == 1 and len(device_infos[0]) == 0):
        print_error_and_exit('No attached Android device found')
    elif len(device_infos) == 1:
        _print_device_info()
    else:
        for device_info in device_infos:
            if len(device_info) == 0:
                continue
            device_serial = device_info.split()[0]
            if 'unauthorized' in device_info:
                device_info = ' '.join(device_info.split()[1:])
                print_error(
                ('Unlock Device "%s" and give USB debugging access to ' +
                        'this PC/Laptop by unlocking and reconnecting ' +
                        'the device. More info about this device: "%s"') % (
                                device_serial, device_info))
            else:
                _print_device_info(device_serial)


def _print_device_info(device_serial=None):
    cmd_prefix = ''
    if device_serial is not None:
        cmd_prefix = '-s %s' % device_serial

    manufacturer = execute_adb_command(
        '%s shell getprop ro.product.manufacturer' %
        cmd_prefix)
    model = execute_adb_command(
        '%s shell getprop ro.product.model' %
        cmd_prefix)
    # This worked on 4.4.3 API 19 Moto E
    display_name = execute_adb_command(
        '%s shell getprop ro.product.display' %
        cmd_prefix)
    # First fallback: undocumented
    if display_name is None or len(display_name) == 0 or display_name == 'null':
        # This works on 4.4.4 API 19 Galaxy Grand Prime
        display_name = execute_adb_command('%s shell settings get system device_name' % cmd_prefix)
    # Second fallback, documented to work on API 25 and above
    # Source: https://developer.android.com/reference/android/provider/Settings.Global.html#DEVICE_NAME
    if display_name is None or len(display_name) == 0 or display_name == 'null':
        display_name = execute_adb_command('%s shell settings get global device_name' % cmd_prefix)

    # ABI info
    abi = execute_adb_command(
            '%s shell getprop ro.product.cpu.abi' % cmd_prefix)

    release = execute_adb_command(
        '%s shell getprop ro.build.version.release' %
        cmd_prefix)
    sdk = execute_adb_command(
        '%s shell getprop ro.build.version.sdk' %
        cmd_prefix)
    print_message(
        'Serial ID: %s\nManufacturer: %s\nModel: %s (%s)\nRelease: %s\nSDK version: %s\nCPU: %s\n' %
        (device_serial, manufacturer, model, display_name, release, sdk, abi))


def print_top_activity():
    cmd = 'dumpsys window windows'
    output = execute_adb_shell_command(cmd)
    result = ''
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('mCurrentFocus') or line.startswith('mFocusedApp'):
            result = result + line + '\n'
    print(result)


def dump_ui(xml_file):
    tmp_file = _create_tmp_file(xml_file, 'xml')
    cmd1 = 'uiautomator dump %s' % tmp_file
    cmd2 = 'pull %s %s' % (tmp_file, xml_file)
    cmd3 = 'rm %s' % tmp_file

    print_verbose('Writing UI to %s' % tmp_file)
    execute_adb_shell_command(cmd1)
    print_verbose('Pulling file %s' % xml_file)
    execute_adb_command(cmd2)
    print_verbose('Deleting file %s' % tmp_file)
    print_message('XML UI dumped to %s, you might want to format it using \"xmllint --format %s\"' %
                  (xml_file, xml_file))
    execute_adb_shell_command(cmd3)


def force_stop(app_name):
    cmd = 'am force-stop %s' % app_name
    print_message(execute_adb_shell_command(cmd))


def clear_disk_data(app_name):
    cmd = 'pm clear %s' % app_name
    execute_adb_shell_command(cmd)


# Source:
# https://stackoverflow.com/questions/26539445/the-setmobiledataenabled-method-is-no-longer-callable-as-of-android-l-and-later
def handle_mobile_data(turn_on):
    if turn_on:
        cmd = 'svc data enable'
    else:
        cmd = 'svc data disable'
    execute_adb_shell_command(cmd)


def force_rtl(turn_on):
    if turn_on:
        cmd = 'settings put global debug.force_rtl 1'
    else:
        cmd = 'settings put global debug.force_rtl 0'
    execute_adb_shell_command_and_poke_activity_service(cmd)


def dump_screenshot(filepath):
    file_path_on_device = _create_tmp_file('screenshot', 'png')
    dump_cmd = 'screencap -p %s ' % file_path_on_device
    execute_adb_shell_command(dump_cmd)
    pull_cmd = 'pull %s %s' % (file_path_on_device, filepath)
    execute_adb_command(pull_cmd)
    del_cmd = 'rm %s' % file_path_on_device
    execute_adb_shell_command(del_cmd)


def dump_screenrecord(filepath):
    file_path_on_device = _create_tmp_file('screenrecord', 'mp4')
    dump_cmd = 'screenrecord %s --time-limit 10 ' % file_path_on_device
    execute_adb_shell_command(dump_cmd)
    pull_cmd = 'pull %s %s' % (file_path_on_device, filepath)
    execute_adb_command(pull_cmd)
    del_cmd = 'rm %s' % file_path_on_device
    execute_adb_shell_command(del_cmd)


# https://developer.android.com/training/basics/network-ops/data-saver.html
def handle_mobile_data_saver(turn_on):
    if turn_on:
        cmd = 'cmd netpolicy set restrict-background true'
    else:
        cmd = 'cmd netpolicy set restrict-background false'
    execute_adb_shell_command(cmd)


# Ref: https://github.com/android/platform_packages_apps_settings/blob/4ce19f5c4fd40f3bedc41d3fbcbdede8b2614501/src/com/android/settings/DevelopmentSettings.java#L2123
# adb shell settings put global always_finish_activities true might not work on all Android versions.
# It was in system (not global before ICS)
# adb shell service call activity 43 i32 1 followed by that
def handle_dont_keep_activities_in_background(turn_on):
    # Till Api 25, the value was True/False, above API 25, 1/0 work. Source: manual testing
    if _get_device_android_api_version() <= 25:
        use_true_false_as_value = True
    else:
        use_true_false_as_value = False

    if turn_on:
        value = 'true' if use_true_false_as_value else '1'
        cmd1 = 'settings put global always_finish_activities %s' % value
        cmd2 = 'service call activity 43 i32 1'
    else:
        value = 'false' if use_true_false_as_value else '0'
        cmd1 = 'settings put global always_finish_activities %s' % value
        cmd2 = 'service call activity 43 i32 0'
    execute_adb_shell_command(cmd1)
    execute_adb_shell_command_and_poke_activity_service(cmd2)


def toggle_animations(turn_on):
    if turn_on:
        value = 1
    else:
        value = 0

    # Source: https://github.com/jaredsburrows/android-gif-example/blob/824c493285a2a2cf22f085662431cf0a7aa204b8/.travis.yml#L34
    cmd1 = 'settings put global window_animation_scale %d' % value
    cmd2 = 'settings put global transition_animation_scale %d' % value
    cmd3 = 'settings put global animator_duration_scale %d' % value

    execute_adb_shell_command(cmd1)
    execute_adb_shell_command(cmd2)
    execute_adb_shell_command(cmd3)


def input_text(text):
    cmd = 'input text %s' % text
    execute_adb_shell_command(cmd)


def press_back():
    cmd = 'input keyevent 4'
    execute_adb_shell_command(cmd)


def open_url(url):
    # Let's not do any URL encoding for now, if required, we will add that in the future.
    cmd = 'am start -a android.intent.action.VIEW -d %s' % url
    execute_adb_shell_command(cmd)


def list_permission_groups():
    cmd = 'pm list permission-groups'
    print_message(execute_adb_shell_command(cmd))


def list_permissions(dangerous_only_permissions):
    # -g is to group permissions by permission groups.
    if dangerous_only_permissions:
        # -d => dangerous only permissions
        cmd = 'pm list permissions -g -d'
    else:
        cmd = 'pm list permissions -g'
    print_message(execute_adb_shell_command(cmd))


def _ensure_package_exists(package_name):
    if not _package_exists(package_name):
        print_error_and_exit("Package %s does not exist" % package_name)


def _package_exists(package_name):
    cmd = 'pm path %s' % package_name
    response = execute_adb_shell_command(cmd)
    return response is not None and len(response.strip()) != 0

def _create_tmp_file(filename_prefix = None, filename_suffix = None):
    if filename_prefix is None:
        filename_prefix = 'file'
    if filename_suffix is None:
        filename_suffix = 'tmp'
    filepath_on_device = '/sdcard/%s-%d.%s' % (
        filename_prefix, random.randint(1, 1000 * 1000 * 1000), filename_suffix)
    if _file_exists(filepath_on_device):
        # Retry if the file already exists
        print_verbose('Tmp File %s already exists, trying a new random name' % filepath_on_device)
        return _create_tmp_file(filename_prefix, filename_suffix)
    return filepath_on_device


# Returns true if the file_path exists on the device, false if it does not exists or is inaccessible.
def _file_exists(file_path):
    exists_cmd = "'ls %s > /dev/null && echo exists'" % file_path
    exists_cmd = _may_be_wrap_with_run_as(exists_cmd, file_path)
    output = execute_adb_shell_command(exists_cmd, ignore_stderr=True)
    return output.find('exists') != -1


def _is_sqlite_database(file_path):
    return file_path.endswith('.db')


# Returns a fully-qualified permission group name.
def get_permission_group(args):
    if args['contacts']:
        return 'android.permission-group.CONTACTS'
    elif args['phone']:
        return 'android.permission-group.PHONE'
    elif args['calendar']:
        return 'android.permission-group.CALENDAR'
    elif args['camera']:
        return 'android.permission-group.CAMERA'
    elif args['sensors']:
        return 'android.permission-group.SENSORS'
    elif args['location']:
        return 'android.permission-group.LOCATION'
    elif args['storage']:
        return 'android.permission-group.STORAGE'
    elif args['microphone']:
        return 'android.permission-group.MICROPHONE'
    elif args['sms']:
        return 'android.permission-group.SMS'
    else:
        print_error_and_exit('Unexpected permission group: %s' % args)


# Pass the full-qualified permission group name to this method.
def get_permissions_in_permission_group(permission_group):
    # List permissions by group
    permission_output = execute_adb_shell_command('pm list permissions -g')
    # Remove ungrouped permissions section completely.
    if 'ungrouped:' in permission_output:
        permission_output, _ = permission_output.split('ungrouped:')
    splits = permission_output.split('group:')
    for split in splits:
        if split.startswith(permission_group):
            potential_permissions = split.split('\n')
            # Ignore the first entry which is the group name
            potential_permissions = potential_permissions[1:]
            # Filter out empty lines.
            permissions = filter(
                lambda x: len(
                    x.strip()) > 0,
                potential_permissions)
            permissions = list(map(
                lambda x: x.replace(
                    'permission:', ''), permissions))
            print_message(
                'Permissions in %s group are %s' %
                (permission_group, permissions))
            return permissions


def grant_or_revoke_runtime_permissions(
        package_name, action_grant, permissions):
    if action_grant:
        cmd = 'pm grant %s' % package_name
    else:
        cmd = 'pm revoke %s' % package_name
    for permission in permissions:
        execute_adb_shell_command(cmd + ' ' + permission)


# Source: https://developer.android.com/reference/android/app/usage/UsageStatsManager#STANDBY_BUCKET_ACTIVE
_APP_STANDBY_BUCKETS = {
    10: 'active',
    20: 'working',
    30: 'frequent',
    40: 'rare',
}


# Source: https://developer.android.com/preview/features/power#buckets
def get_standby_bucket(package_name):
    api_version = _get_device_android_api_version()
    if api_version < 28:
        print_error_and_exit(
            'This command cannot be executed below API version 28, your Android version is %s' %
            api_version)
    cmd = 'am get-standby-bucket %s' % package_name
    result = execute_adb_shell_command(cmd)
    if result is None:
        print_error_and_exit('Unknown')
    print_verbose('App standby bucket for \"%s\" is %s' %(
        package_name, _APP_STANDBY_BUCKETS.get(int(result), 'unknown')))
    print(_APP_STANDBY_BUCKETS.get(int(result), 'unknown'))


def set_standby_bucket(package_name, mode):
    api_version = _get_device_android_api_version()
    if api_version < 28:
        print_error_and_exit(
            'This command cannot be executed below API version 28, your Android version is %s' %
            api_version)
    cmd = 'am set-standby-bucket %s %s' % (package_name, mode)
    result = execute_adb_shell_command(cmd)
    if result is not None:  # Expected
        print_error_and_exit(result)


def _calculate_standby_mode(args):
    if args['active']:
        return 'active'
    elif args['working_set']:
        return 'working_set'
    elif args['frequent']:
        return 'frequent'
    elif args['rare']:
        return 'rare'
    else:
        raise ValueError('Illegal argument: %s' % args)


# Source: https://developer.android.com/preview/features/power
def apply_or_remove_background_restriction(package_name, set_restriction):
    api_version = _get_device_android_api_version()
    if api_version < 28:
        print_error_and_exit(
            'This command cannot be executed below API version 28, your Android version is %s' %
            api_version)

    appops_cmd = 'cmd appops set %s RUN_ANY_IN_BACKGROUND %s' % (
        package_name, 'ignore' if set_restriction else 'allow')
    execute_adb_shell_command(appops_cmd)


def list_directory(file_path, long_format, recursive):
    cmd_prefix = 'ls'
    if long_format:
        cmd_prefix += ' -l'
    if recursive:
        cmd_prefix += ' -R'
    cmd = '%s %s' % (cmd_prefix, file_path)
    cmd = _may_be_wrap_with_run_as(cmd, file_path)

    print_message(execute_adb_shell_command(cmd))


# Copies from remote_file_path on Android to local_file_path on the disk
# local_file_path can be None
def pull_file(remote_file_path, local_file_path, copy_ancillary = False):
    if not _file_exists(remote_file_path):
        print_error_and_exit('File %s does not exist' % remote_file_path)

    if local_file_path is None:
        local_file_path = remote_file_path.split('/')[-1]
        print_verbose('Local file path not provided, using \"%s\" for that' % local_file_path)

    tmp_file = _create_tmp_file()
    cp_cmd = 'cp -r %s %s' % (remote_file_path, tmp_file)
    wrapped_cp_cmd = _may_be_wrap_with_run_as(cp_cmd, remote_file_path)
    if cp_cmd == wrapped_cp_cmd:
        # cp command is not required at all, if copying it is not required.
        pull_cmd = 'pull %s %s' % (remote_file_path, local_file_path)
        execute_adb_command(pull_cmd)
    else:
        # First copy the files to sdcard, then pull them out, and then delete them from sdcard.
        execute_adb_shell_command(wrapped_cp_cmd)
        pull_cmd = 'pull %s %s' % (tmp_file, local_file_path)
        execute_adb_command(pull_cmd)
        del_cmd = 'rm -r %s' % tmp_file
        execute_adb_shell_command(del_cmd)

    print_message('Copying remote file \"%s\" to local file \"%s\" (Size: %d bytes)' % (
        remote_file_path,
        local_file_path,
        os.path.getsize(local_file_path)))

    if _is_sqlite_database(remote_file_path):
        # Copy temporary Sqlite files
        # Source :https://ashishb.net/all/android-the-right-way-to-pull-sqlite-database-from-the-device/
        for suffix in ['wal', 'journal', 'shm']:
            tmp_db_file = '%s-%s' % (remote_file_path, suffix)
            if not _file_exists(tmp_db_file):
                continue
            if copy_ancillary:
                pull_file(tmp_db_file, '%s-%s' %(local_file_path, suffix), copy_ancillary=True)
            else:
                print_error('File \"%s\" has an ancillary file \"%s\" which should be copied.\nSee %s for details'
                            % (remote_file_path, tmp_db_file,
                               'https://ashishb.net/all/android-the-right-way-to-pull-sqlite-database-from-the-device/'))


def cat_file(file_path):
    cmd_prefix = 'cat'
    cmd = '%s %s' % (cmd_prefix, file_path)
    cmd = _may_be_wrap_with_run_as(cmd, file_path)
    print_message(execute_adb_shell_command(cmd))


def _may_be_wrap_with_run_as(cmd, file_path):
    # This is hacky but works for the cases I am looking for.
    if file_path.startswith('/data/data/'):
        run_as_package = file_path.split('/')[3]
        if run_as_package is not None and len(run_as_package.strip()) > 0:
            print_verbose('Running as package: %s' % run_as_package)
            cmd = 'run-as %s %s' % (run_as_package, cmd)
    return cmd


# Source: https://stackoverflow.com/a/25398877
def launch_app(app_name):
    adb_shell_cmd = 'monkey -p %s -c android.intent.category.LAUNCHER 1' % app_name
    execute_adb_shell_command(adb_shell_cmd)


def stop_app(app_name):
    # Below API 21, stop does not kill app in the foreground.
    # Above API 21, it seems it does.
    if _get_device_android_api_version() < 21:
        force_stop(app_name)
    else:
        adb_shell_cmd = 'am kill %s' % app_name
        execute_adb_shell_command(adb_shell_cmd)


def _regex_extract(regex, data):
    regex_object = re.search(regex, data, re.IGNORECASE)
    if regex_object is None:
        return None
    else:
        return regex_object.group(1)


# adb shell pm dump <app_name> produces about 1200 lines, mostly useless,
# compared to this.
def print_app_info(app_name):
    app_info_dump = execute_adb_shell_command('dumpsys package %s' % app_name)
    version_code = _regex_extract('versionCode=(\\d+)?', app_info_dump)
    version_name = _regex_extract('versionName=([\\d.]+)?', app_info_dump)
    min_sdk_version = _regex_extract('minSdk=(\\d+)?', app_info_dump)
    target_sdk_version = _regex_extract('targetSdk=(\\d+)?', app_info_dump)
    max_sdk_version = _regex_extract('maxSdk=(\\d+)?', app_info_dump)
    installer_package_name = _regex_extract('installerPackageName=(\\S+)?', app_info_dump)
    is_debuggable = re.search(
        'pkgFlags.*DEBUGGABLE',
        app_info_dump,
        re.IGNORECASE) is not None

    msg = ''
    msg += 'App name: %s\n' % app_name
    msg += 'Version: %s\n' % version_name
    msg += 'Version Code: %s\n' % version_code
    msg += 'Is debuggable: %r\n' % is_debuggable
    msg += 'Min SDK version: %s\n' % min_sdk_version
    msg += 'Target SDK version: %s\n' % target_sdk_version
    if max_sdk_version is not None:
        msg += 'Max SDK version: %s\n' % max_sdk_version

    if _get_device_android_api_version() >= 23:
        msg += _get_permissions_info_above_api_23(app_info_dump)
    else:
        msg += _get_permissions_info_below_api_23(app_info_dump)

    msg += 'Installer package name: %s\n' % installer_package_name

    # TODO: Consider adding printing the signing key support to this in the
    # future.
    print_message(msg)

# API < 23 have no runtime permissions
def _get_permissions_info_below_api_23(app_info_dump):
    install_time_permissions_regex = re.search('grantedPermissions:(.*)', app_info_dump,
                                               re.IGNORECASE | re.DOTALL)
    if install_time_permissions_regex is None:
        install_time_permissions_string = []
    else:
        install_time_permissions_string = install_time_permissions_regex.group(1).split('\n')

    install_time_granted_permissions = []
    install_time_permissions_string = filter(None, install_time_permissions_string)
    for permission_string in install_time_permissions_string:
        install_time_granted_permissions.append(permission_string)

    permissions_info_msg = ''
    if len(install_time_granted_permissions) > 0:
        permissions_info_msg += 'Install time granted permissions:\n%s\n\n' % '\n'.join(
            install_time_granted_permissions)
    return permissions_info_msg

# API 23 and have runtime permissions
def _get_permissions_info_above_api_23(app_info_dump):
    requested_permissions_regex = \
        re.search('requested permissions:(.*)install permissions:', app_info_dump, re.IGNORECASE | re.DOTALL)
    if requested_permissions_regex is None:
        requested_permissions_regex = re.search('requested permissions:(.*)runtime permissions:', app_info_dump,
                                                re.IGNORECASE | re.DOTALL)
    if requested_permissions_regex is None:
        requested_permissions = []  # No permissions requested by the app.
    else:
        requested_permissions = requested_permissions_regex.group(1).split('\n')
    install_time_permissions_regex = re.search('install permissions:(.*)runtime permissions:', app_info_dump,
                                               re.IGNORECASE | re.DOTALL)
    if install_time_permissions_regex is None:
        install_time_permissions_string = []
    else:
        install_time_permissions_string = install_time_permissions_regex.group(1).split('\n')
    # Remove empty entries
    requested_permissions = list(filter(None, requested_permissions))
    install_time_permissions_string = filter(None, install_time_permissions_string)
    install_time_granted_permissions = []
    install_time_denied_permissions = []  # This will most likely remain empty
    for permission_string in install_time_permissions_string:
        if permission_string.find('granted=true') >= 0:
            permission, _ = permission_string.split(':')
            install_time_granted_permissions.append(permission)
        elif permission_string.find('granted=false') >= 0:
            permission, _ = permission_string.split(':')
            install_time_denied_permissions.append(permission)
    runtime_denied_permissions = []
    runtime_granted_permissions = []
    for permission in requested_permissions:
        if permission in install_time_granted_permissions or permission in install_time_denied_permissions:
            continue
        granted_pattern = '%s: granted=true' % permission
        denied_pattern = '%s: granted=false' % permission
        if app_info_dump.find(granted_pattern) >= 0:
            runtime_granted_permissions.append(permission)
        elif app_info_dump.find(denied_pattern) >= 0:
            runtime_denied_permissions.append(permission)
    runtime_not_granted_permissions = list(filter(
        lambda p: p not in runtime_granted_permissions and
                  p not in runtime_denied_permissions and
                  p not in install_time_granted_permissions and
                  p not in install_time_denied_permissions, requested_permissions))

    permissions_info_msg = ''
    permissions_info_msg += '\nPermissions:\n\n'
    if len(install_time_granted_permissions) > 0:
        permissions_info_msg += 'Install time granted permissions:\n%s\n\n' % '\n'.join(
            install_time_granted_permissions)
    if len(install_time_denied_permissions) > 0:
        permissions_info_msg += 'Install time denied permissions:\n%s\n\n' % '\n'.join(
            install_time_denied_permissions)
    if len(runtime_granted_permissions) > 0:
        permissions_info_msg += 'Runtime granted permissions:\n%s\n\n' % '\n'.join(
            runtime_granted_permissions)
    if len(runtime_denied_permissions) > 0:
        permissions_info_msg += 'Runtime denied permissions:\n%s\n\n' % '\n'.join(
            runtime_denied_permissions)
    if len(runtime_not_granted_permissions) > 0:
        permissions_info_msg += 'Runtime Permissions not granted and not yet requested:\n%s\n\n' % '\n'.join(
            runtime_not_granted_permissions)
    return permissions_info_msg


def print_app_path(app_name):
    adb_shell_cmd = 'pm path %s' % app_name
    str = execute_adb_shell_command(adb_shell_cmd)
    apk_path = str.split(':', 2)[1]
    print_verbose('Path for %s is %s' % (app_name, apk_path))
    print(str)


def execute_adb_shell_command_and_poke_activity_service(adb_cmd):
    return_value = execute_adb_shell_command(adb_cmd)
    execute_adb_shell_command(get_update_activity_service_cmd())
    return return_value


def execute_adb_shell_command(adb_cmd, piped_into_cmd=None, ignore_stderr=False):
    return execute_adb_command('shell %s' % adb_cmd, piped_into_cmd, ignore_stderr)


def execute_adb_command(adb_cmd, piped_into_cmd=None, ignore_stderr=False):
    final_cmd = ('%s %s' % (_adb_prefix, adb_cmd))
    if piped_into_cmd:
        print_verbose("Executing \"%s | %s\"" % (final_cmd, piped_into_cmd))
        ps1 = subprocess.Popen(final_cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=None if ignore_stderr is False else open(os.devnull, 'w'))
        output = subprocess.check_output(
            piped_into_cmd, shell=True, stdin=ps1.stdout)
        print_message(output)
        return output
    else:
        print_verbose("Executing \"%s\"" % final_cmd)
        ps1 = subprocess.Popen(final_cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=None if ignore_stderr is False else open(os.devnull, 'w'))
        output = ''
        first_line = True
        for line in ps1.stdout:
            if first_line:
                output += line.decode('utf-8').strip()
                first_line = False
            else:
                output += '\n' + line.decode('utf-8').strip()
        print_verbose("Result is \"%s\"" % output)
        return output


# adb shell getprop ro.build.version.sdk
def _get_device_android_api_version():
    version_string = _get_prop('ro.build.version.sdk')
    if version_string is None:
        return -1
    return int(version_string)


def _get_prop(property_name):
    return execute_adb_shell_command('getprop %s' % property_name)


def print_message(message):
    print(message)


def print_error_and_exit(error_string):
    print('%s%s%s' % (bcolors.FAIL, error_string, bcolors.ENDC))
    quit(1)


def print_error(error_string):
    print('%s%s%s' % (bcolors.FAIL, error_string, bcolors.ENDC))


def print_verbose(message):
    if _verbose:
        print('%s%s%s' % (bcolors.WARNING, message, bcolors.ENDC))


# Coloring approach inspired from https://stackoverflow.com/a/287944
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if __name__ == '__main__':
    main()
