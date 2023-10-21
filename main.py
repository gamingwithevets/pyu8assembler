import re
import sys
import logging
import argparse

logging.basicConfig(datefmt = '%d/%m/%Y %H:%M:%S', format = '[%(asctime)s] %(levelname)s: %(message)s')

class Assembler:
	def __init__(self):
		self.instruction_list = (
		(('MOV', 'GR', 'num_imm8'), 0),
		)

		self.assembly = None

		self.idx = 0

		self.numtypes = {
			# type: (immediate, andval)
			'num_imm8': (True, 0xff),
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
		if not num_str[-1].isnumeric() and num_str[-1] in self.bases.keys(): base = self.bases[num_str[-1]]
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
				if line[0] != ins[0][0]: continue
				score = 0
				for i in (1, 2):
					if ins[0][i].startswith('G') and line[i].startswith(ins[0][i][2:]): score += 1
				if score < 1: continue

				instruction = ins

			if instruction == None: self.stop_lineno(f'Line {idx+1}: Cannot detect instruction, check that your syntax is correct\n(Instruction may not be implemented yet)')

			ins = instruction[0]
			opcode = instruction[1]
			ins_len = 2

			for i in range(1, len(ins)):
				if ins[i].startswith('G'):
					if ins[i][1] == 'R':
						if line[i][1:].isnumeric() and int(line[i][1:]) < 16: opcode |= int(line[i][1:]) << (8 if i == 1 else 4)
						else: self.stop_lineno('Invalid Rn value')
				elif ins[i].startswith('num_'):
					numtype = self.numtypes[ins[i]]
					if numtype[0]:
						if line[i][0] == '#': opcode += self.conv_num(line[i][1:])
						else: self.stop_lineno('Expected immediate (did you forget to add "#"?)')

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
	args = parser.parse_args()

	assembler = Assembler()
	assembler.assembly = args.input.read().split('\n')
	
	assembler.assemble(args.output)
