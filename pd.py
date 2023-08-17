##
## Copyright (C) 2023 Jim Keener <jim@jimkeener.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd
from common.sdcard import (cmd_names, acmd_names)

class Ann:
    BITS=0
    CMD=1
    DATA=2

class Decoder(srd.Decoder):
    api_version = 3
    id = 'st7920_spi'
    name = 'ST7920 Display (SPI mode)'
    longname = 'ST7920 (SPI mode)'
    desc = 'ST7920 (SPI mode)'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Memory']
    annotations = (
            ('bits', 'Bits'),
            ('cmd', 'Command'),
            ('data', 'data'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('cmd', 'Commands', (1,)),
        ('data', 'Data', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.ss, self.es = 0, 0
        self.ss_bit, self.es_bit = 0, 0
        self.ss_cmd, self.es_cmd = 0, 0
        self.ss_busy, self.es_busy = 0, 0
        self.cmd_token = []
        self.cmd_token_bits = []
        self.is_acmd = False # Indicates CMD vs. ACMD
        self.blocklen = 0
        self.read_buf = []
        self.cmd_str = ''
        self.is_cmd24 = False
        self.cmd24_start_token_found = False
        self.is_cmd17 = False
        self.cmd17_start_token_found = False
        self.busy_first_byte = False

        self.ann = Ann.BITS
        self.val = 0
        self.ann_start = 0
        self.extended = False
        self.vert_horz_addr = True
        self.scroll_ram_sel = True

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
    
    def decode(self, ss, es, data):
        ptype, mosi, miso = data

        if ptype not in ('DATA'):
            return

        if self.state == 'IDLE':
            if mosi == 0xF8:
                self.ann = Ann.CMD
                self.ann_start = ss
                self.state = 'CMD0'
                self.val = 0
            elif mosi == 0xFA:
                self.ann = Ann.DATA
                self.ann_start = ss
                self.state = 'DATA0'
                self.val = 0
            else:
                # Not sure what to do here
                pass
        elif self.state in ['CMD0', 'DATA0']:
            self.val = mosi & 0xF0
            self.state = self.state.replace('0', '1')
        elif self.state in ['CMD1', 'DATA1']:
            self.val += (mosi >> 4 )
            txt = f"{self.val:02X} "
            if self.state == 'DATA1':
                txt += chr(self.val)
            elif self.state == 'CMD1':
                if self.val & 0x80:
                    if self.extended:
                        txt += "Set GDRAM "
                        addr = 0
                        if self.vert_horz_addr:
                            txt += "Vert "
                            addr = self.val & 0x7F
                        else:
                            txt += "Horz "
                            addr = self.val & 0x0F
                        self.vert_horz_addr = not self.vert_horz_addr
                        txt += f"{addr:02X}"
                    else:
                        addr = self.val & 0x7F
                        txt += f"Set DRAM Addr {addr:02X}"
                elif self.val & 0x40:
                    if self.extended:
                        addr = 0
                        if self.scroll_ram_sel:
                            addr = self.val & 0x1F
                            txt += "Set Vert Addr {addr:02X"
                        else:
                            addr = self.val & 0x0F
                            txt += "Set Horz Addr {addr:02X}"
                    else:
                        addr = self.val & 0x3F
                        txt += f"Set CGRAM Addr {addr:02X}"
                elif self.val & 0x20:
                    txt += "Function Set "
                    if self.val & 0x10:
                        txt += "DL=1 8-bit "
                    else:
                        txt += "DL=0 4-bit "

                    if self.val & 0x08:
                        txt += "RE=1 Extended Instructions"
                        self.extended = True
                    else:
                        txt += "RE=0 Basic Instructions"
                        self.extended = False

                elif self.val & 0x10:
                    if self.extended:
                        txt += "0x10 not defined"
                    else:
                        sc = str(self.val & 0x08)
                        rl = str(self.val & 0x04)
                        txt += f"Cursor Control S/C={sc} R/L={rl}"

                elif self.val & 0x08:
                    txt += "Display On/Off "

                    if self.val & 0x04:
                        txt += "D=1 Display On "
                    else:
                        txt += "D=0 Display Off "

                    if self.val & 0x02:
                        txt += "C=1 Cursor On "
                    else:
                        txt += "C=0 Cursor Off "

                    if self.val & 0x01:
                        txt += "B=1 Blink On"
                    else:
                        txt += "B=0 Blink Off"

                elif self.val & 0x04:
                    if self.extended:
                        txt += "Reverse"
                    else:
                        txt += "Entry Mode "

                        if self.val & 0x02:
                            txt += "I/D=1 "
                        else:
                            txt += "I/D=0 "

                        if self.val & 0x01:
                            txt += "S=1"
                        else:
                            txt += "S=0"

                elif self.val & 0x02:
                    if self.extended:
                        self.scroll_ram_sel = self.val & 0x01
                        if self.scroll_ram_sel:
                            txt += "Vert Scroll Pos"
                        else:
                            txt += "I/CG Ram Addr"
                    else:
                        txt += "Home"
                elif self.val & 0x01:
                    if self.extended:
                        txt += "Stand By"
                    else:
                        txt += "Clear"

            self.put(self.ann_start, es, self.out_ann, [self.ann, [txt]])
            self.state = 'IDLE'

