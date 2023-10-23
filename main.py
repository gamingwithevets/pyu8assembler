import re
import sys
import logging
import argparse
from functools import cache

class Assembler:
	def __init__(self):
		self.instruction_list = (
		(('DW',    'num_word'),                 0x0000),


		# Arithmetic Instructions
		(('ADD',   'GR0',     'GR1'),           0x8001),
		(('ADD',   'GR0',     'num_imm8'),      0x1000),

		(('ADD',   'GER0',    'GER1'),          0xf006),
		(('ADD',   'GER0',    'num_imm7'),      0xe080),

		(('ADDC',  'GR0',     'GR1'),           0x8006),
		(('ADDC',  'GR0',     'num_imm8'),      0x6000),

		(('AND',   'GR0',     'GR1'),           0x8002),
		(('AND',   'GR0',     'num_imm8'),      0x2000),

		(('CMP',   'GR0',     'GR1'),           0x8007),
		(('CMP',   'GR0',     'num_imm8'),      0x7000),

		(('CMPC',  'GR0',     'GR1'),           0x8005),
		(('CMPC',  'GR0',     'num_imm8'),      0x5000),

		(('MOV',   'GER0',    'GER1'),          0xf005),
		(('MOV',   'GER0',    'num_imm7'),      0xe000),

		(('MOV',   'GR0',     'GR1'),           0x8000),
		(('MOV',   'GR0',     'num_imm8'),      0x0000),

		(('OR',    'GR0',     'GR1'),           0x8003),
		(('OR',    'GR0',     'num_imm8'),      0x3000),

		(('XOR',   'GR0',     'GR1'),           0x8004),
		(('XOR',   'GR0',     'num_imm8'),      0x4000),

		(('CMP',   'GER0',    'GER1'),          0xf007),

		(('SUB',   'GR0',     'GR1'),           0x8008),
		
		(('SUBC',  'GR0',     'GR1'),           0x8009),


		# Load/Store Instructions
		(('L',     'GER0',    'P:[EA]'),        0x9032),
		(('L',     'GER0',    'P:[EA+]'),       0x9052),

		(('L',     'GR0',     'P:[EA]'),        0x9030),
		(('L',     'GR0',     'P:[EA+]'),       0x9050),

		(('L',     'GXR0',    'P:[EA]'),        0x9034),
		(('L',     'GXR0',    'P:[EA+]'),       0x9054),

		(('L',     'GQR0',    'P:[EA]'),        0x9036),
		(('L',     'GQR0',    'P:[EA+]'),       0x9056),

		(('ST',    'GER0',    '[EA]'),          0x9033),
		(('ST',    'GER0',    '[EA+]'),         0x9053),

		(('ST',    'GR0',     '[EA]'),          0x9031),
		(('ST',    'GR0',     '[EA+]'),         0x9051),

		(('ST',    'GXR0',    '[EA]'),          0x9035),
		(('ST',    'GXR0',    '[EA+]'),         0x9055),

		(('ST',    'GQR0',    '[EA]'),          0x9037),
		(('ST',    'GQR0',    '[EA+]'),         0x9057),


		# Shift Instructions
		(('SLL',   'GR0',     'GR1'),           0x800a),

		(('SLLC',  'GR0',     'GR1'),           0x800b),

		(('SRA',   'GR0',     'GR1'),           0x800e),

		(('SRL',   'GR0',     'GR1'),           0x800c),

		(('SRLC',  'GR0',     'GR1'),           0x800d),


		# Control Register Access Instructions
		(('ADD',   'SP',      'num_signed8'),   0xe100),

		(('MOV',   'ECSR',    'GR1'),           0xa00f),
		(('MOV',   'ELR',     'GER0'),          0xa00d),
		(('MOV',   'EPSW',    'GR1'),           0xa00c),

		(('MOV',   'GER0',    'ELR'),           0xa005),
		(('MOV',   'GER0',    'SP'),            0xa01a),

		(('MOV',   'PSW',     'GR1'),           0xa00b),
		(('MOV',   'PSW',     'num_unsigned8'), 0xe900),

		(('MOV',   'GR0',     'ECSR'),          0xa007),
		(('MOV',   'GR0',     'EPSW'),          0xa004),
		(('MOV',   'GR0',     'PSW'),           0xa003),
		(('MOV',   'SP',      'GER1'),          0xa10a),


		# PUSH/POP Instructions
		(('PUSH',  'GR0'),                      0xf04e),
		(('PUSH',  'GER0'),                     0xf05e),
		(('PUSH',  'GXR0'),                     0xf06e),
		(('PUSH',  'GQR0'),                     0xf07e),

		(('POP',   'GR0'),                      0xf00e),
		(('POP',   'GER0'),                     0xf01e),
		(('POP',   'GXR0'),                     0xf02e),
		(('POP',   'GQR0'),                     0xf03e),


		# Coprocessor Data Transfer Instructions
		(('MOV',   'GCR0',    'GR1'),           0xa00e),

		(('MOV',   'GCER0',   'P:[EA]'),        0xf02d),
		(('MOV',   'GCER0',   'P:[EA+]'),       0xf03d),

		(('MOV',   'GCR0',    'P:[EA]'),        0xf00d),
		(('MOV',   'GCR0',    'P:[EA+]'),       0xf01d),

		(('MOV',   'GCXR0',   'P:[EA]'),        0xf04d),
		(('MOV',   'GCXR0',   'P:[EA+]'),       0xf05d),

		(('MOV',   'GCQR0',   'P:[EA]'),        0xf06d),
		(('MOV',   'GCQR0',   'P:[EA+]'),       0xf07d),

		(('MOV',   'GR0',     'GCR1'),          0xa006),

		(('MOV',   'P:[EA]',  'GCER0'),         0xf0ad),
		(('MOV',   'P:[EA+]', 'GCER0'),         0xf0bd),

		(('MOV',   'P:[EA]',  'GCR0'),          0xf08d),
		(('MOV',   'P:[EA+]', 'GCR0'),          0xf09d),

		(('MOV',   'P:[EA]',  'GXQR0'),         0xf0cd),
		(('MOV',   'P:[EA+]', 'GXQR0'),         0xf0dd),

		(('MOV',   'P:[EA]',  'GCQR0'),         0xf0ed),
		(('MOV',   'P:[EA+]', 'GCQR0'),         0xf0fd),


		# EA Register Data Transfer Instructions
		# (not implemented yet)

		# ALU Instructions
		(('DAA',   'GR0'),                      0x801f),
		(('DAS',   'GR0'),                      0x803f),
		(('NEG',   'GR0'),                      0x805f),


		# Bit Access Instructions
		# (not implemented yet)


		# PSW Access Instructions
		(('EI',),                               0xed08),
		(('DI',),                               0xebf7),
		(('SC',),                               0xeb80),
		(('RC',),                               0xeb7f),
		(('CPLC',),                             0xfecf),


		# Conditional Relative Branch Instructions
		# (not implemented yet)


		# Sign Extension Instruction
		(('EXTBW', 'GER0'),                     0x800f),


		# Software Interrupt Instructions
		(('SWI',   'num_snum'),                 0xe500),
		(('BRK',),                              0xffff),


		# Branch Instructions
		(('B',     'GER1'),                     0xf002),
		(('BL',    'GER1'),                     0xf003),


		# Multiplication and Division Instructions
		(('MUL',   'GER0',    'GR1'),           0xf004),
		(('DIV',   'GER0',    'GR1'),           0xf009),

		# Miscellaneous
		(('INC',   'P:[EA]'),                   0xfe2f),
		(('DEC',   'P:[EA]'),                   0xfe3f),
		(('RT',),                               0xfe1f),
		(('RTI',),                              0xfe0f),
		(('NOP',),                              0xfe8f),
		)

		self.assembly = None

		self.idx = 0
		self.adr = 0

		self.numtypes = {
			# type:          (req_#, numbits, signed, unsigned)
			'num_imm8':      (True,  8,       True,   True),
			'num_signed8':   (True,  8,       True,   False),
			'num_unsigned8': (True,  8,       False,  True),
			'num_imm7':      (True,  7,       True,   True),
			'num_snum':      (True,  6,       False,  True),
			'num_byte':      (False, 8,       False,  True),
			'num_word':      (False, 16,      False,  True),
		}

		self.bases = {
			'H': 16,
			'D': 10,
			'O': 8,
			'Q': 8,
			'B': 2,
		}

		self.regtypes = {
		#   reg: modval
			'R': 1,
			'ER': 2,
			'XR': 4,
			'QR': 8,
			'CR': 1,
			'CER': 2,
			'CXR': 4,
			'CQR': 8,
		}

	@staticmethod
	@cache
	def fmt_addr(addr: int) -> str:
		csr = (addr & 0xf0000) >> 16
		high = (addr & 0xff00) >> 8
		low = addr & 0xff
		return f'{csr:X}:{high:02X}{low:02X}H'

	def stop_lineno(self, err_str): self.stop(f'line {self.idx+1}: {err_str}')

	def debug_lineno(self, debug_str): logging.debug(f'line {self.idx+1} ({self.fmt_addr(self.adr)}): {debug_str}')

	@staticmethod
	def stop(err_str):
		logging.error(err_str)
		sys.exit()	

	def conv_num(self, num_str, numbits, allow_signed, allow_unsigned):
		maxval = 2 ** (numbits if allow_unsigned else numbits - 1) - 1
		minval = -2 ** (numbits - 1) if allow_signed else 0

		negative = False
		if num_str[0] == '-':
			if allow_signed:
				num_str = num_str[1:]
				negative = True
			else: self.stop_lineno('Cannot specify negative number for unsigned addressing type')
		elif num_str == '+': num_str = num_str[1:]

		base = 10
		if num_str[-1].isnumeric():
			try: num = int(num_str, base)
			except ValueError: self.stop_lineno(f'Invalid number: {num_str}')
		else:
			if num_str[-1] in self.bases.keys(): base = self.bases[num_str[-1]]
			else: self.stop_lineno('Invalid radix specifier')
			try: num = int(num_str[:-1], base)
			except ValueError: self.stop_lineno(f'Invalid number: {num_str}')

		if negative: num = -num
		if not (minval <= num <= maxval): self.stop_lineno(f'Number not in range({minval}, {maxval+1})')
		
		return num

	def is_number(self, num_str):
		base = 10
		if num_str[-1].isnumeric():
			try: int(num_str, base)
			except ValueError: return False
		else:
			if num_str[-1] in self.bases.keys(): base = self.bases[num_str[-1]]
			else: return False
			try: int(num_str[:-1], base)
			except ValueError: return False

		return True

	def assemble_prefix(self, prefix):
		if prefix == 'DSR': return 0xfe9f
		elif prefix[0] == 'R':
			if prefix[1:].isnumeric() and int(prefix[1:]) < 16: return 0x900f | int(prefix[1:]) << 4
			else: self.stop_lineno(f'Invalid Rn value')
		elif self.is_number(prefix): return 0xe300 + self.conv_num(prefix, 0xff, 0, False)
		else: self.stop_lineno('Invalid DSR prefix')

	def assemble(self, output):
		self.adr = 0
		opcodes = {}
		logging.info('Assembling')
		for idx in range(len(self.assembly)):
			if self.assembly[idx] == '' or self.assembly[idx].strip().split(';')[0].strip() == '': continue
			self.idx = idx
			line = list(filter(('').__ne__, re.split('[ \t]', self.assembly[idx].strip().split(';')[0].strip().upper())))
			if line[0] == 'END': 
				if len(line) > 1: self.stop_lineno('END directive takes no arguments')
				break

			for i in range(1, len(line) - 1): line[i] = line[i][:-1]
			if len(line) > 3 and line[0] not in ('PUSH', 'POP'): self.stop_lineno("Non-PUSH/POP instruction has more than 3 operands")
			instruction = None
			opcode_dsr = None
			for ins in self.instruction_list:
				if len(line) != len(ins[0]): continue
				if line[0] != ins[0][0]: continue
				score = 0
				if len(line) > 1:
					for i in range(1, len(line)):
						if ins[0][i].startswith('G') and line[i].startswith(ins[0][i][1:]): score += 1
						elif ins[0][i].startswith('num_'):
							numtype = self.numtypes[ins[0][i]]
							if numtype[0]:
								if line[i][0] == '#': score += 1
								else: self.stop_lineno('Expected immediate (did you forget to add "#"?)')
							else: score += 1
						elif ins[0][i].startswith('P:'):
							splitted = line[i].split(':')
							comp_str = splitted[0]
							if len(splitted) > 1:
								if len(splitted) != 2: self.stop_lineno('Too many colons')
								comp_str = splitted[1]
								opcode_dsr = self.assemble_prefix(splitted[0])
								self.debug_lineno(f"Converted DSR prefix '{splitted[0]}' to word {opcode_dsr:04X}")
							if comp_str == ins[0][i][2:]: score += 1
						elif ins[0][i] == line[i]: score += 1
					if score != len(line) - 1: continue

				instruction = ins
				self.debug_lineno(f'Instruction matches format of {ins[0]}')
				break

			if instruction == None: self.stop_lineno('Unknown instruction/directive\n(Instruction/directive may not be implemented yet)')

			ins = instruction[0]
			opcode = instruction[1]
			opcode2 = None
			ins_len = 2

			for i in range(1, len(ins)):
				if ins[i].startswith('G'):
					for reg, modval in self.regtypes.items():
						match = re.match(reg, ins[i])
						if match:
							try: j = line[i][-1]
							except ValueError: self.stop_lineno('Error getting register nibble placement')
							num = line[i][match.end():-1]
							if num.isnumeric() and int(num) < 16 and int(num) % modval == 0:
								val = int(num)
								if reg == 'ER' and ins[0] == 'EXTBW': opcode |= (val + 1) << 8 + val << 4
								else: opcode |= int(num) << (4 if j == 1 else 8)
							else: self.stop_lineno(f'Invalid {reg}n value')
				elif ins[i].startswith('num_'):
					numtype = self.numtypes[ins[i]]
					andval = 2 ** numtype[1] - 1
					conv_str = line[i]
					if numtype[0]:
						if line[i][0] == '#': conv_str = line[i][1:]
						else: self.stop_lineno('Expected "#" before expression')

					ok = False
					for op in ('+', '-', '*', '/', '%'):
						if op in conv_str:
							if ok: self.stop_lineno('One operator at a time only')
							else: ok = True
						
					ok = False
					for op in ('+', '-', '*', '/', '%'):
						exp_og = conv_str.split(op)
						exp = [self.conv_num(e, *numtype[1:]) for e in exp_og]
						op_ = op if op != '/' else '//'
						number = eval(f'{exp[0]}{op_}{exp[1]}')
						ok = True
						break

					if not ok: number = self.conv_num(conv_str, *numtype[1:])

					self.debug_lineno(f'Converted expression {conv_str} to {number}')
					opcode += number & andval

			self.debug_lineno(f'Converted to word(s) {format(opcode_dsr, "04X") + " " if opcode_dsr is not None else ""}{opcode:04X}{format(opcode2, "04X") + " " if opcode2 is not None else ""}')

			byte_data = b''
			
			if opcode_dsr is not None:
				byte_data += opcode_dsr.to_bytes(2, 'little')
				ins_len += 2
			byte_data += opcode.to_bytes(2, 'little')
			if opcode2 is not None:
				byte_data += opcode2.to_bytes(2, 'little')
				ins_len += 2

			for i in range(ins_len): opcodes[self.adr+i] = byte_data[i]
			self.adr += ins_len

		logging.info('Writing bytes to bytearray')
		binary = bytearray(b'\xff'*(sorted(list(opcodes.keys()))[-1] + 1))
		for self.adr in opcodes: binary[self.adr] = opcodes[self.adr]

		logging.info('Writing bytearray to file')
		with open(output, 'wb') as f: f.write(binary)

		logging.info('Done!')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'nX-U8/100 assembler.', epilog = '(c) 2023 GamingWithEvets Inc.\nLicensed under the GNU GPL-v3 license', formatter_class=argparse.RawTextHelpFormatter, allow_abbrev = False)
	parser.add_argument('input', type = open, help = 'name of assembly file')
	parser.add_argument('-o', '--output', metavar = 'output', default = 'out.bin', help = 'name of output file. default: out.bin')
	parser.add_argument('-d', '--debug', action = 'store_true', help = 'enable debug logs')
	args = parser.parse_args()

	logging.basicConfig(datefmt = '%d/%m/%Y %H:%M:%S', format = '[%(asctime)s] %(levelname)s: %(message)s', level = logging.DEBUG if args.debug else logging.INFO)

	assembler = Assembler()
	assembler.assembly = args.input.read().split('\n')
	
	assembler.assemble(args.output)
