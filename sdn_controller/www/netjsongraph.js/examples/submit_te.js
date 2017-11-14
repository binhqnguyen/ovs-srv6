
function submit_te(){
	var from = document.getElementById("from").value;
	var to = document.getElementById("to").value;
	var controller = document.getElementById("controller").value;
	var seg_types = document.getElementsByName("seg_type");
	var segs = document.getElementById("segs").value;
	var reversed_segs = reverse_str(segs);
	var seg_type;	//node or adj
	//Facing corenetwork: port 1
	//Facing host: port 2
	var in_port = 1;
	var out_port = 2;

	for (var i = 0; i < seg_types.length; i++){
		if (seg_types[i].checked){
			seg_type = seg_types[i].value;
			break;
		}
	}
	var src_dpid = get_dpid(from);
	var dst_dpid = get_dpid(to);
	window.alert("src dpid " + src_dpid + ", dst dpid " + dst_dpid + ", seg type " + seg_type + ", segs " + segs + ", reversed segs " + reversed_segs + ", controller " + controller);
	var graph = fetch_graph(controller+":8080/ospf_monitor/get_topology_netjson");
	var src_match = get_match(to, graph);
	var dst_match = get_match(from, graph);
	if (src_match.length == 0 || dst_match.length == 0){
		window.alert("Can't find match for router " + to + " or " + from);
		return;
	}
	window.alert("Src match: " + src_match + ", dst match: " + dst_match);
	var src_actions = get_actions(segs, seg_type, graph);
	var dst_actions = get_actions(reversed_segs, seg_type, graph);

	var method = "POST";
	/*
	var post_data = "dpid="+dpid+"&match=ipv6_dst="+match+"&actions="+actions+",output="+out_port

	// You REALLY want shouldBeAsync = true.
	// Otherwise, it'll block ALL execution waiting for server response.
	var shouldBeAsync = true;

	var request = new XMLHttpRequest();

	request.onload = function () {
	   var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
	   var data = request.responseText; // Returned data, e.g., an HTML document.
	   console.log(data);
	}
	var url = controller+":8080/flow_mgmt/insert";
	console.log(url);
	request.open(method, url, shouldBeAsync);

	//request.setRequestHeader("Content-Type", "application/json");
	request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

	// Actually sends the request to the server.
	request.send(post_data);
	*/
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

function reverse_str(segs){
	var tokens = segs.split(",");
	var reversed_tokens = tokens.reverse();
	return reversed_tokens.join(",");
}

function get_dpid(node){
	return node;
}

function get_match(node, graph){
	nodes = graph.nodes;
	var n = null;
	var matches = [];
	for (var i = 0; i < nodes.length; i++){
		if (nodes[i].id == node){
			n = nodes[i];
			break;
		}
	}
	if (n==null){
		return [];
	}
	
	for (var i = 0; i < n.properties.Prefixes.length; i++){
		if (is_valid_ipv6(n.properties.Prefixes[i]) == true){
			var prefix_length = get_ipv6_prefix_length(n.properties.Prefixes[i]);
			if (prefix_length > 0)
				matches.push("ipv6_dst="+n.properties.Prefixes[i]+"/"+prefix_length);
		}
	}
	return matches;
	
}

//TODO
function get_actions(segs, seg_type, graph){
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
