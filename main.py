import re
import sys
import logging
import argparse

class Assembler:
	def __init__(self):
		self.instruction_list = (
		(('DB',   'num_byte'),        0x0000),
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
		(('DEC',  '[EA]'),            0xfe3f),
		(('DI',),                     0xebf7),
		(('EI',),                     0xed08),
		(('INC',  '[EA]'),            0xfe2f),
		(('L',    'GR',  '[EA]'),     0x9030),
		(('L',    'GR',  '[EA+]'),    0x9050),
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
			# type: (immediate, andval)
			'num_imm8': (True,  0xff),
			'num_byte': (False, 0xff),
			'num_word': (False, 0xffff),
		}

		self.bases = {
			'H': 16,
			'D': 10,
			'O': 8,
			'Q': 8,
			'B': 2,
		}

	def stop_lineno(self, err_str): self.stop(f'line {self.idx+1}: {err_str}')

	@staticmethod
	def stop(err_str):
		logging.error(err_str)
		sys.exit()	

	def conv_num(self, num_str):
		base = 10
		if num_str[-1].isnumeric():
			try: num = int(num_str, base)
			except ValueError: self.stop_lineno('Invalid number')
		else:
			if num_str[-1] in self.bases.keys(): base = self.bases[num_str[-1]]
			else: self.stop_lineno('Invalid radix specifier')
			try: num = int(num_str[:-1], base)
			except ValueError: self.stop_lineno('Invalid number')

		return num

	def assemble(self, output):
		adr = 0
		opcodes = {}
		for idx in range(len(self.assembly)):
			if self.assembly[idx] == '' or re.fullmatch(r'\s+', self.assembly[idx]): continue
			self.idx = idx
			line = list(filter(('').__ne__, re.split('[ \t]', self.assembly[idx].upper())))
			if len(line) > 3: self.stop_lineno("Instruction has more than 3 operands\n(note: are you trying to add a label? labels aren't implemented yet.)")
			elif len(line) == 3: line[1] = line[1][:-1]
			instruction = None
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
						elif ins[0][i] == line[i] == '[EA]': score += 1
					if score != len(line) - 1: continue

				instruction = ins
				logging.debug(f'line {self.idx+1}: instruction matches format of {ins[0]}')
				break

			if instruction == None: self.stop_lineno('Cannot detect instruction, check that your syntax is correct\n(Instruction may not be implemented yet)')

			ins = instruction[0]
			opcode = instruction[1]
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
							logging.debug(f'line {self.idx+1}: converted number {line[i][1:]} to {self.conv_num(line[i][1:])}')
							opcode += self.conv_num(line[i][1:]) & numtype[1]
						else: self.stop_lineno('Expected immediate (did you forget to add "#"?)')
					else:
						logging.debug(f'line {self.idx+1}: converted number {line[i]} to {self.conv_num(line[i])}')
						opcode += self.conv_num(line[i]) & numtype[1]

			logging.debug(f'line {self.idx+1}: converted to word {opcode:04X}')

			byte_data = opcode.to_bytes(ins_len, 'little')
			for i in range(ins_len): opcodes[adr+i] = byte_data[i]
			adr += ins_len

		binary = bytearray(b'\xff'*(sorted(list(opcodes.keys()))[-1] + 1))
		for adr in opcodes: binary[adr] = opcodes[adr]

		with open(output, 'wb') as f: f.write(binary)

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
