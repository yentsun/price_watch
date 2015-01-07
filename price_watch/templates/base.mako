<!DOCTYPE html>
<html lang="${req.locale_name}">
<head>
    <meta charset="utf-8">
    <%def name="project_title()">food-price.net</%def>

    <title>${self.title()} - ${project_title()}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="Max Korinets">
    <link rel="shortcut icon" type="image/png"
          href="${request.static_url('price_watch:static/favicon.png')}"/>
    <!-- Le styles -->
    <link href="${request.static_url('price_watch:static/css/'
    'bootstrap.min.css')}"
          rel="stylesheet">
    <link href="${request.static_url('price_watch:static/css/'
    'bootstrap-responsive.min.css')}"
          rel="stylesheet">
    <link href="${request.static_url('price_watch:static/css/theme.css')}"
          rel="stylesheet">
    <!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="../assets/js/html5shiv.js"></script>
    <![endif]-->
</head>

<body>

<div class="container-narrow">

    <div class="masthead">

        <ul class="nav nav-pills pull-right">
            % for title, path, active in view.menu():
            % if active:
            <li class="active">
            % else:
            <li>
                % endif
                <a href="${path}">${title}</a>
            </li>

            % endfor
        </ul>
        % if req.context is not req.root:
            <a href="/" title="На главную">
        % endif
        <img src="${request.static_url('price_watch:static/img/logo.png')}"
             alt="Логотип" width="230"/>
        % if req.context is not req.root:
            </a>
        % endif
    </div>

    <hr>
    ${next.body()}
    <hr class="footer_separator clearfix">

    <div class="footer">
        <p class="pull-right">
            email: <a href="mailto:info@food-price.net">info@food-price.net</a>
        </p>
        <p>&copy; ${project_title()}
            <small>(${req.registry.settings['version']})</small>
        </p>
    </div>

</div> <!-- /container -->
    % if hasattr(self,'js'):
        ${self.js()}
    % endif
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-58171047-1', 'auto');
  ga('send', 'pageview');
</script>
<script type="text/javascript">
    var reformalOptions = {
        project_id: 829937,
        project_host: "food-price.reformal.ru",
        tab_orientation: "left",
        tab_indent: "50%",
        tab_bg_color: "#F05A00",
        tab_border_color: "#FFFFFF",
        tab_image_url: "http://tab.reformal.ru/T9GC0LfRi9Cy0Ysg0Lgg0L%252FRgNC10LTQu9C%252B0LbQtdC90LjRjw==/FFFFFF/2a94cfe6511106e7a48d0af3904e3090/left/1/tab.png",
        tab_border_width: 2
    };

    (function() {
        var script = document.createElement('script');
        script.type = 'text/javascript'; script.async = true;
        script.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'media.reformal.ru/widgets/v3/reformal.js';
        document.getElementsByTagName('head')[0].appendChild(script);
    })();
</script>
<noscript><a href="http://reformal.ru"><img src="http://media.reformal.ru/reformal.png" />
</a><a href="http://food-price.reformal.ru">Oтзывы и предложения для food-price.net</a>
</noscript>
</body>
</html>
