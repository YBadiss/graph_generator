from collections import defaultdict

class SegmentTree:
	min_value	 = 0
	infinite = None

	@staticmethod
	def __includes(int1, int2):
		start1,end1 = int1
		start2,end2 = int2
		return (start1 <= start2) and ((end1 >= end2) or (end1 == SegmentTree.infinite))

	def __init__(self):
		self.max_value = 1
		self.nodes = defaultdict(set) # key = (start,end), val = list(element_ids)
		self.__inifinite_elements = set()

	def insert(self, element_id, interval):
		assert len(interval) == 2
		start,end = interval
		if end != SegmentTree.infinite:
			assert start < end
		assert start >= SegmentTree.min_value

		if end == SegmentTree.infinite:
			self.__inifinite_elements.add(element_id)
			self.__extend(start)
		else:
			self.__extend(end)
		self.__insert(element_id, start, end, SegmentTree.min_value, self.max_value)

	def __insert(self, element_id, start, end, in_start, in_end):
		key = (in_start, in_end)
		if SegmentTree.__includes((start,end), key):
			self.nodes[key].add(element_id)
		else:
			mid = int((in_start + in_end)/2)
			if start <= mid:
				self.__insert(element_id, start, end, in_start, mid)
			if (end > mid) or (end == SegmentTree.infinite):
				self.__insert(element_id, start, end, mid + 1, in_end)

	def delete(self, element_id, interval):
		assert len(interval) == 2
		start,end = interval
		if end != SegmentTree.infinite:
			assert start < end
		assert start >= SegmentTree.min_value

		self.__delete(element_id, start, end, SegmentTree.min_value, self.max_value)
		if element_id in self.__inifinite_elements:
			self.__inifinite_elements.remove(element_id)

	def __delete(self, element_id, start, end, in_start, in_end):
		key = (in_start, in_end)
		if SegmentTree.__includes((start,end), key):
			if not element_id in self.nodes[key]:
				print key
				print self.max_value
			self.nodes[key].remove(element_id)
		else:
			mid = int((in_start + in_end)/2)
			if start <= mid:
				self.__delete(element_id, start, end, in_start, mid)
			if (end > mid) or (end == SegmentTree.infinite):
				self.__delete(element_id, start, end, mid + 1, in_end)

	def query(self, point):
		if point == SegmentTree.infinite:
			# infinity is pretty equivalent to the first integer past the max value
			point = self.max_value + 1
		assert point >= SegmentTree.min_value

		if point <= self.max_value:
			return set(self.__query(point, SegmentTree.min_value, self.max_value))
		else:
			return self.__inifinite_elements

	def __query(self, point, in_start, in_end):
		matches = list(self.nodes[(in_start, in_end)])
		if in_start == in_end:
			return matches
		mid = int((in_start + in_end)/2)
		if point <= mid:
			return matches + self.__query(point, in_start, mid)
		else:
			return matches + self.__query(point, mid + 1, in_end) 

	def __extend(self, new_max_value):
		while new_max_value > self.max_value:
			temp_max_value = 2*(self.max_value+1)-1
			for element_id in self.__inifinite_elements:
				if element_id in self.nodes[(SegmentTree.min_value,self.max_value)]:
					self.nodes[(SegmentTree.min_value,self.max_value)].remove(element_id)
					self.nodes[(SegmentTree.min_value, temp_max_value)].add(element_id)
				else:
					self.nodes[(self.max_value+1, temp_max_value)].add(element_id)
			self.max_value = temp_max_value