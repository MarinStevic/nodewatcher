(function ($) {
    $(window).on('map:init', function (e) {
        var detail = e.originalEvent ? e.originalEvent.detail : e.detail;
        var map = detail.map;
        
        //Fulscreen map button
        map.addControl(new L.Control.Fullscreen());
        
        //Adding the sidebar to the map
        //Adds the HTML div with id="sidebar" from map.html to the map
        var sidebar = L.control.sidebar({ container: 'sidebar', closeButton: false, position: 'right'}).addTo(map);
        
        // TODO: Some kind of loading indicator
        
        //Time selection for the recently offline nodes
        //Currently it is 24h since now-1h
        var time_start = new Date();
        var time_stop = new Date();
        time_start.setHours(time_start.getHours() - 25);
        time_stop.setHours(time_stop.getHours() - 1);
        
        //APIv2 request for the recently offline nodes
        $.ajax({
            'url': 'https://nodes.otvorenamreza.org/api/v2/node/?format=json&limit=1&filters=monitoring:core.general__last_seen__gt="' + time_start.toISOString() + '",monitoring:core.general__last_seen__lt="' + time_stop.toISOString() + '"',
        }).done(function(data) {
            for(var i = 1; i < data.count; i++) {
                $.ajax({
                    'url': 'https://nodes.otvorenamreza.org/api/v2/node/?format=json&limit=1&fields=monitoring:core.general__last_seen&fields=config:core.location&fields=config:core.general&fields=config:core.type&filters=monitoring:core.general__last_seen__gt="' + time_start.toISOString() + '",monitoring:core.general__last_seen__lt="' + time_stop.toISOString() + '"&offset=' + (i - 1),
                }).done(function(data) {
                    var node = {
                        'data': {
                            'n': data.results[0]["config"]["core.general"]["name"],                         //node name
                            'i': data.results[0]["@id"],                                                    //node id
                            't': data.results[0]["config"]["core.type"]["type"],                            //node type
                            'l': (data.results[0]["config"]["core.location"]["geolocation"] ? data.results[0]["config"]["core.location"]["geolocation"]["coordinates"] : null),  //node coordinates
                            'api': "v2",                                                                    //api version which was used to get the data
                        },
                    }
                    sidebarTableAddNode(node,"recently-offline-table");
                });
            }
        });
		
		
		var nodes = [];
		var edges = [];
		var nodeIndex = {};
		
		$.ajax({
            'url': 'https://nodes.otvorenamreza.org/api/v2/node/?format=json&limit=1&filters=monitoring:core.general',
        }).done(function(data) {

            for(var i = 0; i < data.count; i++) {
                $.ajax({
                    'url': 'https://nodes.otvorenamreza.org/api/v2/node/?format=json&limit=1&fields=monitoring:core.general__last_seen&fields=config:core.location&fields=config:core.general&fields=config:core.type&offset=' + i,
                }).done(function(data) {
                    var node = {
                        'data': {
                            'n': data.results[0]["config"]["core.general"]["name"],                         //node name
                            'i': data.results[0]["@id"],                                                    //node id
                            't': data.results[0]["config"]["core.type"]["type"],                            //node type
                            'l': (data.results[0]["config"]["core.location"]["geolocation"] ? data.results[0]["config"]["core.location"]["geolocation"]["coordinates"] : null),  //node coordinates
                        },
                    }
					
					//storing each node data
					if (node.data.l != null) {
						nodes.push(node);
					}
                });
            }
        });
		$.nodewatcher.map.extend(map, nodes, edges);
    });
})(jQuery);
