//MODIFY this before run
var url = "http://node1.srv6.phantomnet.emulab.net:8080/ospf_monitor/get_topology_netjson";
var graph = {};
/*
while (1){
	graph = fetch_graph(url);
	if (graph != null){
		console.log(graph);
	}
	console.log("draw_graph");
	draw_graph(graph);
	sleep(2000);
}
*/

graph = fetch_graph(url);
if (graph != null){
	console.log(graph);
}
console.log("draw_graph");
draw_graph(graph);
//window.location.reload();

function draw_graph(graph){
	var nodes = [];
	for (var key in graph){
		if (graph.hasOwnProperty(key)) {	
			nodes.push({
					id: key,
					label: key,
					shape: 'circle',
					color: '#6E6EFD'
					});
		}
	}
	// create an array with nodes
	var nodes_vis = new vis.DataSet(nodes);

	// create edges
	var visited_nodes = [];
	var edges = [];
	if (nodes.length > 0){
		get_edges(graph[nodes[0].id], visited_nodes, edges, graph, nodes[0].id);
	}
	var edges_vis = new vis.DataSet(edges);

	// create a network
	var container = document.getElementById('mynetwork');
	var data = {
	    nodes: nodes_vis,
	    edges: edges_vis
	};
	var options = {
	    nodes: {
	      shape: 'circle'
	    }
	};
	var network = new vis.Network(container, data, options);
}

//DFS, get all edges
function get_edges(root, visited_nodes, edges, graph, ID){
	//console.log("current node: ", ID);
	//console.log("visited nodes: ", visited_nodes);
	num_active_nbs = get_size(root.ActiveNbs);
	if (num_active_nbs == 1 || jQuery.inArray(ID, visited_nodes) != -1){
		//console.log("returned: ", ID);
		return;
	}

	visited_nodes.push(ID);
	for (var nb in root.ActiveNbs){
		if (root.ActiveNbs.hasOwnProperty(nb) && is_edge_existed(ID, nb, edges) == false){
			//console.log("new edge:", ID, nb);
			edges.push({
				from: ID,
				to: nb,
				color: 'rgba(30,30,30,0.2)',
				highlight: 'blue'		
				});
		}
		get_edges(graph[nb], visited_nodes, edges, graph, nb);
	}
}

function get_size(obj){
	var size = 0;
	for (var key in obj){
		if (obj.hasOwnProperty(key)) size++;
	}
	return size;
}

function is_edge_existed(src, dst, edges){
	for (var i = 0; i < edges.length; i+=1){
		if ((src==edges[i].from && dst==edges[i].to) || (src==edges[i].to && dst==edges[i].from)){
			return true;
		}
	}
	return false;
}

function fetch_graph(url){
	var graph = (function() {
			var json = null;
			$.ajax({
				'async': false,
				'global': false,
				'url': url,
				'dataType': "json",
				'success': function (data) {
					json = data;
				}
			});
			return json;
	})();
	return graph;
}

async function check_update(url, graph){
	var last_graph = graph;
	while (JSON.stringify(graph) === JSON.stringify(last_graph)) {
		console.log("fetch_graph");
		last_graph = graph;
		graph = fetch_graph(url);
		//console.log("graph: ", graph);
		sleep(2000);
	}	
	return graph;
}

function sleep(ms) {
  var start = new Date().getTime(), expire = start + ms;
  while (new Date().getTime() < expire) { }
  return;
}
