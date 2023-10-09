import re
import sys
import logging

logging.basicConfig(datefmt = '%d/%m/%Y %H:%M:%S', format = '[%(asctime)s] %(levelname)s: %(message)s')

instruction_list = (
(('MOV', '*Rn', '*#imm8'), 0),
)

regexes = {
	'*Rn': 'R(?:[0-9]|1[0-5])',
	'*#imm8': '#(?:[0-9A-F]+H|[0-7]+[OQ]|[01]+B|[0-9]+D|[0-9]+)'
}

hex_vals = {
	'H': 16,
	'D': 10,
	'O': 8,
	'Q': 8,
	'B': 2,
}

with open('test.asm', 'r') as f: assembly = f.read().split('\n')
assembly = list(filter(('').__ne__, assembly))

binary = b''
for idx in range(len(assembly)):
	line = re.split('[ \t]', assembly[idx].upper())
	if len(line) == 3: line[1] = line[1][:-1]
	instruction = None
	for ins in instruction_list:
		score = 0
		if len(ins[0]) != len(line): continue
		for i in range(len(ins[0])):
			if ins[0][i][0] == '*': regex = regexes[ins[0][i]]
			else: regex = ins[0][i]
			if re.fullmatch(regex, line[i]): score += 1

		if score == len(ins[0]):
			instruction = ins
			break

	if instruction == None:
		logging.error(f'Line {idx+1}: Cannot detect instruction')
		sys.exit()

	opcode = instruction[1]
	op1 = None
	op2 = None
	ins_len = 2

	for i in range(len(instruction[0])):
		if instruction[0][i] == '*Rn': opcode += int(line[i][1:]) << 8
		elif instruction[0][i] == '*#imm8':
			if line[i][-1].isnumeric(): opcode += int(line[i][1:])
			else: opcode += int(line[i][1:-1], hex_vals[line[i][-1]])

	binary += opcode.to_bytes(ins_len, 'little')

with open('test.bin', 'wb') as f: f.write(binary)
