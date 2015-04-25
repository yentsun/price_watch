<%inherit file="base.mako"/>
<%def name="location_suffix()">${', '+current_location if current_location else ''}</%def>
<%def name="title()">
    Цены на ${cat_title} за ${package_title}${location_suffix()}
    </%def>
<%def name="description()">
Динамика цен на ${cat_title} за последний месяц
    % if current_location:
    ${current_location}
    % endif
</%def>
<%def name="location_menu()">
    <%include file="partials/location_menu.mako"
              args="current_location=current_location, locations=locations,
                    current_path=current_path" />
</%def>

% if median_price:
    <div class="pull-right well well-sm cat_price">
    <%include file="partials/price.mako"
          args="price=median_price, delta=category_delta" /><br>
        <small class="package_title">за ${package_title}</small>
    </div>
% endif
<a id="category" href="${req.resource_url(req.root)}#${category_title}"
   title="основная категория">
    ${category_title_ru}
</a>
<h1>
    Цены на ${cat_title}${location_suffix()}
</h1>

<div class="row-fluid marketing">
    <div class="span12">
        % if len(products):
        <div id="chart_div" style="width: 700px; height: 300px;"></div>
        <div>
            Ниже представлен список продуктов, из цен на которые складывается
            средняя цена.
        </div>
        <table id="product_list" class="table">
            <thead>
            <tr>
                <th>№</th>
                <th>Продукт</th>
                <th class="price">Цена за ${package_title}</th>
            </tr>
            </thead>
            <tbody>
                % for num, product, url, price, delta, median in products:
                    % if median:
                        <tr class="info" title="Этот товар имеет среднюю цену
                                                в категории">
                    % else:
                        <tr>
                    % endif
                        <td>${num}</td>
                        <td>
                            <a href="${url}">
                                ${product.title}
                            </a>
                        </td>
                        <td align="center">
                        <%include file="partials/price.mako"
                                  args="price=price, delta=delta" />
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
        % else:
        <div class="alert alert-info">Нет данных в этой категории :(</div>
        % endif
    </div>
</div>
<%def name="js()">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
        google.load("visualization", "1", {packages:["corechart"]});
        google.setOnLoadCallback(drawChart);
        function drawChart() {
            var headers = [['Дата', 'Средняя цена, руб.']];
            var data = google.visualization.arrayToDataTable(
                headers.concat(${price_data|n})
            );
            var options = {
                title: 'Динамика за месяц',
                curveType: 'function',
                legend: {position: 'top'},
                hAxis: {showTextEvery: 4},
                chartArea:{left:50, top:50, width:'90%', height:'75%'}
            };

            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

            chart.draw(data, options);
        }
    </script>
</%def>