#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random, pprint
import SegmentTree as st
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt

class Node:
	tr = 0 # number of steps while communition propagation occurs
	h = 75 # number of link it remebers
	d = 2 # decay on the edges
	p = 100 # 1/proba to create its own community

	def __init__(self, id):
		self.id = id
		self.c = self.id
		self.H = [self.id]
		self.r = False
		self.rc = 0

	def add_contact(self, node_j):
		if len(self.H) >= Node.h:
			self.H.pop(0)
		self.H.append(node_j.c)

	def do_relabel(self, a, b):
		if random.random() < 1/Node.p:
			a[self.id] = self.c
			b[self.id] = self.id
			self.c = self.id
			self.rc = 0
			self.r = True
		return a,b

	# O(Node.h)
	def replace_contacts(self, a, b):
		self.H = [b if val == a else val for val in self.H]

	# O(Node.h)
	def compute_communities_weights(self):
		len_H = len(self.H)
		weights = {k:1 for k in set(self.H)}
		for k in range(len_H):
			weights[self.H[k]] += 1
			val = Node.h - Node.d*(len_H-k)
			if val > 1:
				weights[self.H[k]] += val - 1
		return zip(weights.values(),weights.keys())

	def update_relabel(self):
		if self.rc == Node.tr:
			self.r = False
			self.rc = 0
		if self.r:
			self.rc += 1

class CommunityDetector(object):
	def __init__(self, graph, tr, h, d, p):
		Node.tr = tr
		Node.h = h
		Node.d = d
		Node.p = p

		self.graph = graph
		self.a = {}
		self.b = {}
		self.V = {}

	def __find_community(self, node_i, node_j):
		node_i.add_contact(node_j)

		if not node_i.r:
			self.a,self.b = node_i.do_relabel(self.a,self.b)

		if node_i.r:
			node_i.replace_contacts(self.a[i],self.b[i])

		if node_j.r:
			node_i.replace_contacts(self.a[j],self.b[j])

		weights = node_i.compute_communities_weights()
		(_,node_i.c) = max(weights)
		
		node_i.update_relabel()

	def compute_accuracy(self, export_graph=False, draw_graph=False, time=st.SegmentTree.infinite):
		clust_attr = "clustId"

		labels_nodes = defaultdict(set)
		for node_id, node in self.V.items():
			labels_nodes[node.c].add(node_id)

		clust_nodes = defaultdict(set)
		G = self.graph.get_graph_at_time(time)
		for node_id, node_attr in G.nodes(data=True):
			clust_nodes[node_attr[clust_attr]].add(node_id)
		clust_cnt = sorted([(len(v),k) for k,v in clust_nodes.items()])

		clust_jaccard = defaultdict(dict)
		for label, lblset in labels_nodes.items():
			for clustId, clustset in clust_nodes.items():
				clust_jaccard[clustId][label] = len(lblset.intersection(clustset)) / float(len(lblset.union(clustset)))

		matching = {}
		best_jaccard = {}
		for _,clustId in clust_cnt:
			if len(clust_jaccard[clustId]) > 0:
				best_jaccard_value,best_label = max([(v,k) for k,v in clust_jaccard[clustId].items()])
				best_jaccard[clustId] = best_jaccard_value
				matching[best_label] = clustId
				for _,i in clust_cnt:
					del clust_jaccard[i][best_label]

		if export_graph:
			for node in G.node.keys():
				G.node[node]['label'] = self.V[node].c
				if self.V[node].c in matching:
					G.node[node]['matching'] = self.V[node].c
				else:
					G.node[node]['matching'] = -1
			nx.write_gexf(G, "graph_%d.gexf"%time)

			if draw_graph:
				colors = [(0,0,1),(0,1,0),(1,0,0),(0.9,0.7,0),(0.7,0,0.9)]
				node_color_mapping = {}
				for i in range(len(matching)):
					node_color_mapping[matching.keys()[i]] = colors[i]

				node_color_list = [node_color_mapping[self.V[node_id].c] if self.V[node_id].c in node_color_mapping else (0.5,0.5,0.5) for node_id in G.node.keys()]
				nx.draw_networkx(G, nx.spring_layout(G), False, node_color=node_color_list, alpha=0.7)

				plt.show()

		return sum([1 if (self.V[node].c in matching) and (node in clust_nodes[matching[self.V[node].c]]) else 0 for node in G.node.keys()]) / float(len(G.nodes()))

	# O(|E| * Node.h)
	def run(self, accuracy=False, export_graph=False, draw_graph=False, start=0, end=-1):
		E = []
		for diff,time in self.graph.get_all_diffs(start,end):
			for n in diff["remove_nodes_from"]:
				if n in self.a:
					del self.a[n]
				if n in self.b:
					del self.b[n]
				if n in self.V:
					del self.V[n]
			for n in diff["add_nodes_from"]:
				self.a[n] = 0
				self.b[n] = 0
				self.V[n] = Node(n)

			E = E + list(diff["add_edges_from"])
			random.shuffle(E)

			for (n,m) in E:
				if random.random() > 0.5:
					self.__find_community(self.V[n],self.V[m])
				else:
					self.__find_community(self.V[m],self.V[n])
			
			if accuracy:
				print "Accuracy at time %d: %f"%(time,self.compute_accuracy(export_graph, draw_graph, time))