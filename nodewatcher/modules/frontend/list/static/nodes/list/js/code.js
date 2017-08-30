(function ($) {
    function renderTimeAgo(data, type, row, meta) {
        if (type !== 'display')
            return data;

        var t = moment(data);
        if (!t.isValid())
            return "<em>never</em>";

        // TODO: custom date formats, refresing?
        var output = $('<span/>').attr('title', t.format($.nodewatcher.theme.dateFormat)).addClass('time').append(t.fromNow());

        return output.wrap('<span/>').parent().html();

    }

    function renderRoutingTopology(data, type, row, meta) {
        var output = $('<span/>');

        // Sort by protocol name to get a consistent order everywhere.
        data = _.sortBy(data, 'protocol');

        _.each(data, function (info, index) {
            // TODO: Structure this better. Use <dl>, <dt> and <dd>.
            var obj = $('<span />');
            obj.attr('title', info.protocol);
            obj.append(info.link_count);

            if (index < data.length - 1)
                obj.append('&nbsp;·&nbsp;');

            output.append(obj);
        });

        return output.html();
    }

    function renderRouterId(data, type, row, meta) {
        data = _.sortBy(data);
        return data.join('<br/>');
    }

    $(document).ready(function () {
        $('.node-list').each(function (i, table) {
            $.nodewatcher.api.newDataTable(table, $(table).data('source'), {
                registryRoots: {
                    '*': {
                        fields: {
                            'config': [
                                ['core.general', 'name'],
                                ['core.type', 'type'],
                                ['core.routerid', 'router_id'],
                                ['core.project', 'project__name']
                            ],
                            'monitoring': [
                                'core.general',
                                'core.status',
                                'network.routing.topology'
                            ],
                        },
                        searchFilters: 'config:core.general__name__icontains="%s"',
                    },
                },
                columns: [
                    {data: 'config.core__type.type', registry: true, width: 0, render: $.nodewatcher.renderNodeType(table)},
                    {data: 'config.core__general.name', registry: true, render: $.nodewatcher.api.renderNodeName(table)},
                    {data: 'config.core__routerid[].router_id', registry: true, render: renderRouterId},
                    {data: 'monitoring.core__general.last_seen', registry: true, render: renderTimeAgo},
                    {data: 'monitoring.core__status.network', registry: true, render: $.nodewatcher.renderStatus(table, 'Network'), class: 'center', width: '20px'},
                    {data: 'monitoring.core__status.monitored', registry: true, render: $.nodewatcher.renderStatus(table, 'Monitored'), class: 'center', width: '20px'},
                    {data: 'monitoring.core__status.health', registry: true, render: $.nodewatcher.renderStatus(table, 'Health'), class: 'center', width: '20px'},
                    {data: 'monitoring.network__routing__topology[].', registry: true, render: renderRoutingTopology},
                    {data: 'config.core__project.project.name', registry: true},
                    {data: '@id', visible: false}
                ],
                // And make default sorting by type and name columns.
                order: [[0, 'asc'],[1, 'asc']],
                language: {
                    // TODO: Make strings translatable
                    zeroRecords: "No matching nodes found.",
                    emptyTable : "There are currently no nodes recorded/connected.",
                    info: "_START_ to _END_ of _TOTAL_ nodes shown",
                    infoEmpty: "0 nodes shown",
                    infoFiltered: "(from _MAX_ all nodes)",
                    infoPostFix: "",
                    search: "Filter:"
                }
            });
        });
    });
})(jQuery);
