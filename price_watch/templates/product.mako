<%inherit file="base.mako"/>
<%def name="title()">Цена на ${req.context.title}</%def>
<%def name="description()">
    Текущая цена и история цен на ${req.context.title} за последний месяц
</%def>
<div itemscope itemtype="http://www.data-vocabulary.org/Product">
% if current_price:
<div class="pull-right well well-sm cat_price">
<%include file="partials/price.mako"
          args="price=current_price, delta=product_delta" /><br>
    <small class="package_title">за ${package_title}</small>
</div>
% endif
<a id="category" href="${req.resource_url(req.root)}#${category_title}"
   title="основная категория">
    ${category_title_ru}
</a> /
<a itemprop="category" id="product_category" href="${product_category_url}"
   title="категория">
    ${product_category_title}
</a>
    <style>
        .category_wrapper table>tbody>tr>td a{
            color: #${category_primary_color}
        }
        .category_wrapper{
            background: #${category_background_color}
        }
    </style>
<h1 itemprop="name" id="product_heading">
    ${req.context.title}
</h1>
<div class="row-fluid marketing" itemprop="offers">
    <div class="span12 category_wrapper">
        % if len(reports):
            <div id="chart_div" style="width: 650px; height: 300px;"></div>
            <table class="table">
                <thead>
                <tr>
                    <th>Дата и время отчета</th>
                    <th>Продавец</th>
                    <th>Цена / ${package_title}</th>
                    <th></th>
                </tr>
                </thead>
                <tbody>
                    % for url, date, merchant, location, price in reports:
                        <tr itemscope
                            itemtype="http://www.data-vocabulary.org/Offer">
                            <td>
                                <a itemprop="priceValidUntil"
                                   href="${url}">${date}</a>
                            </td>
                            <td itemprop="seller">${merchant} (${location})</td>
                            <td>
                                <%include file="partials/price.mako"
                                          args="price=price"/>
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        % else:
            <div class="alert alert-warning">
                По этому продукту отчеты не поступали длительное время.
                % if last_report_url:
                <a href="${last_report_url}">Последний отчет</a>
                % endif
            </div>
        % endif
    </div>
</div>
</div>
<%def name="js()">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
        google.load("visualization", "1", {packages:["corechart"]});
        google.setOnLoadCallback(drawChart);
        function drawChart() {
            var headers = [['Дата', 'Цена, руб.']];
            var data = google.visualization.arrayToDataTable(
                    headers.concat(${chart_data|n})
            );
            var options = {
                title: 'Динамика цены за месяц ',
                curveType: 'function',
                legend: {position: 'top'},
                hAxis: {showTextEvery: 4},
                chartArea:{left:50, top:50, width:'90%', height:'75%'},
                colors: ['#${category_primary_color}'],
                backgroundColor: {fill:'transparent'}
            };

            var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

            chart.draw(data, options);
        }
    </script>
</%def>