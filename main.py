import re
import sys
import logging
import argparse

class Assembler:
	def __init__(self):
		self.instruction_list = (
		(('DW',   'num_word'),        0x0000),
		(('ADD',  'GR',  'GR'),       0x8001),
		(('ADD',  'GR',  'num_imm8'), 0x1000),
		(('ADDC', 'GR',  'GR'),       0x8006),
		(('ADDC', 'GR',  'num_imm8'), 0x6000),
		(('AND',  'GR',  'GR'),       0x8002),
		(('AND',  'GR',  'num_imm8'), 0x2000),
		(('BRK',),                    0xffff),
		(('CMP',  'GR',  'GR'),       0x8007),
		(('CMP',  'GR',  'GR'),       0x8007),
		(('CMPC', 'GR',  'GR'),       0x8005),
		(('CMPC', 'GR',  'num_imm8'), 0x5000),
		(('CPLC',),                   0xfecf),
		(('DAA',  'GR'),              0x801f),
		(('DAS',  'GR'),              0x803f),
		(('DEC',  'P:[EA]'),          0xfe3f),
		(('DI',),                     0xebf7),
		(('EI',),                     0xed08),
		(('INC',  'P:[EA]'),          0xfe2f),
		(('L',    'GR',  'P:[EA]'),   0x9030),
		(('L',    'GR',  'P:[EA+]'),  0x9050),
		(('MOV',  'GR',  'EPSW'),     0xa004),
		(('MOV',  'GR',  'PSW'),      0xa003),
		(('MOV',  'GR',  'GR'),       0x8000),
		(('MOV',  'GR',  'num_imm8'), 0x0000),
		(('NEG',  'GR'),              0x805f),
		(('NOP',),                    0xfe8f),
		(('OR',   'GR',  'GR'),       0x8003),
		(('OR',   'GR',  'num_imm8'), 0x3000),
		(('POP',  'GR'),              0xf00e),
		(('PUSH', 'GR'),              0xf04e),
		(('RC',),                     0xeb7f),
		(('RT',),                     0xfe1f),
		(('RTI',),                    0xfe0f),
		(('SC',),                     0xeb80),
		(('SLL',  'GR', 'GR'),        0x800a),
		(('SLLC', 'GR', 'GR'),        0x800b),
		(('SRA',  'GR', 'GR'),        0x800e),
		(('SRL',  'GR', 'GR'),        0x800c),
		(('SRLC', 'GR', 'GR'),        0x800d),
		(('ST',   'GR',  '[EA]'),     0x9031),
		(('ST',   'GR',  '[EA+]'),    0x9051),
		(('SUB',  'GR',  'GR'),       0x8008),
		(('SUBC', 'GR',  'GR'),       0x8009),
		(('XOR',  'GR',  'GR'),       0x8004),
		(('XOR',  'GR',  'num_imm8'), 0x4000),
		)

		self.assembly = None

		self.idx = 0

		self.numtypes = {
			# type:     (isimm, maxval, minval, allow_signed)
			'num_imm8': (True,  0xff,   0,      True),
			'num_byte': (False, 0xff,   0,      False),
			'num_word': (False, 0xffff, 0,      False),
		}

		self.bases = {
			'H': 16,
			'D': 10,
			'O': 8,
			'Q': 8,
			'B': 2,
		}

	def stop_lineno(self, err_str): self.stop(f'line {self.idx+1}: {err_str}')

	def debug_lineno(self, debug_str): logging.debug(f'line {self.idx+1}: {debug_str}')

	@staticmethod
	def stop(err_str):
		logging.error(err_str)
		sys.exit()	

	def conv_num(self, num_str, maxval, minval, allow_signed):
		negative = False
		if num_str[0] == '-':
			if allow_signed:
				num_str = num_str[1:]
				negative = True
			else: self.stop_lineno('Cannot specify negative number for unsigned addressing type')

		base = 10
		if num_str[-1].isnumeric():
			try: num = int(num_str, base)
			except ValueError: self.stop_lineno('Invalid number')
		else:
			if num_str[-1] in self.bases.keys(): base = self.bases[num_str[-1]]
			else: self.stop_lineno('Invalid radix specifier')
			try: num = int(num_str[:-1], base)
			except ValueError: self.stop_lineno('Invalid number')

		if negative: num = -num
		if not (minval < num < maxval): self.stop_lineno(f'Number not in range({minval}, {maxval})')
		
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
		adr = 0
		opcodes = {}
		logging.info('Start assembling.')
		for idx in range(len(self.assembly)):
			if self.assembly[idx] == '' or self.assembly[idx].strip().split(';')[0].strip() == '': continue
			self.idx = idx
			line = list(filter(('').__ne__, re.split('[ \t]', self.assembly[idx].strip().split(';')[0].strip().upper())))

			if line[0] == 'END': break

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
					if score != len(line) - 1: continue

				instruction = ins
				self.debug_lineno(f'instruction matches format of {ins[0]}')
				break

			if instruction == None: self.stop_lineno('Unknown instruction/directive\n(Instruction/directive may not be implemented yet)')

			ins = instruction[0]
			opcode = instruction[1]
			opcode2 = None
			ins_len = 2

			for i in range(1, len(ins)):
				if ins[i].startswith('G'):
					if ins[i][1] == 'R':
						if line[i][1:].isnumeric() and int(line[i][1:]) < 16: opcode |= int(line[i][1:]) << (8 if i == 1 else 4)
						else: self.stop_lineno(f'Invalid Rn value')
				elif ins[i].startswith('num_'):
					numtype = self.numtypes[ins[i]]
					if numtype[0]:
						if line[i][0] == '#':
							converted = self.conv_num(line[i][1:], *numtype[1:])
							self.debug_lineno(f'converted number {line[i][1:]} to {converted}')
							opcode += converted & numtype[1]
						else: self.stop_lineno('Expected immediate (did you forget to add "#"?)')
					else:
						converted = self.conv_num(line[i], *numtype[1:])
						self.debug_lineno(f'converted number {line[i]} to {converted}')
						opcode += converted & numtype[1]

			self.debug_lineno(f'converted to word(s) {format(opcode_dsr, "04X") + " " if opcode_dsr is not None else ""}{opcode:04X}{format(opcode2, "04X") + " " if opcode2 is not None else ""}')

			byte_data = b''
			
			if opcode_dsr is not None:
				byte_data += opcode_dsr.to_bytes(2, 'little')
				ins_len += 2
			byte_data += opcode.to_bytes(2, 'little')
			if opcode2 is not None:
				byte_data += opcode2.to_bytes(2, 'little')
				ins_len += 2

			for i in range(ins_len): opcodes[adr+i] = byte_data[i]
			adr += ins_len

		logging.info('Writing bytes to bytearray')
		binary = bytearray(b'\xff'*(sorted(list(opcodes.keys()))[-1] + 1))
		for adr in opcodes: binary[adr] = opcodes[adr]

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
