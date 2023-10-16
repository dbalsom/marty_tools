##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Uwe Hermann <uwe@hermann-uwe.de>
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

class Pin:
    CLK, HS, VS = range(3)
    
class Annot:
    Frame, Scanline, X = range(3)

class TrackedValue:
    def __init__(self, initial_value=None):
        self.prev = None
        self.cur = initial_value

    def update(self, new_value):
        self.prev = self.cur
        self.cur = new_value
        return self

    def changed(self):
        return self.prev != self.cur

class Decoder(srd.Decoder):
    api_version = 3
    id = 'm6845'
    name = 'm6845'
    longname = 'Motorola M6845 CRTC'
    desc = 'Motorola M6845 CRT Controller'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Retrocomputing']
    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'CPU Clock'},      
        {'id': 'hs', 'name': 'HS', 'desc': 'Horizontal Sync'},
        {'id': 'vs', 'name': 'VS', 'desc': 'Vertical Sync'},    
    )
    options = (
        {'id': 'clock_divisor', 'desc': 'Clock divisor from source to hdot clock',
            'default': 3},
    )
    annotations = (
        # Warnings
        ('frame', 'Frame Number'),
        # Bits/bytes
        ('scanline', 'scanline number'),
        ('r_x', 'raster x position'),
    )
    annotation_rows = (
        ('frame', 'Frame', (0,)),
        ('scanline', 'Scanline', (1,)),
        ('r_x', 'RasterX', (2,)),
    )

    def __init__(self):
        self.reset()
        self.vs = False
        self.hs = False        
        self.r_x = 0;

        self.scanline_ss = TrackedValue()
        self.frame_ss = TrackedValue()
        
        self.last_ss = None
        self.clock_divisor = 3

    def reset(self):
        self.reset_variables()

    def reset_variables(self):
        self.frame = 0
        self.scanline = 0
        self.r_x = 0
        
    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        
        self.clock_divisor = chips[self.options['clock_divisor']]        
        
  
        

        
    def decode(self):
        
        
        while True:
            # Wait for rising edge on the CPU clock.
            pins = self.wait({Pin.CLK: 'r'})
            
            if pins[Pin.VS] == 0:
                # no VS
                if self.vs == True: 
                    # VS ending
                    self.vs = False
                    
                    self.frame_ss.update(self.samplenum)
                    
                    if self.frame_ss.prev is not None:
                        self.put(
                            self.frame_ss.prev, 
                            self.frame_ss.cur, 
                            self.out_ann, 
                            [Annot.Frame, ["{}".format(self.frame)]]
                        )          

                    self.frame += 1
                    self.scanline = 0                        
            else:
                # VS active
                self.vs = True
             
             
            if self.last_ss is not None:
                self.put(
                    self.last_ss, 
                    self.samplenum,
                    self.out_ann, 
                    [Annot.X, ["{}".format(self.r_x)]]
                ) 
                
            if pins[Pin.HS] == 0:
                # no HS
                if self.hs == True:
                    # HS ending
                    self.hs = False
                    
                    self.scanline_ss.update(self.samplenum)
                    
                    if self.scanline_ss.prev is not None:
                        self.put(
                            self.scanline_ss.prev, 
                            self.scanline_ss.cur, 
                            self.out_ann, 
                            [Annot.Scanline, ["{}".format(self.scanline)]]
                        )                           
                        
                    self.scanline += 1
                    self.r_x = 0
                        
            else:
                # HS active
                self.hs = True                        
            
            self.r_x += self.clock_divisor
            self.last_ss = self.samplenum
            
                 
                  
                    
                    
                