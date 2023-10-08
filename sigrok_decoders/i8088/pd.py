##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2013-2016 Uwe Hermann <uwe@hermann-uwe.de>
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
from functools import reduce
from common.srdhelper import bitpack
from collections import deque
from .disasm import Disassembler

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>, <pdata>
 - 'ITEM', [<item>, <itembitsize>]
 - 'WORD', [<word>, <wordbitsize>, <worditemcount>]

<item>:
 - A single item (a number). It can be of arbitrary size. The max. number
   of bits in this item is specified in <itembitsize>.

<itembitsize>:
 - The size of an item (in bits). For a 4-bit parallel bus this is 4,
   for a 16-bit parallel bus this is 16, and so on.

<word>:
 - A single word (a number). It can be of arbitrary size. The max. number
   of bits in this word is specified in <wordbitsize>. The (exact) number
   of items in this word is specified in <worditemcount>.

<wordbitsize>:
 - The size of a word (in bits). For a 2-item word with 8-bit items
   <wordbitsize> is 16, for a 3-item word with 4-bit items <wordbitsize>
   is 12, and so on.

<worditemcount>:
 - The size of a word (in number of items). For a 4-item word (no matter
   how many bits each item consists of) <worditemcount> is 4, for a 7-item
   word <worditemcount> is 7, and so on.
'''

class ChannelError(Exception):
    pass

ADDRESS_LINES = ['ad0', 'ad1', 'ad2', 'ad3', 'ad4', 'ad5', 'ad6', 'ad7', 'a8', 'a9', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19']

ADDR_LEN = 20
PINS_LEN = 27

class Pin:
    AD0, AD1, AD2, AD3, AD4, AD5, AD6, AD7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18, A19, S0, S1, S2, QS0, QS1, RDY, CLK = range(PINS_LEN)

class Addr:
    AD0, AD1, AD2, AD3, AD4, AD5, AD6, AD7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18, A19 = range(ADDR_LEN)

class Status:
    S0, S1, S2 = 20, 21, 22

class TState:
    TI, T1, T2, T3, TW, T4 = range(6)

class Annot:
    ALE,AddrLatch,BusStatus,BusStatusL,QsF,QsS,QsE,TI,T1,T2,T3,TW,T4,D,F,Mm,Piq,Ib,Dbg,Err = range(20)

class BusStatus:
    INTA,IOR,IOW,HALT,CODE,MEMR,MEMW,PASV = range(8)

class QueueOp:
    Idle, First, Empty, Subs = range(4)

QUEUE_ANNOTS = [
    Annot.QsF,
    Annot.QsF,
    Annot.QsE,
    Annot.QsS,
]

BUS_STATES = [
    'INTA',
    'IOR',
    'IOW',
    'HALT',
    'CODE',
    'MEMR',
    'MEMW',
    'PASV',
]

QUEUE_STATES = [
    '.',
    'F',
    'E',
    'S',
]

T_ANNOTS = [
    Annot.TI, 
    Annot.T1, 
    Annot.T2, 
    Annot.T3, 
    Annot.TW, 
    Annot.T4
]

T_STATES = [
    'Ti',
    'T1',
    'T2',
    'T3',
    'Tw',
    'T4',
]

def reduce_bus(bus):
    if 0xFF in bus:
        return None # unassigned bus channels
    else:
        return reduce(lambda a, b: (a << 1) | b, reversed(bus))
    
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
    id = 'i8088'
    name = 'i8088'
    longname = 'Intel 8088 CPU'
    desc = 'Decoder for the Intel 8088 CPU'
    license = 'gplv2+'
    inputs = ['logic']
    outputs  = []
    tags = ['Retrocomputing']
    channels = (
        {'id': 'ad0', 'name': 'AD0', 'desc': 'Address/Data Line 0'},
        {'id': 'ad1', 'name': 'AD1', 'desc': 'Address/Data Line 1'},
        {'id': 'ad2', 'name': 'AD2', 'desc': 'Address/Data Line 2'},
        {'id': 'ad3', 'name': 'AD3', 'desc': 'Address/Data Line 3'},
        {'id': 'ad4', 'name': 'AD4', 'desc': 'Address/Data Line 4'},
        {'id': 'ad5', 'name': 'AD5', 'desc': 'Address/Data Line 5'},
        {'id': 'ad6', 'name': 'AD6', 'desc': 'Address/Data Line 6'},
        {'id': 'ad7', 'name': 'AD7', 'desc': 'Address/Data Line 7'},
        {'id': 'a8',  'name': 'A8',  'desc': 'Address Line 8'},
        {'id': 'a9',  'name': 'A9',  'desc': 'Address Line 9'},
        {'id': 'a10', 'name': 'A10', 'desc': 'Address Line 10'},
        {'id': 'a11', 'name': 'A11', 'desc': 'Address Line 11'},
        {'id': 'a12', 'name': 'A12', 'desc': 'Address Line 12'},
        {'id': 'a13', 'name': 'A13', 'desc': 'Address Line 13'},
        {'id': 'a14', 'name': 'A14', 'desc': 'Address Line 14'},
        {'id': 'a15', 'name': 'A15', 'desc': 'Address Line 15'},
        {'id': 'a16', 'name': 'A16', 'desc': 'Address Line 16'},
        {'id': 'a17', 'name': 'A17', 'desc': 'Address Line 17'},
        {'id': 'a18', 'name': 'A18', 'desc': 'Address Line 18'},
        {'id': 'a19', 'name': 'A19', 'desc': 'Address Line 19'},
        {'id': 's0',  'name': 'S0',  'desc': 'Status Line 0'},
        {'id': 's1',  'name': 'S1',  'desc': 'Status Line 1'},
        {'id': 's2',  'name': 'S2',  'desc': 'Status Line 2'},
        {'id': 'qs0', 'name': 'QS0', 'desc': 'Queue Status Line 0'},
        {'id': 'qs1', 'name': 'QS1', 'desc': 'Queue Status Line 1'},    
        {'id': 'rdy', 'name': 'RDY', 'desc': 'READY input'},
        {'id': 'clk', 'name': 'CLK', 'desc': 'CPU Clock'},       
    )
    options = ()
    annotations = (
        ('ale', 'Address Latch Enable'),
        ('address-latch', 'Address Latch'),
        ('bus-status', 'Bus Status'),
        ('bus-status-latch', 'Bus Status Latch'),
        ('qs-f', 'Queue Status: F'),
        ('qs-e', 'Queue Status: S'),
        ('qs-s', 'Queue Status: E'),
        ('ti', 'Ti'),
        ('t1', 'T1'),
        ('t2', 'T2'),
        ('t3', 'T3'),
        ('tw', 'Tw'),
        ('t4', 'T4'),
        ('d', 'Data Bus'),
        ('cf', 'Code Fetch'),
        ('mm', 'Mnemonic'),
        ('piq', 'Processor Instruction Queue'),
        ('ib', 'Instruction Bytes'),
        ('dbg', 'Debug Msg'),
        ('err', 'Error Msg'),
    )
    annotation_rows = (
        ('ALE', 'Address Latch Enable', (Annot.ALE,)),
        ('AL', 'Address Latch', (Annot.AddrLatch,)),
        ('BUS', 'Bus Status', (Annot.BusStatus,)),
        ('BUSL', 'Bus Status Latch', (Annot.BusStatusL,)),
        ('QOP', 'Queue Status', (Annot.QsF, Annot.QsS, Annot.QsE,)),
        ('TCYC', 'CPU T-cycle', (Annot.TI, Annot.T1, Annot.T2, Annot.T3, Annot.TW, Annot.T4,)),
        ('DATA', 'Data Bus', (Annot.D,)),
        ('FETCH', 'Code Fetch', (Annot.F,)),
        ('PIQ', 'Instruction Queue', (Annot.Piq,)),
        ('IB', 'Instruction Bytes', (Annot.Ib,)),
        ('INST', 'Instruction', (Annot.Mm,)),
        ('DBG', 'Debug', (Annot.Dbg,Annot.Err,)),
    )

    def __init__(self):
        self.reset()

        self.disasm = Disassembler()

    def reset(self):
        self.items = []
        self.saved_item = None
        self.ss_item = self.es_item = None
        self.saved_word = None
        self.ss_word = self.es_word = None
        self.first = True

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        
        # 8088 specific state
        self.last_pins = [0] * PINS_LEN 

        self.ale = False            # Address Latch Enable
        self.al = None              # Address Latch
        self.al_ss = TrackedValue()
        self.al_annotation = TrackedValue('')

        self.cycle_sample = TrackedValue(0)

        # Bus status
        self.bus_status = TrackedValue()         # Bus Status
        self.bus_status_ss = TrackedValue()      # Bus cycle sample number
        self.bus_status_latch = TrackedValue()   # Bus Status Latch
        
        self.t_state = TState.TI    # CPU T-state
        self.prev_queue_ss = 0
        self.queue_status = TrackedValue(0)

        self.data_valid = False
        self.data_bus = 0

        self.queue = deque()
        self.opcode = TrackedValue(0)
        self.instr_ss = TrackedValue()
        self.instr = deque()
        self.mnemonic = TrackedValue('')

    def putpb(self, data):
        self.put(self.ss_item, self.es_item, self.out_python, data)

    def putb(self, data):
        self.put(self.ss_item, self.es_item, self.out_ann, data)

    def putpw(self, data):
        self.put(self.ss_word, self.es_word, self.out_python, data)

    def putw(self, data):
        self.put(self.ss_word, self.es_word, self.out_ann, data)

    def save_pins(self, pins):
        for i in range(PINS_LEN):
            self.last_pins[i] = pins[i] 

    def cycle_annot(self, annot, text):
        self.put(
            self.cycle_sample.prev, 
            self.samplenum, 
            self.out_ann, 
            [annot, ["{}".format(text)]]
        )

    def debug_annot(self, text):
        self.put(
            self.cycle_sample.prev, 
            self.samplenum, 
            self.out_ann, 
            [Annot.Dbg, ["{}".format(text)]]
        )

    def error_annot(self, text):
        self.put(
            self.cycle_sample.prev, 
            self.samplenum, 
            self.out_ann, 
            [Annot.Err, ["{}".format(text)]]
        )

    def decode_status(self, pins):
        
        # Decode bus status pins S0-S2 to BUS status.
        if (
            self.last_pins[Status.S0] != pins[Status.S0]
            or self.last_pins[Status.S1] != pins[Status.S1]
            or self.last_pins[Status.S2] != pins[Status.S2]
        ):
            # Any one of the three status lines has changed...

            # Emit annotation for the previous bus state.
            if self.bus_status_ss.cur is not None and self.bus_status.prev is not None:
                self.put(
                    self.bus_status_ss.cur,
                    self.samplenum,
                    self.out_ann,
                    [Annot.BusStatus, [BUS_STATES[self.bus_status.cur]]],
                )
    
            # Decode the bus status pins to an integer.
            self.bus_status.update(reduce_bus(pins[Status.S0 : Status.S2 + 1]))
            self.bus_status_ss.update(self.samplenum)
            
            if self.bus_status.prev is not None:
                if self.bus_status.prev == 7 and self.bus_status.cur != 7:
                    # New bus cycle is beginning, indicating the ALE signal should go high.
                    self.ale = True
                    self.al_ss.update(self.samplenum)
                    # Latch the bus status. The instantaneous bus status goes LOW on T3, but
                    # we want to remember it to detect type of reads and writes.
                    self.bus_status_latch.update(self.bus_status.cur)

    def display_queue(self):
        if len(self.queue) > 0:
            hex_string = ''.join(format(byte, '02X') for byte in self.queue)
            self.put(
                self.cycle_sample.prev, 
                self.samplenum, 
                self.out_ann, 
                [Annot.Piq, [hex_string]],
            )
        else:
            self.put(
                self.cycle_sample.prev, 
                self.samplenum, 
                self.out_ann, 
                [Annot.Piq, ['-']],
            )

    def instr_string(self):
        return ''.join(format(byte, '02X') for byte in self.instr)

    def display_instr(self):
        if len(self.instr) > 0:
            hex_string = self.instr_string()
            self.put(
                self.cycle_sample.prev, 
                self.samplenum, 
                self.out_ann, 
                [Annot.Ib, [hex_string]],
            )
        else:
            self.put(
                self.cycle_sample.prev, 
                self.samplenum, 
                self.out_ann, 
                [Annot.Ib, ['-']],
            )            

    def queue_push(self, byte):
        if len(self.queue) > 3:
            raise IndexError("This is a custom error message")
        else:
            self.queue.append(byte)

    def queue_pop(self):
        return self.queue.popleft()

    def instr_push(self, byte):
        if len(self.instr) < 8:
            self.instr.append(byte)

    def decode_queue(self, pins):
        if self.queue_status.update(reduce_bus(pins[Pin.QS0:Pin.QS1+1])).changed():
            if self.queue_status.prev != 0:
                self.cycle_annot(
                    QUEUE_ANNOTS[self.queue_status.prev],
                    QUEUE_STATES[self.queue_status.prev]    
                )

            if self.queue_status.prev == QueueOp.Empty:
                self.queue.clear()
                self.debug_annot("q_e")
                self.display_queue()

            try:
                if self.queue_status.cur == QueueOp.First:
                    # Update disassembly and clear instruction deque
                    self.instr_ss.update(self.samplenum)
                    self.opcode.update(self.instr[0])
                    try:
                        self.mnemonic.update(self.disasm.disassemble(list(self.instr)))
                    except:
                        self.mnemonic.update("inval")
                        self.error_annot("e:{}".format(e))
                    self.put(
                        self.instr_ss.prev,
                        self.cycle_sample.cur,
                        self.out_ann,
                        [Annot.Mm, ["{:02X}:{}".format(self.opcode.cur, self.mnemonic.cur)]],
                    )
                    self.instr.clear()
            except Exception as e:
                self.error_annot("e: {}".format(e))

            if self.queue_status.prev == QueueOp.First or self.queue_status.prev == QueueOp.Subs:
                try:
                    qb = self.queue_pop()
                    self.opcode.update(qb)
                    self.instr_push(qb)
                    self.display_queue()
                    self.display_instr()
                    self.debug_annot("q_rd:{:02X}".format(qb))
                except:
                    self.error_annot("q_err_uf")

    def advance_t_state(self, pins):
        # Check if we should transition to T1.
        if self.ale == True and self.t_state != TState.T1:
            self.t_state = TState.T1
        else:
            if self.t_state == TState.T1:
                # Clear the ALE state - it should only be active for one cycle.
                self.ale = False
                self.cycle_annot(Annot.ALE, "ALE")
                self.t_state = TState.T2
            elif self.t_state == TState.T2:
                self.t_state = TState.T3
                if pins[Pin.RDY] == 1:
                    self.data_valid = True
            elif self.t_state == TState.T3:
                if pins[Pin.RDY] == 1:
                    self.t_state = TState.T4
                else:
                    self.t_state = TState.TW
            elif self.t_state == TState.TW:
                if self.last_pins[Pin.RDY] == 0:
                    if pins[Pin.RDY] == 1:
                        self.data_valid = True
                else:
                    self.t_state = TState.T4
            elif self.t_state == TState.T4:
                self.t_state = TState.TI

    def set_address_latch(self, pins):
        if self.ale:
            #self.debug_annot(Annot.ALE, "ALE")
            if self.al_ss.prev is not None:

                # Decode entire address bus and save sample 
                self.al_annotation.update('%05X' % reduce_bus(pins[Addr.AD0:Addr.A19+1]))

                self.put(
                    self.al_ss.prev, 
                    self.samplenum, 
                    self.out_ann, 
                    [Annot.AddrLatch, [self.al_annotation.prev]]
                )

    def decode_data(self, pins):
        self.data_bus = reduce_bus(pins[Pin.AD0:Pin.AD7+1])
        self.cycle_annot(Annot.D, '%02X' % self.data_bus)

    def fetch(self):
        self.cycle_annot(Annot.F, '%02X' % self.data_bus)
        try:
            self.queue_push(self.data_bus)
        except:
            self.error_annot('q_err_of')

        self.display_queue()
        #inst = self.disasm.disassemble([self.data_bus])
        #self.cycle_annot(Annot.Mm, inst)

    def decode(self):
        while True:
            # Wait for rising edge on the CPU clock.
            pins = self.wait({Pin.CLK: 'r'})
            
            self.cycle_sample.update(self.samplenum)

            self.decode_status(pins)

            self.cycle_annot(T_ANNOTS[self.t_state], T_STATES[self.t_state])

            if self.data_valid:
                self.decode_data(pins)
                if self.bus_status_latch.cur == BusStatus.CODE:
                    # This was a code fetch. Process it.
                    self.fetch()

                self.data_valid = False

            self.decode_queue(pins)
            self.advance_t_state(pins)
            self.set_address_latch(pins)
            self.save_pins(pins)
