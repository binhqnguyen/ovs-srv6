
function submit_te(){
	var from = document.getElementById("from").value;
	var to = document.getElementById("to").value;
	var controller = document.getElementById("controller").value;
	var url = controller+":8080/flow_mgmt/insert";
	var seg_types = document.getElementsByName("seg_type");
	var segs = document.getElementById("segs").value.split(",");
	var reversed_segs = document.getElementById("segs").value.split(",").reverse();
	var seg_type = get_segment_type_option(seg_types);	//node or adj
	//Facing corenetwork: port 1
	//Facing host: port 2
	//Segment routing encapsulation port: port 5
	var in_port = 1;
	var out_port = 2;
	var sr_encap_port = 5;
	var priority = 2;

	var src_dpid = get_dpid(from);
	var dst_dpid = get_dpid(to);
	window.alert("src dpid " + src_dpid + ", dst dpid " + dst_dpid + ", seg type " + seg_type + ", segs " + segs + ", reversed segs " + reversed_segs + ", controller " + controller);
	var graph = fetch_graph(controller+":8080/ospf_monitor/get_topology_netjson");
	//TODO: check if segments path is valid: eg, it starts with the "from" node and ends with the "to" node, etc.
	var src_match = get_match(to, graph);
	var dst_match = get_match(from, graph);
	if (src_match.length == 0 || dst_match.length == 0){
		window.alert("Can't find match for router " + to + " or " + from);
		return;
	}
	window.alert("Src match: " + src_match + "\nDst match: " + dst_match);
	var src_actions = get_actions(segs, seg_type, graph);
	var dst_actions = get_actions(reversed_segs, seg_type, graph);
	if (src_actions.length == 0 || dst_actions.length == 0){
		window.alert("Can't find actions for path " + segs);
		return;
	}
	//window.alert("Src actions: " + src_actions + "\nDst actions: " + dst_actions);
	var method = "POST";
	var src_post_data = construct_post_data(src_dpid, src_match, src_actions, in_port, out_port, priority);
	var dst_post_data = construct_post_data(dst_dpid, dst_match, dst_actions, in_port, out_port, priority);
	if (src_post_data.length == 0 || dst_post_data.length == 0){
		window.alert("Can't construct post data for path " + segs);
		return;
	}
	//window.alert("Src POST data: " + src_post_data.join("\n"));
	//window.alert("Dst POST data: " + dst_post_data.join("\n"));
	// You REALLY want shouldBeAsync = true.
	// Otherwise, it'll block ALL execution waiting for server response.
	var shouldBeAsync = true;

	var request = new XMLHttpRequest();

	request.onload = function () {
	   var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
	   var data = request.responseText; // Returned data, e.g., an HTML document.
	   console.log(data);
	}
	console.log(url);
	request.open(method, url, shouldBeAsync);

	//request.setRequestHeader("Content-Type", "application/json");

	// Actually sends the request to the server.
	for (var i = 0; i < src_post_data.length; i++){
		request.open(method, url, shouldBeAsync);
		request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
		request.send(src_post_data[i]);
		//window.alert("Sent src_post_data " + src_post_data[i]);
	}
	for (var i = 0; i < dst_post_data.length; i++){
		request.open(method, url, shouldBeAsync);
		request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
		request.send(dst_post_data[i]);
		//window.alert("Sent dst_post_data " + dst_post_data[i]);
	}
}

function get_segment_type_option(seg_types){
	var seg_type = "node";
	for (var i = 0; i < seg_types.length; i++){
		if (seg_types[i].checked){
			seg_type = seg_types[i].value;
			break;
		}
	}
	return seg_type;

}
function check_valid_parameters(controller, match){
	if (is_valid_ipv6(match) == false){
		window.alert("Match field " + match + "is an INVALID IPv6 address!");
		return false;
	}
	if (is_valid_controller(controller) == false){
		window.alert("Controller address " + controller + " is an INVALID address!");
		return false;
	}
}

function construct_actions(segments){
	tokens = segments.split(",");
	var ret = "";
	for (var i = 0; i < tokens.length; i++){
		if (is_valid_ipv6(tokens[i]) == true){
			ret += "ipv6_dst=" + tokens[i] + ","		
		} else {
			window.alert("Segment " + tokens[i] +"is an INVALID IPv6 address!");
			return "";
		}
	}
	return ret.substring(0,ret.length-1);
}

function construct_post_data(dpid, match, actions, in_port, out_port, priority){
	var ret = [];
	if (dpid == "" || match == "" || actions == "" || out_port == "") {
		return ret;
	}
	var matches = match.split(",");
	for (var i = 0; i < matches.length; i++){
		var p = "";
		p += "dpid="+dpid;
		p += "&priority="+priority;
		p += "&match="+matches[i]+",eth_type=0x86DD,in_port="+in_port;
		p += "&actions="+actions+",output="+out_port;
		ret.push(p);
	}
	return ret;
}

//TODO
function is_valid_controller(controller){
	if (controller.length > 0){
		return true;
	} 
	return false
}

function is_valid_ipv6(ipv6){
 	return /^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$|^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/.test(ipv6);
}

//not used
function reverse_str(segs){
	var tokens = segs.split("");
	var reversed_tokens = tokens.reverse();
	return reversed_tokens.join("");
}

function get_dpid(node){
	return node;
}

//Generate the SDN 'match' field from the destination node.
//By default the 'match' field matches all prefixes that the dst node has.
function get_match(node, graph){
	nodes = graph.nodes;
	var ret = "";
	var n = null;
	var matches = [];
	for (var i = 0; i < nodes.length; i++){
		if (nodes[i].id == node){
			n = nodes[i];
			break;
		}
	}
	if (n==null){
		return ret;
	}
	
	for (var i = 0; i < n.properties.Prefixes.length; i++){
		if (is_valid_ipv6(n.properties.Prefixes[i]) == true){
			var prefix_length = get_ipv6_prefix_length(n.properties.Prefixes[i]);
			if (prefix_length > 0)
				matches.push("ipv6_dst="+n.properties.Prefixes[i]+"/"+prefix_length);
		}
	}
	ret = matches.join(",");
	return ret;
	
}

//Generate the SDN 'actions' field from a list of nodes describing the path.
function get_actions(segs, seg_type, graph){
	ret = "";
	ipv6s = [];
	if (segs.length == 0)
		return ret;

	if (seg_type == "node"){
		for (var i = 0; i < segs.length; i++) {
			var node = get_node_by_id(graph, segs[i]);
			if (node != null)
				ipv6s.push("ipv6_dst=" + node.properties['Node segment']);
		}
	}
	if (seg_type == "adj"){
		var node = get_node_by_id(graph, segs[0]);
		if (node != null)
			ipv6s.push("ipv6_dst="+node.properties['Node segment']); //First segment is *always* first node's node segment.
		for (var i = 0; i < segs.length-1; i++) {
			var edge_src = segs[i];
			var edge_dst = segs[i+1];
			var edge = get_edge_from_src_dst(edge_src, edge_dst, graph);
			if (edge != null)
				ipv6s.push("ipv6_dst=" + edge.properties['Dst Interface Address']);
		}
	}
	ret = ipv6s.join(",");
	return ret;
} 

function get_node_by_id(graph, id){
	nodes = graph.nodes;
	for (var i = 0; i < nodes.length; i++) {
		if (nodes[i].id == id)
			return nodes[i];
	}
	return null;
}
function get_edge_from_src_dst(edge_src, edge_dst, graph){
	edges = graph.links;
	for (var i = 0; i < edges.length; i++) {
		if (edge_src==edges[i].source && edge_dst==edges[i].target){
			return edges[i];
		}
	}
	return null;
}

function get_ipv6_prefix_length(ipv6_prefix){
	ipv6_blocks = ipv6_prefix.split(":");
	var count = 0;
	for (var i = 0; i < ipv6_blocks.length; i++){
		if (ipv6_blocks[i] != ""){
			count += 1
		}
	}
	if (ipv6_blocks[ipv6_blocks.length-1] == "1")
		count -= 1;
	return count*16;
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
