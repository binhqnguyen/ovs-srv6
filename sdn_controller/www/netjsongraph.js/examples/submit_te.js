//var querystring = require('querystring');
//var http = require('http');
//var request = require(request);

function submit_te(){
	var match = document.getElementById("match").value;
	var actions = document.getElementById("actions").value;
	var controller = document.getElementById("controller").value;
	var post_request = "";
	var dpid = "17779081360";
	//var form = document.createElement("form");
    	//form.setAttribute("method", "post");
    	//form.setAttribute("action", controller+"/flow_mgmt/insert");

	console.log(match);
	console.log(actions);
	console.log(controller);

	//post_request = "?dpid="+dpid+"&match=ipv6_dst="+match+",eth_type=0x86DD&actions="+ "ipv6_dst=2001::" +",output=1";
	//document.getElementById("te_form").action = controller+"/flow_mgmt/insert"+post_request;

	var method = "POST";
	var postData = JSON.stringify({
		"dpid": "17779081360",
		"match": "ipv6_dst=2001\:\:",
		"actions": "ipv6_dst=2001"
	});

	// You REALLY want shouldBeAsync = true.
	// Otherwise, it'll block ALL execution waiting for server response.
	var shouldBeAsync = true;

	var request = new XMLHttpRequest();

	// Before we send anything, we first have to say what we will do when the
	// server responds. This seems backwards (say how we'll respond before we send
	// the request? huh?), but that's how Javascript works.
	// This function attached to the XMLHttpRequest "onload" property specifies how
	// the HTTP response will be handled. 
	//request.onload = function () {

	   // Because of javascript's fabulous closure concept, the XMLHttpRequest "request"
	   // object declared above is available in this function even though this function
	   // executes long after the request is sent and long after this function is
	   // instantiated. This fact is CRUCIAL to the workings of XHR in ordinary
	   // applications.

	   // You can get all kinds of information about the HTTP response.
	  // var status = request.status; // HTTP response status, e.g., 200 for "200 OK"
	  // var data = request.responseText; // Returned data, e.g., an HTML document.
	  // console.log(data);
	//}
	var url = controller+":8080/flow_mgmt/insert";
	console.log(url);
	request.open(method, url, shouldBeAsync);

	request.setRequestHeader("Content-Type", "application/json");
	//request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8");
	// Or... request.setRequestHeader("Content-Type", "text/plain;charset=UTF-8");
	// Or... whatever

	// Actually sends the request to the server.
	request.send(postData);

	request.onreadystatechange = processRequest;
 
	function processRequest(e) {
 		console.log(e);
	}
}
