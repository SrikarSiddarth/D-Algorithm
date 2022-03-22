'''
Written by K. Srikar Siddarth
Roll number : 181EC218
'''

from collections import defaultdict


class Wire():
	def __init__(self):
		self.type = 'wire'
		self.fault = None
		self.value = 'x'		# current value
		self.cc0 = 0
		self.cc1 = 0
		self.co = 0
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


	def calcControllability(self):
		if self.type=='AND':
			c.wires[self.outputNode[0]].cc0 = min([c.wires[i].cc0 for i in self.inputNode]) + 1
			c.wires[self.outputNode[0]].cc1 = sum([c.wires[i].cc1 for i in self.inputNode]) + 1
		elif self.type=='OR':
			c.wires[self.outputNode[0]].cc0 = sum([c.wires[i].cc0 for i in self.inputNode]) + 1
			c.wires[self.outputNode[0]].cc1 = min([c.wires[i].cc1 for i in self.inputNode]) + 1
		elif self.type=='NOT':
			c.wires[self.outputNode[0]].cc0 = sum([c.wires[i].cc0 for i in self.inputNode]) + 1
			c.wires[self.outputNode[0]].cc1 = sum([c.wires[i].cc1 for i in self.inputNode]) + 1
		elif self.type=='NOR':
			c.wires[self.outputNode[0]].cc0 = min([c.wires[i].cc1 for i in self.inputNode]) + 1
			c.wires[self.outputNode[0]].cc1 = sum([c.wires[i].cc0 for i in self.inputNode]) + 1
		elif self.type=='NAND':
			c.wires[self.outputNode[0]].cc0 = sum([c.wires[i].cc1 for i in self.inputNode]) + 1
			c.wires[self.outputNode[0]].cc1 = min([c.wires[i].cc0 for i in self.inputNode]) + 1
		elif self.type=='XOR':
			c.wires[self.outputNode[0]].cc0 = min(min([c.wires[i].cc1 for i in self.inputNode]),min([c.wires[i].cc0 for i in self.inputNode])) + 1
			c.wires[self.outputNode[0]].cc1 = min(c.wires[self.inputNode[0]].cc1+c.wires[self.inputNode[1]].cc0,c.wires[self.inputNode[0]].cc0+c.wires[self.inputNode[1]].cc1)+1
		elif self.type=='XNOR':
			c.wires[self.outputNode[0]].cc1 = min(min([c.wires[i].cc1 for i in self.inputNode]),min([c.wires[i].cc0 for i in self.inputNode])) + 1
			c.wires[self.outputNode[0]].cc0 = min(c.wires[self.inputNode[0]].cc1+c.wires[self.inputNode[1]].cc0,c.wires[self.inputNode[0]].cc0+c.wires[self.inputNode[1]].cc1)+1
		elif self.type=='fanout':
			for i in range(len(self.outputNode)):
				c.wires[self.outputNode[i]].cc0 = c.wires[self.inputNode[0]].cc0
				c.wires[self.outputNode[i]].cc1 = c.wires[self.inputNode[0]].cc1

	def calcObservability(self):
		if self.type=='AND' or self.type=='NAND':
			c.wires[self.inputNode[0]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[1]].cc1 + 1
			c.wires[self.inputNode[1]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[0]].cc1 + 1
		elif self.type=='OR' or self.type=='NOR':
			c.wires[self.inputNode[0]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[1]].cc0 + 1
			c.wires[self.inputNode[1]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[0]].cc0 + 1
		elif self.type=='NOT':
			c.wires[self.inputNode[0]].co = c.wires[self.outputNode[0]].co + 1
		if self.type=='XOR' or self.type=='XNOR':
			c.wires[self.inputNode[0]].co = c.wires[self.outputNode[0]].co + min(c.wires[self.inputNode[1]].cc0,c.wires[self.inputNode[1]].cc1) + 1
			c.wires[self.inputNode[1]].co = c.wires[self.outputNode[0]].co + min(c.wires[self.inputNode[0]].cc0,c.wires[self.inputNode[0]].cc1) + 1
		elif self.type=='NOR':
			c.wires[self.inputNode[0]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[1]].cc0 + 1
			c.wires[self.inputNode[1]].co = c.wires[self.outputNode[0]].co + c.wires[self.inputNode[0]].cc0 + 1		
		elif self.type=='fanout':
			c.wires[self.inputNode[0]].co = min([c.wires[i].co for i in self.outputNode])
			

# This class represents a circuit
class Circuit():
	# Constructor
	def __init__(self,netlist):

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
		self.recursionDepth = 50
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

		self.netlist_to_graph(netlist)


	# function to add an edge to graph
	def addEdge(self,u,v):
		self.graph[u].append(v)

	def isBlock(self,idnum):
		return idnum<self.numBlocks

	def getWireId(self,name):
		i = self.wireNames.index(name)
		return self.wireIds[i]

	def getValue(self,node):
		# Assumption: That blocks are connected to wires and wires are connected to blocks
		# no two wires are connected to each other...

		if node.inputNode!=[]:
			node.value = node.calc()

	def Simulate(self):
		# Mark all the vertices as not visited
		visited = [False] * len(self.graph)
		# Create a queue for BFS
		queue = []
		for i in range(len(self.inputs)):
			self.wires[self.blocks[i].outputNode[0]].cc0 = 1
			self.wires[self.blocks[i].outputNode[0]].cc1 = 1
			queue.append(self.wires[self.blocks[i].outputNode[0]].outputNode)
		
		reverseOrder = []
		count = 0
		graphKeys = list(self.graph.keys())
		
		while queue:

			# Dequeue a vertex from 
			# queue and print it
			s = queue.pop(0)
			l = [self.wires[i].cc0 for i in self.blocks[s].inputNode]+[self.wires[i].cc1 for i in self.blocks[s].inputNode]		
			if self.debug:				
				print('Current node: {}, neighbours: {}, queue: {}'.format(s,self.graph[s],queue))			
				print(l)
			if 0 in l:
				queue.append(s)
			else:
				# print('om',self.wires[self.blocks[s].outputNode[0]].cc0)
				if self.wires[self.blocks[s].outputNode[0]].cc0==0:
					reverseOrder.append(s)
					self.blocks[s].calcControllability()
					visited[graphKeys.index(s)] = True
			
		
			count += 1
			# Get all adjacent vertices of the
			# dequeued vertex s. If a adjacent
			# has not been visited, then mark it
			# visited and enqueue it
			# if count==10:
			# 	break
			if visited[graphKeys.index(s)]:
				for i in self.graph[s]:
					if self.wires[i].outputNode in self.outputNodes:
						break
					x = graphKeys.index(self.wires[i].outputNode)
					if visited[x] == False:
						queue.append(self.wires[i].outputNode)					

		# reset the pins to x so that it can be simulated again
		# self.reset()
		# print(reverseOrder)
		while reverseOrder:
			self.blocks[reverseOrder.pop()].calcObservability()
		print('#\tWire\t(CC0,CC1)\tCO')
		for i in self.wireIds:
			print('{}\t{}\t( {}, {}) \t{}'.format(i,self.wires[i].name,self.wires[i].cc0,self.wires[i].cc1,self.wires[i].co))

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


if __name__ == '__main__':
	# give your input file here
	c = Circuit('netlist.txt')
	# print(c.outputNodes)
	c.debug = 0
	if c.debug:
		print('ID\tName\tInputs\tOutputs')
		for g in c.blocks.values():
			print('{}\t{}\t{}\t{}'.format(g.id,g.name,g.inputNode,c.graph[g.id]))
		for g in c.wires.values():
			print('{}\t{}\t{}\t{}'.format(g.id,g.name,g.inputNode,c.graph[g.id]))

	c.Simulate()
