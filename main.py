import GraphGenerator as gg
import CommunityDetection as cd
from parameter_learner import *

def main(factor):
	G = gg.Graph()
	set1 = G.create_nodes(200, {"clustId":1}, 0)
	set2 = G.create_nodes(200, {"clustId":2}, 0)
	set3 = G.create_nodes(200, {"clustId":2}, 0)
	set4 = G.create_nodes(50, {"clustId":4}, 0)
	set5 = G.create_nodes(50, {"clustId":5}, 0)

	for i in range(4):
		G.create_random_edges(	500*factor,
								[set1, set2, set3, set4, set5], 
								[[0.303,0.005,0.005,0.001,0.001],
								 [0    ,0.17 ,0.24	 ,0.001,0.001],
								 [0    ,0    ,0.17 ,0.001,0.001],
								 [0    ,0    ,0    ,0.05 ,0.001],
								 [0    ,0    ,0    ,0    ,0.05 ]],
								[gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib()],
								i)

	for i in range(4,7):
		G.create_random_edges(	40*factor,
								[set1, set2, set3, set4, set5], 
								[[0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,1   ],
								 [0   ,0   ,0   ,0   ,0   ]],
								[gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib()],
							    i)

	for i in range(7,9):
		G.delete_random_edges(	200*factor,
								[set1, set2, set3, set4, set5], 
								[[0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,1   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,0   ],
								 [0   ,0   ,0   ,0   ,0   ]],
								[gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib()],
							    i)

	G.delete_random_edges(	0,
							[set1, set2, set3, set4, set5], 
							[[0   ,0   ,0   ,0   ,0   ],
							 [0   ,0   ,1   ,0   ,0   ],
							 [0   ,0   ,0   ,0   ,0   ],
							 [0   ,0   ,0   ,0   ,0   ],
							 [0   ,0   ,0   ,0   ,0   ]],
							[gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib()],
						    9)

	# for i in range(9,14):
	# 	G.delete_random_edges(	40*factor,
	# 							[set1, set2, set3, set4, set5], 
	# 							[[0   ,0   ,0   ,0   ,0   ],
	# 							 [0   ,0   ,1   ,0   ,0   ],
	# 							 [0   ,0   ,0   ,0   ,0   ],
	# 							 [0   ,0   ,0   ,0   ,0   ],
	# 							 [0   ,0   ,0   ,0   ,0   ]],
	# 							[gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib(), gg.UniformDistrib()],
	# 						    i)

	cdr = cd.CommunityDetector(G, 10, 100, 5, 10000)
	cdr.run(True, True, False, 0, 4)

	G.update_nodes(set5, {"clustId":4})
	cdr.run(True, True, False, 4, 7)

	G.update_nodes(set3, {"clustId":3})
	cdr.run(True, True, False, 7, 12)

main(2)