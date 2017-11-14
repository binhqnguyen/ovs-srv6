
function submit_te(){
	var match = document.getElementById("match").value;
	var actions = document.getElementById("actions").value;
	var controller = document.getElementById("controller").value;
	//TODO: how to get dpid of switches?
	var dpid = "17779081360";
	//Facing corenetwork: port 1
	//Facing host: port 2
	var in_port = 1;
	var out_port = 2;
	if (check_valid_parameters(controller, match, actions) == false){
		return;
	}
	actions = construct_actions(actions);
	if (actions == ""){
		return;
	}
	console.log(match);
	console.log(controller);
	console.log(actions);

	var method = "POST";
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
	tokens = segments.split(",")
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

