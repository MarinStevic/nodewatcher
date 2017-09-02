window.DrawCidr = class DrawCidr {
    constructor(svg, size, subnet) {
        this.svg = svg;

        svg.call(d3.zoom().on('zoom', function() {
            svg.attr('transform', d3.event.transform)
        })).append('g');

        this.n_ips = Math.pow(2, 32 - parseInt(subnet.split("/")[1]));
        this.size = Math.sqrt(this.n_ips);
        this.displaySize = this.closestPower(size);

        $('#ipspace').css('transform', 'scale(' + this.displaySize / this.size + ')');
        $('#wraper').width($('#ipspace').width() + 'px');
        $('#wraper').height($('#ipspace').height() + 'px');

        this.svg.style('width', this.size + 'px').style('height', this.size + 'px');

        this.subnet = String(subnet);
        this.ips_side = Math.sqrt(this.n_ips);
        this.ips_pixel = this.ips_side / this.size;
        this.offset = this.ip2num(this.subnet.split("/")[0]);
        this.draw(subnet);
        this.data = new Array();
    }

    closestPower(number) {
        return 2 ** Math.floor(Math.log2(number));
    }

    ip2num(ip) {
        var d = ip.split('.');
        return ((((((+d[0]) * 256) + (+d[1])) * 256) + (+d[2])) * 256) + (+d[3]);
    }

    num2ip(num) {
        var d = num % 256;
        for (var i = 3; i > 0; i--) {
            num = Math.floor(num / 256);
            d = num % 256 + '.' + d;
        }
        return d;
    }

    subnetSize(subnet) {
        var subnet_str = String(subnet);
        var times = 32 - parseInt(subnet_str.split("/")[1]);
        var subnet_ips = Math.pow(2, times);
        var shape_size = Math.sqrt(subnet_ips) / this.ips_pixel;
        return shape_size;
    }

    subnetXY(subnet) {
        var subnet_str = String(subnet);
        var start_num = this.ip2num(subnet_str.split("/")[0]) - this.offset;
        var start_xy = d2xy(start_num);

        var x = start_xy.x / this.ips_pixel;
        var y = start_xy.y / this.ips_pixel;
        return [x, y];
    }

    HSVtoRGB(h, s, v) {
        var r, g, b, i, f, p, q, t;
        if (arguments.length === 1) {
            s = h.s, v = h.v, h = h.h;
        }
        i = Math.floor(h * 6);
        f = h * 6 - i;
        p = v * (1 - s);
        q = v * (1 - f * s);
        t = v * (1 - (1 - f) * s);
        switch (i % 6) {
            case 0:
                r = v, g = t, b = p;
                break;
            case 1:
                r = q, g = v, b = p;
                break;
            case 2:
                r = p, g = v, b = t;
                break;
            case 3:
                r = p, g = q, b = v;
                break;
            case 4:
                r = t, g = p, b = v;
                break;
            case 5:
                r = v, g = p, b = q;
                break;
        }

        return {
            r: Math.round(r * 255),
            g: Math.round(g * 255),
            b: Math.round(b * 255)
        };
    }

    componentToHex(c) {
        var hex = c.toString(16);
        return hex.length == 1 ? '0' + hex : hex;
    }

    rgbToHex(r, g, b) {
        return '#' + this.componentToHex(r) + this.componentToHex(g) + this.componentToHex(b);
    }

    UpdateQueryString(key, value, url) {
        if (!url) url = window.location.href;
        var re = new RegExp("([?&])" + key + "=.*?(&|#|$)(.*)", "gi"),
            hash;

        if (re.test(url)) {
            if (typeof value !== 'undefined' && value !== null)
                return url.replace(re, '$1' + key + "=" + value + '$2$3');
            else {
                hash = url.split('#');
                url = hash[0].replace(re, '$1$3').replace(/(&|\?)$/, '');
                if (typeof hash[1] !== 'undefined' && hash[1] !== null)
                    url += '#' + hash[1];
                return url;
            }
        }
        else {
            if (typeof value !== 'undefined' && value !== null) {
                var separator = url.indexOf('?') !== -1 ? '&' : '?';
                hash = url.split('#');
                url = hash[0] + separator + key + '=' + value;
                if (typeof hash[1] !== 'undefined' && hash[1] !== null)
                    url += '#' + hash[1];
                return url;
            }
            else
                return url;
        }
    }

    getUrlParameter(sParam) {
        var sPageURL = decodeURIComponent(window.location.search.substring(1)),
            sURLVariables = sPageURL.split('&'),
            sParameterName,
            i;

        for (i = 0; i < sURLVariables.length; i++) {
            sParameterName = sURLVariables[i].split('=');

            if (sParameterName[0] === sParam) {
                return sParameterName[1] === undefined ? true : sParameterName[1];
            }
        }
    };

    draw(subnet, description) {
        var times = 32 - parseInt(subnet.split('/')[1]);
        var subnet_ips = Math.pow(2, times);
        var shape_size = Math.sqrt(subnet_ips) / this.ips_pixel;

        var start_num = this.ip2num(subnet.split('/')[0]) - this.offset;

        var start_xy = d2xy(start_num);

        var x = start_xy.x / this.ips_pixel;
        var y = start_xy.y / this.ips_pixel;

        this.svg.append('rect').attr('x', x).attr('y', y).attr('height', shape_size).attr('width', shape_size).style('fill', this.rgbToHex(times * 8, times * 8, times * 8)).style('opacity', 0.3).attr('id', subnet).attr('n', subnet_ips).attr('d', description);
    }

    load() {
        var self = this;
        for (var i = 0; i < 33; i++) {
            $.getJSON('/api/v2/pool/ip/?format=json&prefix_length=' + i, function(data) {
                for (var j = 0; j < data.results.length; j++) {
                    self.draw(data.results[j].network + "/" + data.results[j].prefix_length, data.results[j].description);
                }
                self.data.push(data);
                if (self.data.length == 33) {
                    jQuery('rect').tipsy({
                        gravity: 'w',
                        html: true,
                        title: function() {
                            return this.id + '<br>Number of hosts: ' + $(this).attr('n') + '<br>Network name: ' + $(this).attr('d');
                        }
                    });
                    self.setTopNodes(self.calcTopNodes(self.data));
                }
            });
        }
    }

    calcTopNodes(data) {
        var res = new Array();
        for (var i = 0; i < data.length; i++) {
            for (var j = 0; j < data[i].results.length; j++) {
                var node = data[i].results[j];
                if (node['@id'] == node.top_level['@id']) {
                    res.push(node);
                }
            }
        }
        return res;
    }

    setTopNodes(data) {
        var self = this;
        $('#topnodes').html('<li id="cidr" cidr="10.0.0.0/8"><a>10.0.0.0/8 (Zoom out)</a></li>');
        data.forEach(function(node) {
            $('#topnodes').append('<li id="cidr" cidr="' + node.network + '/' + node.prefix_length + '"><a>' + node.network + '/' + node.prefix_length + ' (' + node.description + ')' + '</a></li>');
        });
        var scale= self.getUrlParameter('scale');
        var start = self.getUrlParameter('start').split(',');
        if(scale != undefined && start != undefined){
            self.svg.selectAll('rect').attr('transform', 'translate(' + start[0] * -1 * scale + ',' + start[1] * -1 * scale + ') scale(' + scale + ')');
        }
        $('#topnodes').on('click', '#cidr', function(event) {
            var scale = self.size / self.subnetSize($(event.target).parent().attr('cidr'));
            var start = self.subnetXY($(event.target).parent().attr('cidr'));
            history.replaceState({}, document.title, self.UpdateQueryString('scale', scale, window.url));
            history.replaceState({}, document.title, self.UpdateQueryString('start', start, window.url));
            self.svg.selectAll('rect').attr('transform', 'translate(' + start[0] * -1 * scale + ',' + start[1] * -1 * scale + ') scale(' + scale + ')');
        });
    }
}