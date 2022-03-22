'''
Written by K. Srikar Siddarth
Roll number : 181EC218
'''

from collections import defaultdict


class Wire():
	def __init__(self):
		self.type = 'wire'
		self.value = 'x'		# current value
		self.inputNode = None
		self.outputNode = None
		self.id = None
		self.name = None

	def calc(self):
		if self.fault==0:			# stuck at 0 fault (sa0)
			output = 0
		elif self.fault==1:			# stuck at 1 fault (sa1)
			output = 1
		else:
			output = c.blocks[self.inputNode].value 	# no fault
		# print('hi',output)
		return output

	

class Block():
	def __init__(self,idnum,blockType,inputs,outputs):
		self.type = blockType
		self.name = blockType+str(idnum)
		self.id = None
		self.value = 'x'
		self.inputNode = inputs
		self.outputNode = outputs		
		# Assumption: that the gates are commutative so just output the values to a non empty input value


	def calc(self):
		inputs = [c.wires[i].value for i in self.inputNode]
		# print(inputs)
		if self.type=='AND':
			if 0 in inputs:
				output = 0
			elif 'x' not in inputs:
				if 'D' in inputs:
					if 'E' in inputs:
						output = 0
					else:
						output = 'D'
				elif 'E' in inputs:
					output = 'E'
				else: output = 1
			else:
				output = 'x'
			return output
		elif self.type=='OR':
			if 1 in inputs:
				output = 1
			elif 'x' not in inputs:
				if 'D' in inputs:
					if 'E' in inputs:
						output = 1
					else:
						output = 'D'
				elif 'E' in inputs:
					output = 'E'
				else: output = 0
			else:
				output = 'x'
			return output
		elif self.type=='NOT':
			if inputs[0]!='x':
				if inputs[0]=='E':
					output = 'D'
				elif inputs[0]=='D':
					output  = 'E'
				else:		
					output = 1-inputs[0]
			else:
				output = 'x'
			return output
		elif self.type=='fanout':
			# print(self.__dict__)
			return inputs[0]
		elif self.type=='NAND':
			if 0 in inputs:
				output = 1
			elif 'x' not in inputs:
				if 'D' in inputs:
					if 'E' in inputs:
						output = 1
					else:
						output = 'E'
				elif 'E' in inputs:
					output = 'D'
				else: output = 0
			else:
				output = 'x'
			return output
		elif self.type=='NOR':
			if 1 in inputs:
				output = 0
			elif 'x' not in inputs:
				if 'D' in inputs:
					if 'E' in inputs:
						output = 0
					else:
						output = 'E'
				elif 'E' in inputs:
					output = 'D'
				else: output = 1
			else:
				output = 'x'
			return output


# This class represents a circuit
class Circuit():
	# Constructor
	def __init__(self, netlist):

		# default dictionary to store graph
		self.graph = defaultdict(list)
		self.blocks = {}
		self.wires = {}
		self.blockCount= defaultdict(int)
		self.inputs = set()
		self.outputs = set()
		self.outputNodes = set()
		self.index = 0
		self.numBlocks = 0 					# stores the number of blocks
		self.wireNames = []
		self.wireIds = []
		self.faults = []					# useful for storing the list of faults at a particular wire
		self.debug = False

		# d - algorithm variables
		self.dFrontier = []
		self.jFrontier = []
		self.dalg_cnt = 0
		self.recursionDepth = 100
		self.implicationStack = []
		self.checkpoint_D = []
		self.checkpoint_J = []
		self.checkpoint_val = []
		self.checkpoint_impl = []

		# E = ~D
		
		self.intersectionTable = {
			(0,0): 0, (0,1): None, (0,'x'): 0, (0,'D'): None, (0,'E'): None,
			(1,0): None, (1,1): 1, (1,'x'): 1, (1,'D'): None, (0,'E'): None,
			('x',0): 0, ('x',1): 1, ('x','x'): 'x', ('x','D'): 'D', ('x','E'): 'E',
			('D',0): None, ('D',1): None, ('D','x'): 'D', ('D','D'): 'D', ('D','E'): None,
			('E',0): None, ('E',1): None, ('E','x'): 'E', ('E','D'): None, ('E','E'): 'E'
		}

		self.testVector = []
		self.netlist_to_graph(netlist)


	# function to add an edge to graph
	def addEdge(self,u,v):
		self.graph[u].append(v)

	def getWireId(self,name):
		i = self.wireNames.index(name)
		return self.wireIds[i]

	def netlist_to_graph(self,file):
		with open(file) as f:
			lines = f.readlines()
			count = 1
			for line in lines:
				# checking for comments
				# checking for empty lines using line feed ascii value - 10
				
				if line[0]=='#' or line[0]==chr(10):
					continue
				line = line.rstrip('\n')
				if len(line)>=5 and (line[0:5]=='INPUT'):
					line = line[6:].replace(' ','')
					for i in line.split(','):
						self.inputs.add(i)
					continue
				if len(line)>=6 and (line[0:6]=='OUTPUT'):
					line = line[7:].replace(' ','')
					for i in line.split(','):
						self.outputs.add(i)
					continue
				line = line.split(' ')
				e = line.index('=')
				# line[e+1] 	is the gate type : AND, OR, NOT, fanout etc
				# line[e+2:] 	are the inputs
				# line[:e] 		are the outputs
				self.blockCount[line[e+1]]+=1
				# removing the output
				g = Block(self.blockCount[line[e+1]],line[e+1],line[e+2:],line[:e])
				g.id = self.index
				self.blocks[self.index] = g
				self.index += 1
				# except Exception as e:
				# 	print(e)
				# 	print('Something wrong in line {}'.format(count))
				# 	break
				count+=1
			f.close()
			self.numBlocks = self.index
		self.getGraphFromCircuit()

	def getGraphFromCircuit(self):
		tempo = [[],[]]				# stores the outputs wires of each block that might be the input of another blocks
		for block in self.blocks.values():
			for o in block.outputNode:
				if o not in self.outputs:
					tempo[0].append(block.id)
					tempo[1].append(o)
				else:
					self.outputNodes.add(block.id)
		

		# create a wire object for each wire, in order to stored faults
		wires = []
		for n,i in enumerate(tempo[1]):
			self.wireNames.append(i)
			self.wireIds.append(self.index)
			w = Wire()
			w.inputNode = tempo[0][n]
			w.name = i
			w.id= self.index			
			self.index += 1
			wires.append(w)

		# connect all the nodes to create a directed graph
		for b in self.blocks.keys():
			for i in range(len(self.blocks[b].inputNode)):
				if self.blocks[b].inputNode[i] in tempo[1]:
					t = tempo[1].index(self.blocks[b].inputNode[i])
					w = wires[t]
					w.outputNode = self.blocks[b].id
					self.addEdge(tempo[0][t],w.id)
					self.addEdge(w.id,self.blocks[b].id)
					self.wires[w.id] = w
				if (self.blocks[b].inputNode[i] not in self.inputs) and (self.blocks[b].inputNode[i] not in self.outputs):
					self.blocks[b].inputNode[i] = self.getWireId(self.blocks[b].inputNode[i])
			for i in range(len(self.blocks[b].outputNode)):
				if self.blocks[b].outputNode[i] not in self.outputs:
					self.blocks[b].outputNode[i] = self.getWireId(self.blocks[b].outputNode[i])


	def checkConsistency(self,current,new):
		return self.intersectionTable[(current,new)]


	def Imply_and_check(self):
		# here we check for the existence of D and J frontiers
		# also apply the assignment queue / implication stack
		# if there are no problems, then update the signal values
		# else report failure
		if self.debug:
			print('Implication Stack:\t',self.implicationStack)
		
		

		# step1. Compute all values that can be uniquely determined by implication.
		for i in range(len(self.inputs),self.numBlocks-1):

			if self.blocks[i].value=='x':
				g = self.intersectionTable[(self.blocks[i].value,self.blocks[i].calc())]
				if g is not None:
					self.blocks[i].value = self.blocks[i].calc()
				else: 
					print('intersection failed 1: ')
					return False

				# propogate this value to next wire
				for j in self.blocks[i].outputNode:
					# print(i,j)

					self.wires[j].value = self.blocks[i].value
			else:
				# print('om',self.blocks[i].name,self.blocks[i].value)
				pass
		# step2. Check for consistency and assign values.
		while self.implicationStack:
			w,v = self.implicationStack.pop(0)
			g1 = self.checkConsistency(self.wires[w].value,v) 
			g2 = self.checkConsistency(self.blocks[self.wires[w].inputNode].value,v)
			# print('hi')
			if g1 is None:
				if self.debug:
					print('intersection failed 2: at wire {}, current: {}, new: {}'.format(w , self.wires[w].value,v))
				return False
			elif g2 is None:
				if self.debug:
					print('intersection failed 3: at node {}, current: {}, new: {}'.format(w , self.blocks[self.wires[w].inputNode].value,v))
				return False
			else:
				self.wires[w].value = v
				self.blocks[self.wires[w].inputNode].value = v

			
		# step3. Maintain the D-frontier and the J-frontier.
		for w in self.wireIds:
			b = self.blocks[self.wires[w].outputNode]
			# print(w,self.wires[w].value)
			if self.wires[w].value=='D' or self.wires[w].value=='E':
				if b.value=='x':
					if self.wires[w].outputNode not in self.dFrontier:
						self.dFrontier = [self.wires[w].outputNode]	+ self.dFrontier
		for b in range(len(self.inputs),self.numBlocks-1):
			if self.blocks[b].value!='x':
				inputs = [self.wires[i].value for i in self.blocks[b].inputNode]
				if 'x' in inputs:
					if b not in self.jFrontier:
						self.jFrontier.append(b)
				else:
					cal = self.blocks[b].calc()
					if (cal==1 and self.blocks[b].value=='D') or (cal==0 and self.blocks[b].value=='E'):
						
						return True
					elif cal!=self.blocks[b].value:
						if self.debug:
							print('Inconsistency : ',cal,self.blocks[b].value) 
						return False

		return True

	def errorAtPO(self):
		# check if the error has propogated to PO
		for i in self.outputNodes:
			for j in self.blocks[i].inputNode:
				if self.wires[j].value=='D' or self.wires[j].value=='E':
					return True
		return False

	def getControlValue(self,b):
		if self.blocks[b].type=='AND':
			return 0
		elif self.blocks[b].type=='OR':
			return 1
		elif self.blocks[b].type=='NAND':
			return 0
		elif self.blocks[b].type=='NOR':
			return 1
		elif self.blocks[b].type=='fanout':
			return -1
		elif self.blocks[b].type=='NOT':
			return -1

	def inputsAreSpecified(self,g):
		for i in self.blocks[g].inputNode:
			if self.wires[i].value=='x':
				return False
		return True

	def dalg(self):
		# print(self.dalg_cnt)
		if self.dalg_cnt>=self.recursionDepth:
			self.dalg_cnt = 0
			print('Maximum recursion depth reached!!')
			return False
		else:
			self.dalg_cnt += 1
			# begin
			# if Imply_and_check() = FAILURE then return FAILURE
			if not self.Imply_and_check():
				if self.debug:
					print('Imply_and_check failed!\nReturn to previous dalg.')
				return False
			# print('Imply_and_check passed!')
			# if (error not at PO) then
			if not self.errorAtPO():
				# print('Error not yet driven to PO')
				# begin
				# if D-frontier = 0 then return FAILURE
				if not self.dFrontier:
					if self.debug:
						print('D-Frontier empty! Failed to proceed further!')
						print('Return to previous dalg.')
					return False
				# repeat until all gates from D-frontier have been tried
				while self.dFrontier:
					# begin
					if self.debug:
						print('D-Frontier before popping:\t',self.dFrontier)
					# select an untried gate (G) from D-frontier
					G = self.dFrontier.pop(0)
					if self.debug:
						print('{}. {}'.format(G,self.blocks[G].name))
					# v = controlling value of G
					v = self.getControlValue(G)

					# assign ~v to every input of G with value x
					for i in self.blocks[G].inputNode:
						if self.wires[i].value=='x':
							# self.save_checkpoint()
							self.implicationStack.append((i,1-v))
					# if D-alg() = SUCCESS then return SUCCESS
					if self.dalg(): return True
					# end			
				# return FAILURE
				if self.debug:
					print('DALG FAIL: Reached the end of D-Frontier!')
					print('Return to previous dalg.')
				# self.recover_checkpoint()
				return False
				# end
			if self.debug:
				print('Error reached Primary Output! Solving J-Frontiers now!')
			# if J-frontier = 0 then return SUCCESS
			if not self.jFrontier:
				if self.debug: 
					print('J-Frontier is empty! Return SUCESS')
				return True
			if self.debug:
				print('J-Frontier before popping:\t',self.jFrontier)
			# select a gate (G) from the J-frontier
			G = self.jFrontier.pop(0)
			if self.debug:
				print('{}. {}'.format(G,self.blocks[G].name))
			cover = self.getCover(G)
			if self.blocks[G].type=='NOT' or self.blocks[G].type=='fanout':
				if not self.inputsAreSpecified(G):
					# self.save_checkpoint()
					self.implicationStack.append((self.blocks[G].inputNode[0],cover))
					if self.dalg(): return True
					else:
						if self.debug:
							print('loc1')
				else: 
					if self.debug:
						print('loc2')
			else:		
				# v = controlling value of G
				# v = self.getControlValue(G)
				while cover:
					self.save_checkpoint()
					v = cover.pop()
					# repeat until all inputs of G are specified
					if not self.inputsAreSpecified(G):
						# begin
						# self.save_checkpoint()
						# select an input (j) of G with value x
						for i in range(2):
							self.implicationStack.append((self.blocks[G].inputNode[i],v[i]))
						# if D-alg() = SUCCESS then return SUCCESS
						if self.dalg(): return True
						if self.debug:
							print('DALG Failed! Reversing value!')
						# if not self.recover_checkpoint():
						# 	return False
						self.recover_checkpoint()
						# self.save_checkpoint()
						# end
			# return FAILURE
			# self.recover_checkpoint()
			if self.debug:
				print('DALG Failed! Reached the end of line justification! Return to previous dalg.')
			return False
			# end
			pass

	def ATPG(self,node,fault):
		# step 1: set all values to 'x'
		# already done!

		# step 2: sensitize the s-a-v fault to ~v
		self.wires[node].value = fault
		self.blocks[self.wires[node].inputNode].value = fault
		test = self.dalg()
		print('Fault Testable?: ',test)
		# return test,self.testVector
		# self.dummy()

	def save_checkpoint(self):
		sublist_val = []
		
		for i in range(self.numBlocks):
			sublist_val.append(self.blocks[i].value)
		for i in self.wireIds:
			sublist_val.append(self.wires[i].value)

		self.checkpoint_val.append(sublist_val.copy())
		self.checkpoint_D.append(self.dFrontier.copy())
		self.checkpoint_J.append(self.jFrontier.copy())
		self.checkpoint_impl.append(self.implicationStack.copy())
		if self.debug:
			print("************ save checkpoint finish ************\n")
			print("checkpoint_val: ", len(self.checkpoint_val))
			print("checkpoint_J: ", len(self.checkpoint_J))
			print("checkpoint_D: ", len(self.checkpoint_D))
		

	def recover_checkpoint(self):
		if self.checkpoint_D==[]:
			return 0
		self.jFrontier = self.checkpoint_J.pop()
		self.dFrontier = self.checkpoint_D.pop()
		self.implicationStack = self.checkpoint_impl.pop()
		sublist_val = self.checkpoint_val.pop()
		for i in range(self.numBlocks):
			self.blocks[i].value = sublist_val.pop(0)
		for i in self.wireIds:
			self.wires[i].value = sublist_val.pop(0)
		if self.debug:
			print("************ recover checkpoint finish ************\n")
			print("checkpoint_val: ", len(self.checkpoint_val))
			print("checkpoint_J: ", len(self.checkpoint_J))
			print("checkpoint_D: ", len(self.checkpoint_D))
		return 1


	def getCover(self,g):
		if self.blocks[g].type=='AND':
			if self.blocks[g].value=='D' or self.blocks[g].value==1:
				return [(1,1)]
			return [(0,0),(0,1),(1,0)]
		if self.blocks[g].type=='OR':
			if self.blocks[g].value=='E' or self.blocks[g].value==0:
				return [(0,0)]
			return [(1,1),(1,0),(0,1)]
		if self.blocks[g].type=='NAND':
			if self.blocks[g].value=='E' or self.blocks[g].value==0:
				return [(1,1)]
			return [(0,0),(1,0),(0,1)]
		if self.blocks[g].type=='NOR':
			if self.blocks[g].value=='D' or self.blocks[g].value==1:
				return [(0,0)]
			return [(1,1),(1,0),(0,1)]
		if self.blocks[g].type=='NOT':
			if self.blocks[g].value=='D' or self.blocks[g].value==1:
				return 0
			if self.blocks[g].value=='E' or self.blocks[g].value==0:
				return 1
		if self.blocks[g].type=='fanout':
			if self.blocks[g].value=='D' or self.blocks[g].value==1:
				return 1
			if self.blocks[g].value=='E' or self.blocks[g].value==0:
				return 0
		

if __name__ == "__main__":
	# Input your circuit netlist here
	c = Circuit('netlist.txt')
	# c.netlist_to_graph('4_1_mux.txt')
	# when something goes wrong set the debug to 1
	c.debug = 0
	print('ID\tName\tInputs\tOutputs')
	for g in c.blocks.values():
		print('{}\t{}\t{}\t{}'.format(g.id,g.name,g.inputNode,c.graph[g.id]))
	for g in c.wires.values():
		print('{}\t{}\t{}\t{}'.format(g.id,g.name,g.inputNode,c.graph[g.id]))


	print('Enter the Fault location from the list of wires: ',end='')
	node = int(input())
	print('Enter the type of fault (0 for sa0 and 1 for sa1): ',end='')
	fault = int(input())
	fault = 'E' if fault else 'D'
	c.ATPG(node,fault)
	print('The test vector can be: ',end=' ')
	for i in range(len(c.inputs)):
		print(c.wires[c.blocks[i].outputNode[0]].value,end=' ')
	print()
		# print(c.wires[15].value,c.wires[16].value,c.wires[17].value)

