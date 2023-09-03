import os
import sys
import zlib



class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

        self.parents_top = set()
        self.children_top = set()
    
    permanent_mark = False
    temporary_mark = False

def get_directories():
    while os.getcwd() != "/":
        dirs = os.listdir()
        for dir in dirs:
            if dir == ".git":
                return True
        os.chdir("..")
    return False

def get_branches(path=""):
        refs_append = []
        old_ref = ""
        refs = os.listdir(os.path.join("./.git/refs/heads", path))
        for ref in refs: #check each entry
            if os.path.isdir(os.path.join("./.git/refs/heads/", ref)): #if it's a directory
                old_ref = ref
                refs_append = get_branches(path=ref) #recursively search it
        for refs_app in refs_append:
            refs.append(old_ref+"/"+refs_app)
        
        #remove directories
        for ref in refs:
            if os.path.isdir(os.path.join("./.git/refs/heads/", ref)):
                refs.remove(ref)
        return refs

def depth_first_search(some_node, commit_graph, root_commits):
    stack = [some_node] #some node is our head node
    #path = commit_graph

    if any(i.commit_hash == some_node.commit_hash for i in commit_graph) == True: #head node already traversed, so don't do it again
        return
    
    while stack:
        inspect_node = stack.pop()
        if inspect_node in commit_graph:
            continue
        commit_graph.append(inspect_node)

        for parent_hash in inspect_node.parents: #FOR EACH OF INSPECT_NODE'S PARENT NODES, APPEND SUCH PARENT NODE
            parent_hash_address = parent_hash[:2] + '/' + parent_hash[2:]
            try:
                g = open("./.git/objects/" + parent_hash_address, 'rb') #if this fails make it parentless, add to root_commit, return
            except: #if there's an error, we've most likely reached a root commit
                #create a CommitNode object for the current node's parent
                root_node = CommitNode(parent_hash)
                root_node.children.add(inspect_node.commit_hash) #add child (current commit) to its parent commit

                if any(i.commit_hash == root_node.commit_hash for i in commit_graph) == False: #ensure this commit is unique
                    stack.append(root_node) #add root commit
                    root_commits.append(root_node) #add the root commit to root_commits too

            else:
                g_contents = (zlib.decompress(g.read())).decode('utf-8') #contents is the commit's contents
        
                #create a CommitNode object for the current node's parent
                regular_node = CommitNode(parent_hash)
                regular_node.children.add(inspect_node.commit_hash) #add child (current commit) to its parent commit

                #get the head's parent(s)
                g_contents_parsed = g_contents.splitlines()
                for line in g_contents_parsed:
                    if "parent" in line:
                        regular_node.parents.add(line.split("parent ",1)[1])

                if any(i.commit_hash == regular_node.commit_hash for i in commit_graph) == False: #ensure this commit is unique
                    stack.append(regular_node) #prepend CommitNode named some_node to commit_graph
                    if not regular_node.parents: #if no parents, then it's a root commit
                        root_commits.append(regular_node)
                else: #otherwise, check if commit exists, and if so, update parents/children
                    for x in commit_graph:
                        if x.commit_hash == regular_node.commit_hash:
                            x.children.add(inspect_node.commit_hash)

def kahns_algorithm(commit_graph, root_commits, sorted_elements):
    #L = sorted_elements
    #S = root_commits

    while root_commits:
        vertex = root_commits.pop() #remove a vertex n from S
        if any(i.commit_hash == vertex.commit_hash for i in sorted_elements) == False: #ensure vertex is unique
            sorted_elements.append(vertex) #append n to L
        for parent_hash_m in vertex.parents.copy(): #for every parent m with edge e shared with n
            #retrieve m and remove edge e
            for m in commit_graph:
                if m.commit_hash == parent_hash_m: #if m (vertex's PARENT) is found
                    #REMOVE RELATIONSHIPS
                    m.children.remove(vertex.commit_hash) #remove m's parental relationship to n
                    m.children_top.add(vertex.commit_hash)
                    vertex.parents.remove(parent_hash_m) #remove n's child relationship to m
                    vertex.parents_top.add(parent_hash_m)

                    if not m.parents: #if m has no incoming edges 
                        root_commits.append(m)

        for child_hash_m in vertex.children.copy(): #for every child m with edge e shared with n
            #retrieve m and remove edge e
            for m in commit_graph:
                if m.commit_hash == child_hash_m: #if m (vertex's CHILD) is found
                    # REMOVE RELATIONSHIPS
                    try:
                        m.parents.remove(vertex.commit_hash) #remove m's child relationship to n
                        m.parents_top.add(vertex.commit_hash)
                    except KeyError:
                        pass
                    vertex.children.remove(child_hash_m) #remove n's parent relationship to m
                    vertex.children_top.add(child_hash_m)

                    if not m.parents: #if m has no incoming edges
                        root_commits.append(m)


def topo_print(sorted_elements,head_names):
    # print out in topological order
    prev = None
    #go through n-1 sorted_elements
    while sorted_elements:
        i = sorted_elements.pop()
        #print out the hashes, and print out their names if they exist
        try:
            try:
                print(prev.commit_hash + head_names[prev.commit_hash])
            except:
                print(prev.commit_hash)
        except:
            if prev != None: #prev will always end up here the 1st run through; stop it from printing
                try:
                    print(i.commit_hash + head_names[i.commit_hash])
                except:
                    print(i.commit_hash)

        #check for sticky ends
        try:
            if i.commit_hash not in prev.parents_top: #if sticky end required
                parent_list = ""
                for parent in prev.parents_top:
                    if parent_list == "": #account for whitespace between each parent
                        parent_list = parent
                    else:
                        parent_list += " " + parent
                print(parent_list + "=\n")

                children_list = ""
                for children in i.children_top:
                    if children_list == "": #account for whitespace between each child
                        children_list = children
                    else:
                        children_list += " " + children
                print("="+children_list)

              
        except:
            pass
        prev = i

    #print out the last element
    if prev != None:
        try:
            print(prev.commit_hash + head_names[prev.commit_hash])
        except:
            print(prev.commit_hash)



def topo_order_commits():
    commit_graph = [] #graph of all commits, containing CommitNode objects
    root_commits = [] #all the leaf nodes across all the branches (those with no parents, i.e. the oldest ancestors)
    sorted_elements = [] #the output of Kahn's algorithm
    head_names = {}
    if get_directories == False:
        raise ValueError("Not inside a Git repository")
        
    dictionary_of_heads = get_branches()

    #for each head in dictionary_of_heads, do depth-first search
    for entries in dictionary_of_heads:
        with open("./.git/refs/heads/" + entries,"r") as file:
            head = file.read().rstrip()

        #create a CommitNode object for the head
        head_node = CommitNode(head)

        #ADDING TO THE HEAD_NAMES DICTIONARY
        if head_node.commit_hash not in head_names:
            head_names[head_node.commit_hash]= " " + entries
        else:
            head_names[head_node.commit_hash]+= " " + entries

        skip = False
        for q in root_commits:
            if head in q.commit_hash:
                skip = True #if we're about to open a root commit, then continue (so we don't)
        if skip == True: 
            continue

        head_address = head[:2] + '/' + head[2:]
        f = open("./.git/objects/" + head_address, 'rb')
        contents = (zlib.decompress(f.read())).decode('utf-8') #contents is the commit's contents

        #get the head's parent(s)
        contents_parsed = contents.splitlines()
        for line in contents_parsed:
            if "parent" in line:
                head_node.parents.add(line.split("parent ",1)[1])

        # depth-first search for nodes 
        depth_first_search(head_node, commit_graph, root_commits)

    #Kahn's algorithm
    kahns_algorithm(commit_graph, root_commits, sorted_elements)

    commit_graph.reverse()

    # #final step: topologically print it
    topo_print(sorted_elements,head_names)

    

if __name__ == '__main__':
    topo_order_commits()
