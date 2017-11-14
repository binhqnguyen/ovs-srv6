var url = "http://node1.srv6.phantomnet.emulab.net:8080/ospf_monitor/get_topology_netjson";
var graph;
d3.netJsonGraph(url);
graph = fetch_graph(url);
console.log("Displayed graph: " + graph);



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
