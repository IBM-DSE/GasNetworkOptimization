#dd-markdown #### Imports
#dd-cell
from sys import stdout
import pandas as pd
#dd-markdown Extract input data
#dd-cell
gasnetworkNodes = inputs['gasnetwork_nodes']
gasnetworkPipes = inputs['gasnetwork_pipes']
gasnetworkExtensions = inputs['gasnetwork_extensions']
gasnetworkScenarios = []
for name in [s for s in inputs.keys() if "scenario" in s]:
    gasnetworkScenarios.append(inputs[name])
#dd-markdown ## Step 2: Load parameters
#dd-markdown Read parameters from file Parameter
#dd-cell
#Parameter table (assumes 'param' and 'value' pairs)
if 'Parameter' in inputs.keys():
    params = inputs['Parameter'].set_index(['param'])
else:
    params = pd.DataFrame(columns=['param','value']).set_index('param')
params
#dd-markdown Define the scaling value, each scenario will be scaled by this value. A value of 1.0 means that the gas quantities specified in the scenarios set are considered without modification. 
#dd-cell
scale = 1.0 # feasible setting, no network extensions needed
if 'scenarioScale' in params.index:
    scale = float(params.loc['scenarioScale'].value)
#dd-markdown ## Step 3: Model the data
#dd-markdown 
#dd-markdown * a data store is used for storing the gas network and the scenarios
#dd-markdown * all nodes are read from file gasnetwork_nodes
#dd-markdown * all pipes are read from file gasnetwork_pipes
#dd-markdown * all extension candidates are read from file gasnetwork_extensions
#dd-markdown * several scenarios are read from several files gasnetwork_scn*
#dd-cell
import networkx as nx
from math import pow, sqrt, log

class DataStore:
    """
    Class DataStore.

    This class is used to store the network, the extension candidates and the scenarios.
    A directed graph is used for the network and the candidates. Node and arc attributes
    store  the provided network information. Several access functions are provided for 
    accessing the data. 
    """
    def __init__(self, gasnetworkNodes, gasnetworkPipes, gasnetworkExtensions, gasnetworkScenarios, scale, inputs):

        assert isinstance(scale, float)
        self.scale = scale
        self.G = nx.DiGraph()

        stdout.write("\nThe following gas network and extension candidates are loaded:\n")

        self.__readNodes(gasnetworkNodes)
        self.__readPipes(gasnetworkPipes)
        self.__readExtensionCandidates(gasnetworkExtensions)
        self.__readScenarios(gasnetworkScenarios)

    def __readNodes(self, gasnetworkNodes):
        inputDataNodes = gasnetworkNodes
        assert inputDataNodes['name'].dtype == object
        assert inputDataNodes['x'].dtype == float
        assert inputDataNodes['y'].dtype == float
        assert inputDataNodes['pressureMin'].dtype == float
        assert inputDataNodes['pressureMax'].dtype == float
        assert inputDataNodes['isSource'].dtype == int

        for index, row in inputDataNodes.iterrows():
            self.G.add_node(row['name'], 
                            pos=(row['x'],row['y']),
                            pressureMin=row['pressureMin'],
                            pressureMax=row['pressureMax'],
                            isSource=row['isSource'])
            
        stdout.write("\nNodes:\n")
        print inputDataNodes
        
    def __readPipes(self, gasnetworkPipes):
        inputDataPipes = gasnetworkPipes
        assert inputDataPipes['from'].dtype == object
        assert inputDataPipes['to'].dtype == object
        assert inputDataPipes['flowMin'].dtype == int
        assert inputDataPipes['flowMax'].dtype == int
        assert inputDataPipes['length'].dtype == float
        assert inputDataPipes['diameter'].dtype == int
        assert inputDataPipes['name'].dtype == object

        for index, row in inputDataPipes.iterrows():
            weymouthConst = self.__computeWeymouthConst(row['length'],row['diameter'])
            self.G.add_edge(row['from'], 
                            row['to'],
                            flowMin=row['flowMin'],
                            flowMax=row['flowMax'],
                            length=row['length'],
                            diameter=row['diameter'],
                            name=row['name'],
                            weymouth=weymouthConst,
                            isOriginal=True)
            
        stdout.write("\nPipes:\n")
        print inputDataPipes
         
    def __readExtensionCandidates(self, gasnetworkExtensions):
        extensions = gasnetworkExtensions
        assert extensions['from'].dtype == object
        assert extensions['to'].dtype == object
        assert extensions['length'].dtype == float
        assert extensions['diameter'].dtype == float
        assert extensions['cost'].dtype == float
        assert extensions['name'].dtype == object

        for index, row in extensions.iterrows():
            weymouthConst = self.__computeWeymouthConst(row['length'],row['diameter'])                       
            self.G.add_edge(row['from'], 
                            row['to'],
                            flowMin=-1000000,
                            flowMax=1000000,
                            length=row['length'],
                            diameter=row['diameter'],
                            name=row['name'],
                            weymouth=weymouthConst,
                            cost=row['cost'],
                            isOriginal=False)
            
        stdout.write("\nExtension candidates:\n")
        print extensions
        
    def __readScenarios(self, gasnetworkScenarios):
        self.scnList = []
        for scn in gasnetworkScenarios:
            scenario = {}
            assert scn['name'].dtype == object
            assert scn['value'].dtype == float
            for index, row in scn.iterrows():
                scenario[row['name']] = row['value']
            self.scnList.append(scenario)
            
    def __computeWeymouthConst(self, length, diameter):
        length = float(length) # in km
        diameter = float(diameter) # in mm
        roughness = 0.05
        temperature = 281.15;
        density = 0.616;
        zValue = 0.8;

        c = diameter
        c = pow(c,  5) * pow((2 * log(3.7 * c / roughness) / log(10)), 2) * 96.074830e-15
        c = c / (zValue * temperature * length * density);
        c = float(int(c*100.0)) / 100.0

        return c

    def getScnList(self):
        return self.scnList

    def getNodes(self):
        return self.G.nodes()

    def getArcs(self):
        return self.G.edges()

    def getOrigArcs(self):
        isOriginal = nx.get_edge_attributes(self.G, 'isOriginal')
        return [arc for arc in self.G.edges() if isOriginal[arc]]

    def getExtArcs(self):
        isOriginal = nx.get_edge_attributes(self.G, 'isOriginal')
        return [arc for arc in self.G.edges() if isOriginal[arc] == False]

    def getFromNode(self, arc):
        return arc[0]
    
    def getToNode(self, arc):
        return arc[1]

    def isSource(self, node):
        isSource = nx.get_node_attributes(self.G, 'isSource')
        return bool(isSource[node])
    
    def getOutArcs(self, node):
        return self.G.out_edges(node)

    def getInArcs(self, node):
        return self.G.in_edges(node)

    def getNodePressureMax(self, node):
        pressureMax = nx.get_node_attributes(self.G, 'pressureMax')
        return float(pressureMax[node])

    def getNodePressureMin(self, node):
        pressureMin = nx.get_node_attributes(self.G, 'pressureMin')
        return float(pressureMin[node])

    def getArcFlowMax(self, arc):
        flowMax = nx.get_edge_attributes(self.G, 'flowMax')
        return float(flowMax[arc])

    def getArcFlowMin(self, arc):
        flowMin = nx.get_edge_attributes(self.G, 'flowMin')
        return float(flowMin[arc])

    def getArcCost(self, arc):
        cost = nx.get_edge_attributes(self.G, 'cost')
        return float(cost[arc])
    
    def getWeymouthConst(self, arc):
        weymouth = nx.get_edge_attributes(self.G, 'weymouth')
        return float(weymouth[arc])
    
    def getArcLength(self, arc):
        length = nx.get_edge_attributes(self.G, 'length')
        return float(length[arc])
    
    def getArcDiameter(self, arc):
        diameter = nx.get_edge_attributes(self.G, 'diameter')
        return float(diameter[arc])
    
    def getArcName(self, arc):
        name = nx.get_edge_attributes(self.G, 'name')
        return name[arc]
    
    def getGraphCopy(self):
        return self.G.copy()
    
    def getScnScale(self):
        return self.scale
#dd-cell
ds = DataStore(gasnetworkNodes, gasnetworkPipes, gasnetworkExtensions, gasnetworkScenarios, scale, inputs)
#dd-markdown ### Step 4: Set up the optimization model
#dd-cell
from docplex.mp.model import Model
mdl = Model(name="Gas_Network_Optimization")
#dd-markdown #### Define the optimization variables
#dd-markdown 
#dd-markdown Define the decision variables for deciding whether an extension candidate is build
#dd-cell
x = {}
for arc in ds.getExtArcs():
    x[arc] = mdl.binary_var(name="x(%s,%s)" % (ds.getFromNode(arc), ds.getToNode(arc)))
#dd-markdown For each scenario define the squared pressure variables for  each node and the flow variables for each arc
#dd-cell
pi = {}
q = {}
for index in list(range(len(ds.getScnList()))):
    for node in ds.getNodes():
        pi[node,index] = mdl.continuous_var(name="p(%s,%s)" % (node,index), 
                                            ub=int(pow(ds.getNodePressureMax(node), 2)),
                                            lb=int(pow(ds.getNodePressureMin(node), 2)))

    for arc in ds.getArcs():
        q[arc,index] = mdl.continuous_var(name="q(%s,%s,%s)" % (ds.getFromNode(arc), ds.getToNode(arc), index), 
                                          ub=ds.getArcFlowMax(arc), 
                                          lb=ds.getArcFlowMin(arc))
#dd-markdown #### Express the physical constraints
#dd-markdown Add flow conservation constraints for every scenario
#dd-cell
for index, scn in enumerate(ds.getScnList()):
    for node in ds.getNodes():
        scale = ds.getScnScale()
        mdl.add_constraint(mdl.sum(q[arc,index] for arc in ds.getOutArcs(node)) - 
                           mdl.sum(q[arc,index] for arc in ds.getInArcs(node)) == scn[node] * scale)
#dd-markdown Add approximation of weymouth constraints for every arc in every scenario stating that arc flow is induced by the squared pressure difference at the end nodes
#dd-cell
for index in list(range(len(ds.getScnList()))):
    for arc in ds.getOrigArcs():
        mdl.add_constraint(q[arc,index] -
                           ds.getWeymouthConst(arc) * pi[ds.getFromNode(arc),index] +
                           ds.getWeymouthConst(arc) * pi[ds.getToNode(arc),index] == 0)
#dd-markdown Add approximation of weymouth constraints on extension candidates using indicator constraints. Also ensure that the flow equals zero if the arc is not build
#dd-cell
for index in list(range(len(ds.getScnList()))):
    for arc in ds.getExtArcs():
        mdl.add_indicator(x[arc], 
                          q[arc,index] -
                          ds.getWeymouthConst(arc) * pi[ds.getFromNode(arc),index] +
                          ds.getWeymouthConst(arc) * pi[ds.getToNode(arc),index] == 0,
                          1)
        mdl.add_indicator(x[arc], q[arc,index] == 0, 0)
#dd-markdown #### Express the business objective
#dd-markdown Set the objective function which is minimizing the investment costs for the new pipes
#dd-cell
mdl.minimize(mdl.sum(ds.getArcCost(arc) * x[arc] for arc in ds.getExtArcs()))
#dd-markdown Set objective as KPI for the model
#dd-cell
total_cost = mdl.sum(ds.getArcCost(arc) * x[arc] for arc in ds.getExtArcs())
mdl.add_kpi(total_cost, "Total Cost")
#dd-markdown ## Step 5: Solve model and save the solution
#dd-cell
from docplex.mp import sdetails
stdout.write("\nSolving model....\n")
msol = mdl.solve(log_output=True)
stdout.write("Solving done after %.2f" % mdl.get_solve_details().time + " seconds.\n")
#dd-markdown Store KPIs
#dd-cell
all_kpis = [(kp.name, kp.compute()) for kp in mdl.iter_kpis()]
df_kpis = pd.DataFrame(all_kpis, columns=['kpi', 'value'])
#dd-markdown Save the extensions that should be build
#dd-cell
extensions = pd.DataFrame(columns=['Name', 'From', 'To', 'Length', 'Diameter', 'Cost', 'Build'])
if msol:    
    for arc in ds.getExtArcs():
        name = ds.getArcName(arc)
        extensions = extensions.append(pd.DataFrame([[name,
                                                      ds.getFromNode(arc), 
                                                      ds.getToNode(arc), 
                                                      ds.getArcLength(arc), 
                                                      ds.getArcDiameter(arc), 
                                                      ds.getArcCost(arc),
                                                      int(msol[x[arc]])]], 
                                                    columns=['Name', 'From', 'To', 'Length', 'Diameter', 'Cost', 'Build']), 
                                       ignore_index=True)  
outputs['extensions_to_build'] = extensions
