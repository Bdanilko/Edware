#!/usr/bin/env python

# * **************************************************************** **
#
# File: program_data.py
# Desc: The class used to store a program
# Note:
#
# Author: Brian Danilko, Likeable Software (brian@likeablesoftware.com)
#
# Copyright 2006, Microbric Pty Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (in the docs/licenses directory)
# for more details.
#
# Svn: $Id: program_data.py 52 2006-12-03 00:44:40Z briand $
# * **************************************************************** */

import win_data

class Bric(object):
    def __init__(self, id, bric_name):
        self.id = id
        self.bric_name = bric_name
        self.bric_data = None
        self.next_id = [-1, -1]
        self.prev_id = [-1, -1]
        self.if_variant = None

    def get_next_id(self, which=0):
        return self.next_id[which]

    def get_prev_id(self, which=0):
        return self.prev_id[which]

    def dump(self):
        print "Bric %d - p:%d, n:%d, p2:%d, n2:%d name:%s, if_var: %s, data:%s" % (self.id,
                                                                                   self.prev_id[0], self.next_id[0],
                                                                                   self.prev_id[1], self.next_id[1],
                                                                                   self.bric_name, self.if_variant,
                                                                                   self.bric_data)


class Program(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.bric_count = 0
        self.brics = {}
        self.streams = []
        self.move_id = []
        self.start_id = 0

        self.add_new_bric(0, 0, "Main")

    def dump(self):
        print "Streams:", self.streams
        print "Move_id:", self.move_id
        print "Bric count:", self.bric_count
        for k in self.brics:
            self.brics[k].dump()

    def get_stream_count(self):
        return len(self.streams)

    def get_bric_count(self):
        return self.bric_count
    
    def get_stream_id(self, which):
        if ((which < self.get_stream_count()) and
            (self.streams[which] not in self.move_id)):
            return self.streams[which]
        else:
            return -1

    def get_bric_name(self, id):
        return self.brics[id].bric_name

    def set_bric_data(self, id, data):
        self.brics[id].bric_data = data

    def get_bric_data(self, id):
        return self.brics[id].bric_data
    
    def get_next_id(self, cur_id, which=0):
        # skip a bric being moved

        next_id = self.brics[cur_id].next_id[which]
        while ((next_id >= 0) and (next_id in self.move_id)):
            next_id = self.brics[next_id].next_id[0]

        #print next_id
        return next_id

    def get_prev_id(self, cur_id, which=0):
        prev_id = self.brics[cur_id].prev_id[which]
        while ((prev_id >= 0) and (prev_id in self.move_id)):
            prev_id = self.brics[prev_id].prev_id[0]

        #print prev_id
        return prev_id

    def get_bric_if_variant(self, id):
        return self.brics[id].if_variant

    def set_bric_if_variant(self, id, variant):
        if (id in self.brics):
            self.brics[id].if_variant = variant
        else:
            print "WARNING - old bric id:",id
            print self.brics
        
    def add_new_bric(self, prev_id, which_id, bric_name):
        print "add_new_bric() prev_id:",prev_id, "which_id:",which_id,"bric_name:",bric_name
        if (bric_name in ['Loop', 'If']):
            self.bric_count += 2
            ids = self.new_ids(2)
            
            start_bric = Bric(ids[0], bric_name)
            end_bric = Bric(ids[1], "End")
            
            self.brics[ids[0]] = start_bric
            self.brics[ids[1]] = end_bric
            
            start_bric.next_id[0] = ids[1]
            start_bric.next_id[1] = ids[1]
            end_bric.prev_id[0] = ids[0]
            end_bric.prev_id[1] = ids[0]

            self.brics
            self.insert_bric(ids[0], prev_id, which_id)

            return ids[0]

        else:
            self.bric_count += 1
            new_id = self.new_id()
            new_bric = Bric(new_id, bric_name)
            self.brics[new_id] = new_bric
            
            self.insert_bric(new_id, prev_id, which_id)

            return new_id



    def insert_bric(self, new_id, prev_id, which_id):
        #print "Insert", new_id, prev_id, which_id
        if (new_id > 1):
            win_data.update_dirty(True)

        new_bric = self.brics[new_id]
        new_bric.prev_id[0] = prev_id
        
        # Handle starting a new stream
        if (prev_id <= 0):
            self.streams.append(new_id)
            new_bric.next_id[0] = -1
            
        else:
            if (new_bric.bric_name in ['If', 'Loop']):
                # Special processing for if and loop
                end_id = new_id + 1
                
                if (self.brics[prev_id].bric_name == "If"):
                    # previous bric is an if bric
                    next_id = self.brics[prev_id].next_id[which_id]
                    self.brics[prev_id].next_id[which_id] = new_id
                else:
                    next_id = self.brics[prev_id].next_id[0]
                    self.brics[prev_id].next_id[0] = new_id
                        
                if (next_id >= 0):
                    if (self.brics[next_id].bric_name == "End"):
                        # next bric is an end
                        self.brics[next_id].prev_id[which_id] = end_id
                    else:
                        self.brics[next_id].prev_id[0] = end_id
                        
                self.brics[end_id].next_id[0] = next_id
                        
            else:
                
                if (self.brics[prev_id].bric_name == "If"):
                    # previous bric is an if bric
                    next_id = self.brics[prev_id].next_id[which_id]
                    self.brics[prev_id].next_id[which_id] = new_id
                else:
                    next_id = self.brics[prev_id].next_id[0]
                    self.brics[prev_id].next_id[0] = new_id
                        
                if (next_id >= 0):
                    if (self.brics[next_id].bric_name == "End"):
                        # next bric is an end
                        self.brics[next_id].prev_id[which_id] = new_id
                    else:
                        self.brics[next_id].prev_id[0] = new_id
                        
                new_bric.next_id[0] = next_id

        #print "Inserted bric", new_id
        #self.dump()
            
    def new_id(self):
        self.start_id += 1
        
        return self.start_id
    
    def new_ids(self, count):
        result = []
        for i in range(count):
            result.append(self.new_id())

        return result


    def remove_bric(self, id, which_id, no_delete=False):
        #print "Remove",
        #self.brics[id].dump()

        prev_id = self.brics[id].prev_id[0]
        next_id = self.brics[id].next_id[0]

        # handle removing an event - it must already be the only icon in the stream
        if (prev_id == 0):
            # find which stream and remove it
            for i in range(len(self.streams)):
                if (self.streams[i] == id):
                    del self.streams[i]
                    break
            win_data.update_dirty(True)
            return True
            
        if (self.brics[id].bric_name in ('If', 'Loop')):
            # removing an EMPTY If or Loop
            # have to jump the end bit
            next_id = self.brics[next_id].next_id[0]
            
        if (prev_id >= 0):
            if (self.brics[prev_id].bric_name == 'If'):
                # previous bric is an if bric
                self.brics[prev_id].next_id[which_id] = next_id
            else:
                self.brics[prev_id].next_id[0] = next_id

        if (next_id >= 0):
            if (self.brics[next_id].bric_name == "End"):
                # next bric is an End bric
                self.brics[next_id].prev_id[which_id] = prev_id
            else:
                self.brics[next_id].prev_id[0] = prev_id

        if (not no_delete):
            if (self.brics[id].bric_name in ('If', 'Loop')):
                del self.brics[id]
                del self.brics[id+1]
                self.bric_count -= 2
            else:
                del self.brics[id]
                self.bric_count -= 1
            
        win_data.update_dirty(True)
        return True
                    
        
    def check_drag(self, bric_id, bric_name):
        """Check to see if this bric can be moved or deleted"""
        if (bric_name in ('Loop', 'If')):
            # must be empty to move it
            if ((self.brics[bric_id].next_id[0] == bric_id+1) and
                (self.brics[bric_id].next_id[1] == bric_id+1)):
                return True
            else:
                return False

        if (bric_name == 'Event' and self.brics[bric_id].next_id[0] != -1):
            # Can't delete or drag an 'Event' which has brics 
            return False
            
##        if (self.brics[bric_id].prev_id[0] == -1 and self.brics[id].next_id[0] != -1):
##            # Can't delete or drag an 'Event' which has brics 
##            return False
        
        return True

    def is_last_bric(self, id):
        return self.brics[id].next_id == -1
        
    def start_move(self, id, which_id):
        if (self.brics[id].bric_name in ["If", "Loop"]):
            self.move_id = [id, id+1]
        else:
            self.move_id = [id]
        self.move_which_id = which_id
            

    def end_move(self, prev_id, new_which_id):
        """If prev_id == -1, then want to delete it.
        Returns True if all ok, False if want to delete but can't.
        If False, it puts it back in the pre-move spot,
        if True then it adds it into the 
        pass"""

        bric_id = self.move_id[0]
        bric = self.brics[bric_id]
        old_data = bric.bric_data
        name = bric.bric_name
        old_which_id = self.move_which_id
            
        if (prev_id == -1):
            if (self.remove_bric(self.move_id[0], old_which_id)):
                win_data.remove_bric_refs(name, old_data)
            else:
                self.move_id = []
                return False
        else:
            if (not self.remove_bric(self.move_id[0], old_which_id, no_delete=True)):
                self.move_id = []
                return False
            else:
                self.insert_bric(self.move_id[0], prev_id, new_which_id)

        self.move_id = []
        win_data.update_dirty(True)
        #print "Moved bric", bric_id, "Prev:", prev_id
        #self.dump()
        
        return True

    def abort_move(self):
        self.move_id = []

    # ----------------------------- program data as a tree with layout adjustments -----------

    def zero_connections(self, connections):
        for k in self.brics:
            connections[k] = [(0,0), (0,0), (0,0), (0,0)]

    def get_tree_data(self, stream):
        id = self.get_stream_id(stream)
        if (id < 0):
            return None

        #print "id:", id
        tree_data = self.get_subtree(0, id, -1)
        #print "Tree data:", tree_data
        bfs_results = []
        self.bfs(tree_data, 0, bfs_results)
        #print "BFS", bfs_results
        

        # compute adjustments so that ifs don't go over each other
        #self.compute_adjustments(tree_data)
        results = []
        parents_dict = {}

        # Find the parents of a node and all of the paths from a node with max up and max down counts
        self.compute3(tree_data, results, parents_dict)
        
        #print "Check", tree_data, results, parents_dict
        #print "parents_dict", parents_dict

        # Now find the max and mins for each node
        o_results = {}
        for (bric, side, ssf) in results:
            if (bric not in o_results):
                o_results[bric] = [[],[], 0, 0]
            if (side == -1):
                # top
                o_results[bric][0].append(ssf)
            else:
                # bottom
                o_results[bric][1].append(ssf)

        #print "O_results:", o_results
                    
        # put max overlap values into o_results - values of 0 can overlap, any
        # higher definitely overlaps

        max_results = {}
        for bric in o_results:
            max_up = max(o_results[bric][0])
            min_up = min(o_results[bric][0])
            max_dn = max(o_results[bric][1])
            min_dn = min(o_results[bric][1])
            max_results[bric] = (max_up, min_up, max_dn, min_dn)
            
        
        # do adjustments
        #print "Results", results
        #print "max_results", max_results

        adjustments, min_min_y = self.try_adj(max_results, parents_dict, bfs_results)
        
        #adjustments = self.do_adjustments(o_results, parents_dict)

        #print parents_dict
        #print o_results
        #print adjustments
        
        return tree_data, adjustments, min_min_y

                
    def get_subtree(self, dir, id, end_id):
        #print "get_subtree(): dir:", dir, "id:", id, "end_id:", end_id
        sub_tree = [dir]
        while (id != end_id):

            # Don't have to worry about ifs or loops in this case because
            # they must be empty to be moved.
            if (id in self.move_id):
                id = self.brics[id].next_id[0]
                continue
            
            sub_tree.append(id)
            #print "Sub_tree:", sub_tree, "id:", id, "end_id:", end_id
            
            if (self.brics[id].bric_name == "If"):
                sub_tree.append(-2)
                # end bric is always one past if bric
                sub_tree.append(self.get_subtree(-1, self.brics[id].next_id[0], id+1))
                sub_tree.append(self.get_subtree(1, self.brics[id].next_id[1], id+1))
                sub_tree.append(id+1)
                id = id+1
            elif (self.brics[id].bric_name == "Loop"):
                sub_tree.append(-2)
                # end bric is always one past loop bric
                # BED - putting the return on the opposite side requires switch the following
                # 2 lines and fixing up other stuff.
                sub_tree.append(self.get_subtree(-1, self.brics[id].next_id[0], id+1))
                sub_tree.append([1, id+1])
                sub_tree.append(id+1)
                id = id+1

            id = self.brics[id].next_id[0]

        sub_tree.append(end_id)
        return sub_tree



    def walk(self, branch, sum_so_far, bric_id, side, results, parents, parents_dict):
        sum_so_far += branch[0]
        i = 1
        while (i < len(branch)):
            if (branch[i] == -2):

                # Record parent info
                new_bric_id = branch[i-1]
                if (new_bric_id not in parents_dict):
                    parents_dict[new_bric_id] = parents[:]
                parents.append((new_bric_id))
                top_parents = parents[:]
                bot_parents = parents[:]
                
                self.walk(branch[i+1], sum_so_far, bric_id, side, results, top_parents, parents_dict)
                self.walk(branch[i+2], sum_so_far, bric_id, side, results, bot_parents, parents_dict)
                i += 3
            else:
                i += 1

        # Add in all of the path sums from a bric_id
        if (side == 1):
            results.append((bric_id, side, sum_so_far))
        else:
            results.append((bric_id, side, sum_so_far))



    def compute3(self, branch, results, parents_dict):
        start = branch[0]
        
        i = 1
        while (i < len(branch)):
            if (branch[i] == -2):
                bric_id = branch[i-1]
                top_parents = [bric_id]
                bot_parents = [bric_id]
                self.walk(branch[i+1], 0, bric_id, -1, results, top_parents, parents_dict)
                self.walk(branch[i+2], 0, bric_id, 1, results, bot_parents, parents_dict)
                self.compute3(branch[i+1], results, parents_dict)
                self.compute3(branch[i+2], results, parents_dict)
                i += 3
            else:
                i += 1



    def bfs(self, branch, level, results):
        """Take a branch and return a list of lists of the nodes at each level (breadth first)"""
        i = 1
        while (i < len(branch)):
            if (branch[i] == -2):
                if (len(results) <= level):
                    results.append([])
                    
                results[level].append(branch[i-1])

                self.bfs(branch[i+1], level+1, results)
                self.bfs(branch[i+2], level+1, results)
                i += 3
            else:
                i += 1
                

    def try_adj(self, maxs, parents, bfs):
        """maxs - dict[bric] with (max_up, min_up, max_dn, min_dn)
           parents - dict[bric] with [parent ids]
           bfs - list of lists - [[nodes at level 0], [nodes at level 1], ...]
           """

        #print "try_adj:", maxs, parents, bfs
        
        adjust_up = {}
        adjust_dn = {}
        for level in bfs:
            for l in level:
                adjust_up[l] = 0
                adjust_dn[l] = 0


        
        # work from the most distant nodes back
        level_index = len(bfs)
        while (level_index > 0):
            work_nodes = bfs[level_index - 1]
            work_index = 0
            #print "Adj:", level_index, work_nodes
            while (work_index < len(work_nodes)):
                node = work_nodes[work_index]
                max_up, min_up, max_dn, min_dn = maxs[node]

                # make sure that the centre line isn't fouled
                # basically the min_dn and the max_up can't be closer then 1 apart
                #print "Checking", node, min_dn, max_up, min_dn-max_up
                diff = min_dn-max_up
                if (diff < 1):
                    adj_dn = 0
                    adj_up = 0
                    # we have a foul here - create adjustment factors
                    if (min_dn < 0 and max_up > 0):
                        # move them both (move bottom one more to clear top)
                        adj_dn = -1*min_dn+1
                        adj_up = -1*max_up
                        
                    elif (min_dn <= 0):
                        # mov the bottom one down
                        adj_dn = -1*diff + 1
                    else:
                        # mov the top one up
                        adj_up = diff - 1

                    #print "Adjust for node:", node, "up:", adj_up, "dn:", adj_dn
                    
                    if (adj_up < 0):
                        adjust_up[node] -= adj_up
                        if (node in parents):
                            for p in parents[node]:
                                adjust_dn[p] += (-1 * adj_up)
                            
                    if (adj_dn > 0):
                        adjust_dn[node] += adj_dn
                        if (node in parents):
                            for p in parents[node]:
                                # BED testing change
                                #adjust_up[p] -= (-1 * adj_up)
                                adjust_up[p] -= (-1 * adj_dn)
                            
                work_index += 1

            level_index -= 1


        adj_dict = {}
        for level in bfs:
            for l in level:
                adj_dict[l] = [-1*adjust_up[l], adjust_dn[l]]

        # need to find how far down to start
        
        # find the min min_up for all level 0 runs and add in any up adjustments
        min_min_up = -1
##        if (bfs):
##            for node in bfs[0]:
##                max_up, min_up, max_dn, min_dn = maxs[node]
##                #print "min_up at", node, min_up
##                # factor in any adjustments from myself and children
##                for cnode in parents:
##                    if (node in parents[cnode]):
##                        # cnode is a child of node
##                        #print "child", cnode
                        
##                min_up += adj_dict[node][0]
##                if (min_up < min_min_up):
##                    min_min_up = min_up

##        min_min_up += 1
        
        #print "Adj:", adj_dict, min_min_up
        return adj_dict, min_min_up
