import networkx as nx
import random
import bisect
import copy
import matplotlib.pyplot as plt
import SegmentTree as st
import pdb

class Graph:
	@staticmethod
	def __compute_cdf(flattened_distrib):
		cdf = [flattened_distrib[0]]
		for idx in xrange(1,len(flattened_distrib)):
			cdf.append(flattened_distrib[idx] + cdf[idx-1])
		return cdf

	@staticmethod
	def __remove_element_from_distrib(flattened_distrib, element_idx):
		factor = flattened_distrib[element_idx]
		flattened_distrib[element_idx] = 0
		if factor == 1:
			flattened_distrib = [0 for val in flattened_distrib]
		else:
			flattened_distrib = [val/(1-factor) for val in flattened_distrib]
		return flattened_distrib

	def __init__(self, is_directed=False):
		self.__is_directed = is_directed
		self.__nodes_time_index = st.SegmentTree()
		self.__nodes_data = {} # key = node_id ; value = {interval, metadata, edges_ids}
		self.__edges_time_index = st.SegmentTree()
		self.__edges_data = {} # key = edge_id ; value = {interval, metadata, src, dest}
		self.__edge_count = 0
		self.__node_count = 0
		self.__event_times = set()

	def __flatten_matrix_distrib(self, cross_set_distribs):
		flattened = []
		for i in range(len(cross_set_distribs)):
			for j in range(len(cross_set_distribs)):
				if self.__is_directed or (j >= i):
					flattened.append(cross_set_distribs[i][j])
				else:
					flattened.append(0)
		return flattened

	def create_nodes(self, node_count, common_metadata={}, start=0):
		return self.create_nodes_metadata([{k:v for k,v in common_metadata.items()} for i in range(node_count)], start)

	def create_nodes_metadata(self, nodes_metadata, start=0):
		"""
			Creates nodes with the attributes contained in nodes_attr.
			Returns a list of ids of the created nodes
		"""
		assert start >= 0
		self.__event_times.add(start)

		list_ids = []
		for metadata in nodes_metadata:
			node_id = self.__node_count + 1
			interval = (start, st.SegmentTree.infinite)
			# self.__G.add_node(node_id, metadata)
			self.__nodes_data[node_id] = {'interval':interval , 'metadata':metadata, 'edges_ids':set()}
			self.__nodes_time_index.insert(node_id, interval)
			self.__node_count += 1
			list_ids.append(node_id)
		return set(list_ids)

	def update_nodes(self, node_set, common_metadata):
		for node_id in node_set:
			for k,v in common_metadata.items():
				self.__nodes_data[node_id]['metadata'][k] = v

	def delete_nodes(self, nodes_idx, end=1):
		"""
			Delete the nodes with the ids contained in nodes_idx
		"""
		assert end >= 1
		self.__event_times.add(end)

		for node_id in nodes_idx:
			if node_id in self.__nodes_data:
				interval = self.__nodes_data[node_id]['interval']
				self.__nodes_time_index.delete(node_id,interval)
				new_interval = (interval[0],end)
				self.__nodes_time_index.insert(node_id, new_interval)
				self.__nodes_data[node_id]['interval'] = new_interval

				edges_idx = {edge_id for edge_id in self.__nodes_data[node_id]['edges_ids']}
				self.delete_edges(edges_idx, end)
				for edge_id in edges_idx:
					if edge_id in self.__edges_data:
						cur_start,cur_end = self.__edges_data[edge_id]['interval']
						if (cur_end > end) or (cur_end == st.SegmentTree.infinite):
							# remove it, FOR REAL
							self.__edges_time_index.delete(edge_id,(cur_start,cur_end))
							src = self.__edges_data[edge_id]['src']
							dest = self.__edges_data[edge_id]['dest']
							self.__nodes_data[src]['edges_ids'].remove(edge_id)
							self.__nodes_data[dest]['edges_ids'].remove(edge_id)
							del self.__edges_data[edge_id]
			else:
				print "Node id", node_id, "does not exist, skipping"

	def create_edges(self, nodes_list, common_metadata={}, start=0):
		return self.create_edges_metadata(nodes_list, [{k:v for k,v in common_metadata.items()} for i in range(len(nodes_list))], start)

	def create_edges_metadata(self, nodes_list, edges_metadata, start=0):
		assert len(nodes_list) == len(edges_metadata)
		self.__event_times.add(start)
		
		list_ids = []
		for i in range(len(nodes_list)):
			src,dest = nodes_list[i]
			if src in self.__nodes_data and dest in self.__nodes_data:
				src_node = self.__nodes_data[src]
				dest_node = self.__nodes_data[dest]
				
				edge_start = max(start,src_node['interval'][0],dest_node['interval'][0])
				if src_node['interval'][1] == st.SegmentTree.infinite:
					edge_end = dest_node['interval'][1]
				elif dest_node['interval'][1] == st.SegmentTree.infinite:
					edge_end = src_node['interval'][1]
				else:
					edge_end = min(src_node['interval'][1],dest_node['interval'][1])

				if edge_start < edge_end or edge_end == st.SegmentTree.infinite:
					edge_id = self.__edge_count + 1
					interval = (edge_start, edge_end)
					self.__edges_data[edge_id] = {'interval':interval , 'metadata':edges_metadata[i], 'src':src, 'dest':dest}
					self.__edges_time_index.insert(edge_id, interval)
					src_node['edges_ids'].add(edge_id)
					dest_node['edges_ids'].add(edge_id)
					self.__edge_count += 1
					list_ids.append(edge_id)
				else:
					print "Impossible to create edge", i
			else:
				print "Src and dest of edge", i, "do not exist, skipping"
		return list_ids

	def delete_edges(self, edges_idx, end=1):
		assert end >= 1
		self.__event_times.add(end)

		for edge_id in edges_idx:
			if edge_id in self.__edges_data:
				cur_start,cur_end = self.__edges_data[edge_id]['interval']
				if (cur_end > end or cur_end == st.SegmentTree.infinite) and cur_start < end:
					self.__edges_time_index.delete(edge_id,(cur_start,cur_end))
					new_interval = (cur_start,end)
					self.__edges_time_index.insert(edge_id, new_interval)
					self.__edges_data[edge_id]['interval'] = new_interval
			else:
				print "Edge id", edge_id, "does not exist, skipping"

	def create_random_edges(self, edge_count, node_sets, cross_set_distribs, node_select_distribs, start=0):
		"""
			node_sets: size = n ; list of sets (can be of different sizes)
			cross_set_distribs: size = n x n ; matrix of floats summing to one
			node_select_distrib: size = n ; list of function pointers

			Create edge_count edges between nodes belonging to the sets of node_sets.
			The distribution of edges linking sets of nodes is discribed in the multinomial cross_set_distribs.
			Choosing which nodes within sets are actually linked together is decided using the function pointers ofode_select_distrib.

			Returns success code (True/False)
		"""
		# For each edge we find which sets are linked using the multinomial
		# Set1=smallest of the two sets ; Set2=largest of the two sets
		# We get a node n1 from Set1 using node_select_distrib
		# We create a new set of nodes from Set2 by removing the nodes already connected to n1 and removing n1
		# If the new set is empty, we remove n1 from Set1 and rdo the previous steps
		# Else, we chose an node n2 from the new set and create an edge between n1 and n2
		assert start >= 0

		# flatten the cross_set_distribs
		flattened_distrib = self.__flatten_matrix_distrib(cross_set_distribs)
		cdf = Graph.__compute_cdf(flattened_distrib)
		assert cdf[-1] == 1, "cross_set_distribs must sum to 1"
		self.__event_times.add(start)

		graph = self.get_graph_at_time(start)
		existing_node_set = set(graph.nodes())
		filtered_node_sets = []
		for node_set in node_sets:
			filtered_node_sets.append(node_set.intersection(existing_node_set))

		for edge in range(edge_count):
			edge_added = False
			while not edge_added:
				cdf_idx = bisect.bisect_left(cdf, random.random())
				if cdf_idx >= len(cdf):
					print "The graph is completely connected"
					return False
				i = cdf_idx % len(filtered_node_sets)
				j = int(cdf_idx / len(filtered_node_sets))

				if len(filtered_node_sets[i]) < len(filtered_node_sets[j]) or self.__is_directed:
					src_idx, dest_idx = i,j
				else:
					src_idx, dest_idx = j,i

				src_set, dest_set = {node_id for node_id in filtered_node_sets[src_idx]}, filtered_node_sets[dest_idx]
				src_distrib, dest_distrib = node_select_distribs[src_idx], node_select_distribs[dest_idx]
				
				while len(src_set) > 0 and not edge_added:
					node_1 = src_distrib.get_item(src_set)
					except_set = set(graph[node_1].keys() + [node_1])
					filtered_destset = dest_set.difference(except_set)
					if len(filtered_destset) > 0:
						node_2 = dest_distrib.get_item(filtered_destset)
						graph.add_edge(node_1, node_2)
						self.create_edges_metadata([(node_1,node_2)], [{}], start) #nodes_list, edges_metadata, start=0)
						edge_added = True
					else:
						# remove node_1 from src_set
						src_set.remove(node_1)
				if not edge_added:
					flattened_distrib = Graph.__remove_element_from_distrib(flattened_distrib, cdf_idx)
					cdf = Graph.__compute_cdf(flattened_distrib)
		return True


	def delete_random_edges(self, edge_count, node_sets, cross_set_distribs, node_select_distribs, end=0):
		"""
			node_sets: size = n ; list of lists (can be of different sizes)
			cross_set_distribs: size = n x n ; matrix of floats summing to one
			node_select_distrib: size = n ; list of function pointers

			Delete edge_count edges between nodes belonging to the sets of node_sets.
			The distribution of edges linking sets of nodes is discribed in the multinomial cross_set_distribs.
			Choosing which nodes within sets are actually linked together is decided using the function pointers ofode_select_distrib.

			Returns success code (True/False)
		"""

		assert end >= 0

		# flatten the cross_set_distribs
		flattened_distrib = self.__flatten_matrix_distrib(cross_set_distribs)
		cdf = Graph.__compute_cdf(flattened_distrib)
		assert cdf[-1] == 1, "cross_set_distribs must sum to 1"
		self.__event_times.add(end)

		graph = self.get_graph_at_time(end)
		existing_node_set = set(graph.nodes())
		filtered_node_sets = []
		for node_set in node_sets:
			filtered_node_sets.append(node_set.intersection(existing_node_set))

		for edge in range(edge_count):
			edge_deleted = False
			while not edge_deleted:
				cdf_idx = bisect.bisect_left(cdf, random.random())
				if cdf_idx >= len(cdf):
					print "The graph is completely disconected"
					return False
				i = cdf_idx % len(filtered_node_sets)
				j = int(cdf_idx / len(filtered_node_sets))

				if len(filtered_node_sets[i]) < len(filtered_node_sets[j]) or self.__is_directed:
					src_idx, dest_idx = i,j
				else:
					src_idx, dest_idx = j,i

				src_set, dest_set = {node_id for node_id in filtered_node_sets[src_idx]}, filtered_node_sets[dest_idx]
				src_distrib, dest_distrib = node_select_distribs[src_idx], node_select_distribs[dest_idx]

				while len(src_set) > 0 and not edge_deleted:
					node_1 = src_distrib.get_item(src_set)
					node_edge_matching = {}
					for edge_id in self.__nodes_data[node_1]['edges_ids']:
						if self.__edges_data[edge_id]['dest'] == node_1:
							node_edge_matching[self.__edges_data[edge_id]['src']] = edge_id
						else:
							node_edge_matching[self.__edges_data[edge_id]['dest']] = edge_id

					filtered_destset = dest_set.intersection(graph[node_1].keys())
					if len(filtered_destset) > 0:
						node_2 = dest_distrib.get_item(filtered_destset)
						graph.remove_edge(node_1, node_2)
						self.delete_edges([(node_edge_matching[node_2])], end)
						edge_deleted = True
					else:
						# remove node_1 from src_set
						src_set.remove(node_1)
				if not edge_deleted:
					flattened_distrib = Graph.__remove_element_from_distrib(flattened_distrib, cdf_idx)
					cdf = Graph.__compute_cdf(flattened_distrib)
		return True


	def get_graph_at_time(self, time):
		nodes_ids = self.__nodes_time_index.query(time)
		edges_ids = self.__edges_time_index.query(time)
		graph_t = nx.DiGraph() if self.__is_directed else nx.Graph()
		
		for node_id in nodes_ids:
			graph_t.add_node(node_id, self.__nodes_data[node_id]['metadata'])
		for edge_id in edges_ids:
			edge = self.__edges_data[edge_id]
			graph_t.add_edge(edge['src'], edge['dest'], edge['metadata'])
		return graph_t

	def get_diff_between_times(self, start, end):
		nodes_ids_start = self.__nodes_time_index.query(start)
		edges_ids_start = self.__edges_time_index.query(start)
		nodes_ids_end = self.__nodes_time_index.query(end)
		edges_ids_end = self.__edges_time_index.query(end)

		diff = {}
		diff["add_nodes_from"] = nodes_ids_end.difference(nodes_ids_start)
		diff["remove_nodes_from"] = nodes_ids_start.difference(nodes_ids_end)
		add_edges_id = edges_ids_end.difference(edges_ids_start)
		remove_edges_id = edges_ids_start.difference(edges_ids_end)
		diff["add_edges_from"] = {(self.__edges_data[edge_id]['src'],self.__edges_data[edge_id]['dest']) for edge_id in add_edges_id}
		diff["remove_edges_from"] = {(self.__edges_data[edge_id]['src'],self.__edges_data[edge_id]['dest']) for edge_id in remove_edges_id}
		return diff

	def __get_state_at_time(self, start=0):
		time = list(self.__event_times)[start]
		nodes_ids_start = self.__nodes_time_index.query(time)
		edges_ids_start = self.__edges_time_index.query(time)
		diff = {}
		diff["add_nodes_from"] = nodes_ids_start
		diff["remove_nodes_from"] = set()
		diff["add_edges_from"] = {(self.__edges_data[edge_id]['src'],self.__edges_data[edge_id]['dest']) for edge_id in edges_ids_start}
		diff["remove_edges_from"] = set()
		return diff

	def get_all_diffs(self, start=0, end=-1):
		if end < 0:
			end = len(self.__event_times)
		else:
			end = min(end,len(self.__event_times))

		if len(self.__event_times) > start and start <= end:
			list_event_times = list(self.__event_times)
			yield self.__get_state_at_time(start), list_event_times[start]

			for i in range(start,end-1):
				time1 = list_event_times[i]
				time2 = list_event_times[i+1]
				yield self.get_diff_between_times(time1,time2), time2

	def plot(self, t=st.SegmentTree.infinite):
		nx.draw_networkx(self.get_graph_at_time(t))
		plt.show()

	def plot_sequence(self):
		for t in self.__event_times:
			print "Graph at time", t
			self.plot(t)


class Distribution:
	def __init__(self, **kwargs):
		pass
	def get_item(self, item_set):
		raise "Not Implemented: Distribution is an Interface"

class GaussianDistrib(Distribution):
	def __init__(self, sigma, mu):
		self.sigma = sigma
		self.mu = mu
	def get_item(self, item_set):
		pass

class UniformDistrib(Distribution):
	def get_item(self, item_set):
		return list(item_set)[random.randint(0,len(item_set)-1)]

class TestDistrib(Distribution):
	def get_item(self, item_set):
		return list(item_set)[0]
