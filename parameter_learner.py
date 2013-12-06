import GraphGenerator as gg
import CommunityDetection as cd
import pprint

def learn_parameters(G):
	tr_list = [0,5,10]
	h_list = [1,10,20,50,100]
	d_list = [0,5,10]
	p_list = [100,10000,10000000000000000]

	repeat = 10
	results = []
	for tr in tr_list:
		for h in h_list:
			for d in d_list:
				for p in p_list:
					temp = []
					for i in range(repeat):
						cdr = cd.CommunityDetector(G, tr, h, d, p)
						cdr.run()
						temp.append(cdr.compute_accuracy(False))
					results.append((sum(temp)/float(repeat), {"tr":tr,"h":h,"d":d,"p":p}))

	sorted_results = sorted(results)[-10:]
	pprint.pprint(sorted_results)