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

'''
This decoder stacks on top of the 'spi' PD and decodes the ST7920 Display
protocol as used by ST7920 display modules sporting an SPI interface, e.g.
as in an Ender 3 screen.

Datasheet referenced: https://www.waveshare.com/datasheet/LCD_en_PDF/ST7920.pdf
'''

from .pd import Decoder
